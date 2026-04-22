#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""User-friendly CLI wrapper around the PaperBanana pipeline.

Compared to the raw `generate_from_json.py` shipped with the paperbanana
skill, this wrapper:

  * Accepts `--method-file` / `--caption` directly (no JSON file required).
  * Supports `--image-model` / `--fallback-image-model` / `--no-fallback`
    via env vars consumed by the multi-backend patch.
  * Supports `--text-model` / `--text-base-url` to drive Planner / Stylist /
    Critic with any OpenAI-compatible endpoint (e.g. local copilot-api on
    `:4141`), with a quick reachability probe + graceful fallback to the
    Google-AI-direct setup when the endpoint is down.
  * Auto-detects the PaperBanana checkout (`PAPERBANANA_ROOT` env var,
    `--paperbanana-root` flag, or default
    `~/.openclaw/workspace/projects/PaperBanana`).
  * Auto-applies the multi-backend patch if it has not been applied yet
    (idempotent; skip with `--no-auto-patch`).

Run via PaperBanana's venv python OR via `uv run` from the skill directory:

    /path/to/PaperBanana/.venv/bin/python scripts/generate.py \
        --method-file ./method.md \
        --caption "Figure 1: Overview of our framework" \
        --out-dir ./figures/v1 \
        --candidates 3 \
        --aspect-ratio 16:9
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import socket
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Optional
from urllib.parse import urlparse

DEFAULT_PAPERBANANA_ROOT = Path(
    os.environ.get(
        "PAPERBANANA_ROOT",
        str(Path.home() / "PaperBanana"),
    )
).expanduser()

DEFAULT_IMAGE_MODEL = "gemini-3-pro-image-preview"
DEFAULT_FALLBACK_IMAGE_MODEL = "openai/gpt-5.4-image-2"
DEFAULT_TEXT_MODEL = "gemini-3.1-pro-preview"


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _endpoint_reachable(url: str, timeout: float = 0.6) -> bool:
    """Quick TCP probe (no HTTP round-trip) to check a base_url is up."""
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _ensure_patched(paperbanana_root: Path, auto_patch: bool) -> None:
    """Idempotently apply the multi-backend patch if missing.

    Detects three states for `utils/generation_utils.py`:
      * our marker present → nothing to do
      * upstream-already-patched (has both openrouter_client init AND the
        image-chat helper) → nothing to do
      * neither → try to apply our patch, but treat failures as warnings
        rather than fatal errors (upstream layout drifts).
    """
    patch_script = Path(__file__).resolve().parent / "patch_multibackend.py"
    if not patch_script.exists():
        return  # nothing to do

    target = paperbanana_root / "utils" / "generation_utils.py"
    if target.exists():
        try:
            txt = target.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            txt = ""
        if "paperbanana-multibackend-patch" in txt:
            return  # already stamped by us
        if (
            "openrouter_client = AsyncOpenAI" in txt
            and "call_openrouter_image_chat_with_retry_async" in txt
        ):
            return  # upstream already shipped multi-backend dispatch

    if not auto_patch:
        print(
            "note: multi-backend patch not applied; pass --auto-patch or run "
            "scripts/patch_multibackend.py manually if you need it.",
            file=sys.stderr,
        )
        return

    print(f"info: applying multi-backend patch to {paperbanana_root}")
    rc = subprocess.call(
        [
            sys.executable,
            str(patch_script),
            "--paperbanana-root",
            str(paperbanana_root),
        ]
    )
    if rc != 0:
        print(
            f"warn: patch_multibackend.py exited with rc={rc}; the underlying\n"
            f"      PaperBanana checkout may already supply equivalent\n"
            f"      functionality, or its layout may have drifted from what\n"
            f"      the patch expects. Continuing — image generation will\n"
            f"      either Just Work or fail with a clearer error below.",
            file=sys.stderr,
        )


def _resolve_text_endpoint(
    text_model: str,
    text_base_url: Optional[str],
) -> tuple[str, Optional[str]]:
    """Decide which text endpoint to actually use.

    Returns (final_model, final_base_url_or_None). If `final_base_url` is
    None, the underlying agents fall back to their built-in Google AI
    direct path — which is the right default for almost everyone.

    The `--text-base-url` flag is only meant for advanced users who run a
    local OpenAI-compatible proxy (e.g. copilot-api, vLLM, ollama). We do
    NOT auto-probe well-known ports, because surprise-routing through a
    random local server is exactly the kind of behaviour that breaks
    reproducibility.
    """
    if text_base_url:
        if _endpoint_reachable(text_base_url):
            return text_model, text_base_url
        print(
            f"warn: text endpoint {text_base_url} unreachable; falling back "
            f"to Google AI direct for {text_model}.",
            file=sys.stderr,
        )
    return text_model, None


@contextmanager
def _temp_override_yaml(
    yaml_path: Path,
    image_model: Optional[str],
    text_model: Optional[str],
) -> Iterator[None]:
    """Temporarily rewrite `defaults.image_model_name` / `defaults.model_name`
    in the PaperBanana model_config.yaml, restoring the original on exit.

    Only fields we actually need to change are touched; everything else is
    left byte-identical. Backup is written next to the original as a safety
    net in case the process is killed mid-run.
    """
    if not yaml_path.is_file() or (image_model is None and text_model is None):
        yield
        return

    original = yaml_path.read_text(encoding="utf-8")
    backup = yaml_path.with_suffix(yaml_path.suffix + ".bak.generate-py")
    backup.write_text(original, encoding="utf-8")

    new_text = original
    if image_model is not None:
        new_text = re.sub(
            r'^(\s*image_model_name:\s*)"[^"]*"',
            lambda m: f'{m.group(1)}"{image_model}"',
            new_text,
            count=1,
            flags=re.MULTILINE,
        )
    if text_model is not None:
        new_text = re.sub(
            r'^(\s*model_name:\s*)"[^"]*"',
            lambda m: f'{m.group(1)}"{text_model}"',
            new_text,
            count=1,
            flags=re.MULTILINE,
        )

    yaml_path.write_text(new_text, encoding="utf-8")
    try:
        yield
    finally:
        yaml_path.write_text(original, encoding="utf-8")
        try:
            backup.unlink()
        except OSError:
            pass


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate academic figures via PaperBanana (multi-backend).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # I/O
    ap.add_argument("--method-file", type=Path, help="Path to a Markdown/text file containing the Method section.")
    ap.add_argument("--method", type=str, help="Inline method text (overrides --method-file).")
    ap.add_argument("--caption", type=str, required=True, help="Target figure caption.")
    ap.add_argument("--out-dir", type=Path, required=True, help="Output directory for PNG candidates.")

    # Pipeline knobs
    ap.add_argument("--candidates", type=int, default=3, help="Number of independent diagram candidates.")
    ap.add_argument("--max-concurrent", type=int, default=2, help="Max concurrent candidates (be gentle on quota).")
    ap.add_argument(
        "--exp-mode",
        default="demo_planner_critic",
        choices=["demo_planner_critic", "demo_full", "dev_planner", "dev_full", "vanilla"],
    )
    ap.add_argument("--retrieval", default="none", choices=["auto", "manual", "random", "none"])
    ap.add_argument("--aspect-ratio", default="16:9", choices=["21:9", "16:9", "3:2", "1:1"])
    ap.add_argument("--max-critic-rounds", type=int, default=1)

    # Backend selection
    ap.add_argument(
        "--image-model",
        default=os.environ.get("PAPERBANANA_IMAGE_MODEL", DEFAULT_IMAGE_MODEL),
        help="Primary image backend id.",
    )
    ap.add_argument(
        "--fallback-image-model",
        default=os.environ.get("PAPERBANANA_FALLBACK_IMAGE_MODEL", DEFAULT_FALLBACK_IMAGE_MODEL),
        help="Fallback image backend id when primary fails on quota/billing/rate-limit.",
    )
    fallback_group = ap.add_mutually_exclusive_group()
    fallback_group.add_argument(
        "--auto-fallback", dest="auto_fallback", action="store_true", default=True,
        help="Automatically retry with --fallback-image-model on quota errors (default).",
    )
    fallback_group.add_argument(
        "--no-fallback", dest="auto_fallback", action="store_false",
        help="Disable automatic image-backend fallback (useful while debugging).",
    )

    ap.add_argument(
        "--text-model",
        default=os.environ.get("PAPERBANANA_TEXT_MODEL", DEFAULT_TEXT_MODEL),
        help="Text model used for Planner / Stylist / Critic.",
    )
    ap.add_argument(
        "--text-base-url",
        default=os.environ.get("PAPERBANANA_TEXT_BASE_URL"),
        help=(
            "Optional OpenAI-compatible base URL for the text model. Only "
            "set this if you run a local proxy (copilot-api, vLLM, ollama, "
            "etc.); otherwise text agents call Google AI directly."
        ),
    )

    # Plumbing
    ap.add_argument(
        "--paperbanana-root",
        type=Path,
        default=DEFAULT_PAPERBANANA_ROOT,
        help="Path to the PaperBanana checkout.",
    )
    ap.add_argument("--no-auto-patch", dest="auto_patch", action="store_false", default=True,
                    help="Skip idempotent multi-backend patch application.")
    ap.add_argument("--keep-input-json", action="store_true",
                    help="Keep the temporary input JSON in --out-dir for debugging.")

    args = ap.parse_args()

    # Detect which flags the user actually typed (vs. parser defaults), so we
    # only patch model_config.yaml when overriding intentionally.
    user_supplied = {
        a.lstrip("-").split("=", 1)[0].replace("-", "_")
        for a in sys.argv[1:]
        if a.startswith("--")
    }
    explicit_image_model = (
        args.image_model
        if (
            "image_model" in user_supplied
            or os.environ.get("PAPERBANANA_IMAGE_MODEL")
        )
        else None
    )
    explicit_text_model = (
        args.text_model
        if (
            "text_model" in user_supplied
            or os.environ.get("PAPERBANANA_TEXT_MODEL")
        )
        else None
    )

    # ---- validate inputs ---------------------------------------------------
    project_root = args.paperbanana_root.expanduser().resolve()
    if not project_root.is_dir():
        print(
            f"error: PaperBanana checkout not found at {project_root}.\n"
            "Set --paperbanana-root or PAPERBANANA_ROOT, or clone it first:\n"
            "  git clone https://github.com/google-research/PaperBanana.git",
            file=sys.stderr,
        )
        return 2

    method_text = args.method
    if not method_text:
        if not args.method_file:
            print("error: provide --method or --method-file", file=sys.stderr)
            return 2
        if not args.method_file.is_file():
            print(f"error: --method-file {args.method_file} does not exist", file=sys.stderr)
            return 2
        method_text = args.method_file.read_text(encoding="utf-8")

    if not method_text.strip():
        print("error: method text is empty", file=sys.stderr)
        return 2

    out_dir: Path = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---- ensure patch ------------------------------------------------------
    # NOTE: most modern PaperBanana / PaperVizAgent checkouts already ship
    # the multi-backend dispatch upstream. We try to detect that and skip
    # patching automatically. The patch script itself is best-effort against
    # one specific intermediate upstream layout; if your checkout differs,
    # it will warn and continue rather than abort.
    _ensure_patched(project_root, auto_patch=args.auto_patch)

    # ---- resolve text endpoint --------------------------------------------
    text_model, text_base_url = _resolve_text_endpoint(args.text_model, args.text_base_url)

    # ---- export env for the underlying agents -----------------------------
    env = os.environ.copy()
    env["PAPERBANANA_IMAGE_MODEL"] = args.image_model
    env["PAPERBANANA_FALLBACK_IMAGE_MODEL"] = args.fallback_image_model
    env["PAPERBANANA_AUTO_FALLBACK"] = "1" if args.auto_fallback else "0"
    env["PAPERBANANA_TEXT_MODEL"] = text_model
    if text_base_url:
        env["COPILOT_BASE_URL"] = text_base_url
        env.setdefault("COPILOT_API_KEY", "copilot")

    # Sanity-warn missing keys but don't hard-fail (the user might be on a
    # patched yaml that supplies them).
    if "openrouter" in args.image_model.lower() or args.image_model.startswith("openai/") \
            or args.fallback_image_model.startswith("openai/"):
        if not env.get("OPENROUTER_API_KEY"):
            print(
                "warn: OPENROUTER_API_KEY not set; GPT-Image-2 calls will fail.",
                file=sys.stderr,
            )
    if args.image_model.startswith("gemini-") or args.fallback_image_model.startswith("gemini-"):
        if not env.get("GOOGLE_API_KEY") and not env.get("GEMINI_API_KEY"):
            print(
                "warn: GOOGLE_API_KEY / GEMINI_API_KEY not set; Gemini calls will fail.",
                file=sys.stderr,
            )

    # ---- write input JSON & delegate to generate_from_json.py -------------
    input_json = out_dir / "_input.json"
    input_json.write_text(
        json.dumps({"method": method_text, "caption": args.caption}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Locate generate_from_json.py: prefer the sibling skill if installed,
    # otherwise our own scripts/ dir.
    candidates = [
        Path.home() / ".openclaw/skills/paperbanana/scripts/generate_from_json.py",
        Path(__file__).resolve().parent / "generate_from_json.py",
    ]
    runner: Optional[Path] = next((p for p in candidates if p.exists()), None)
    if runner is None:
        print(
            "error: could not find generate_from_json.py; ensure the paperbanana "
            "skill is installed at ~/.openclaw/skills/paperbanana/.",
            file=sys.stderr,
        )
        return 3

    # Use the PaperBanana venv if available; otherwise the current interpreter
    # (the user invoked us with the right one).
    venv_python = project_root / ".venv" / "bin" / "python"
    interpreter = str(venv_python) if venv_python.exists() else sys.executable

    cmd = [
        interpreter,
        str(runner),
        "--project-root", str(project_root),
        "--input-json", str(input_json),
        "--out-dir", str(out_dir),
        "--candidates", str(args.candidates),
        "--max-concurrent", str(args.max_concurrent),
        "--exp-mode", args.exp_mode,
        "--retrieval", args.retrieval,
        "--aspect-ratio", args.aspect_ratio,
        "--max-critic-rounds", str(args.max_critic_rounds),
    ]
    print(f"info: running {' '.join(cmd)}")
    yaml_path = project_root / "configs" / "model_config.yaml"
    with _temp_override_yaml(yaml_path, explicit_image_model, explicit_text_model):
        rc = subprocess.call(cmd, env=env)

    if not args.keep_input_json:
        try:
            input_json.unlink()
        except OSError:
            pass

    if rc != 0:
        print(f"error: generate_from_json.py exited with rc={rc}", file=sys.stderr)
        return rc

    # Friendly summary
    pngs = sorted(out_dir.glob("candidate_*.png"))
    if pngs:
        print(f"\n✓ generated {len(pngs)} candidate(s):")
        for p in pngs:
            print(f"  - {p}")
    else:
        print(
            "\nwarn: no candidate PNGs landed in the output dir. Check "
            f"{out_dir / 'results.json'} for raw responses.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
