#!/usr/bin/env python3
"""Patch a PaperBanana checkout to support multiple image / text backends.

Adds:
- OpenRouter chat-completions image client (for `openai/gpt-5.4-image-2`).
- Local copilot-api / OpenAI-compatible text client (lets non-Gemini text
  models drive Planner / Stylist / Critic without rewriting the agents).
- Quota-aware automatic fallback for the image backend.

The patch is **idempotent**: running it twice on the same checkout is a no-op.
Backups are written next to each mutated file as `<file>.bak.before-multibackend`.

Usage:

    python patch_multibackend.py --paperbanana-root /path/to/PaperBanana
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from textwrap import dedent

PATCH_MARKER = "# === paperbanana-multibackend-patch"  # prefix; covers all stamp variants
PATCH_MARKER_FULL = "# === paperbanana-multibackend-patch ==="


def _backup_once(path: Path) -> None:
    backup = path.with_suffix(path.suffix + ".bak.before-multibackend")
    if not backup.exists():
        shutil.copy2(path, backup)


def patch_generation_utils(util_path: Path) -> bool:
    """Add OpenRouter + copilot clients, image-chat helper, and routing layer."""
    src = util_path.read_text()
    if PATCH_MARKER in src:
        return False  # already patched (our own marker)

    # Upstream-already-patched detection: newer PaperBanana releases ship
    # the OpenRouter client + image-chat helper out of the box. If both are
    # present, stamp a marker and bail — nothing for us to do.
    if (
        "openrouter_client = AsyncOpenAI" in src
        and "call_openrouter_image_chat_with_retry_async" in src
    ):
        _backup_once(util_path)
        util_path.write_text(
            "# === paperbanana-multibackend-patch: upstream already patched ===\n"
            + src
        )
        return True

    _backup_once(util_path)

    # 1) Insert OpenRouter + copilot client init after the existing OpenAI client init.
    # Try multiple known anchor variants since upstream wording varies.
    openai_client_anchor = None
    for candidate in (
        "openai_client = AsyncOpenAI(api_key=openai_api_key)",
        "openai_client = AsyncOpenAI(api_key=key)",
    ):
        if candidate in src:
            openai_client_anchor = candidate
            break
    if openai_client_anchor is None:
        print(
            f"warn: no recognised OpenAI client init in {util_path.name}; skipping "
            "client-block insertion. Most upstream forks already initialise OpenRouter "
            "on their own — if that's the case, this skip is harmless.",
            file=sys.stderr,
        )
        return False

    client_block = dedent(f"""\

        {PATCH_MARKER_FULL}
        # OpenRouter chat-completions client (used for image-output models such as
        # openai/gpt-5.4-image-2).
        openrouter_api_key = get_config_val(
            "api_keys", "openrouter_api_key", "OPENROUTER_API_KEY", ""
        )
        if openrouter_api_key:
            openrouter_client = AsyncOpenAI(
                api_key=openrouter_api_key,
                base_url="https://openrouter.ai/api/v1",
                default_headers={{
                    "HTTP-Referer": "https://github.com/jxtse/scientific-research-skills",
                    "X-Title": "PaperBanana",
                }},
            )
            print("Initialized OpenRouter Client with API Key")
        else:
            print("Warning: OpenRouter Client not initialized (set OPENROUTER_API_KEY).")
            openrouter_client = None

        # Optional OpenAI-compatible proxy for routing non-Gemini text models
        # (e.g. anthropic/claude-opus-4.7 via copilot-api, vLLM, ollama, etc.).
        # OFF BY DEFAULT — only initialised if the user explicitly sets a
        # base URL. Without it, non-Gemini text model ids will fall through
        # to whatever upstream PaperBanana does with them.
        copilot_base_url = get_config_val(
            "api_keys", "copilot_base_url", "COPILOT_BASE_URL", ""
        )
        copilot_api_key = get_config_val(
            "api_keys", "copilot_api_key", "COPILOT_API_KEY", ""
        )
        if copilot_base_url:
            copilot_client = AsyncOpenAI(
                api_key=copilot_api_key or "sk-no-key-required",
                base_url=copilot_base_url,
            )
            print(f"Initialized OpenAI-compatible proxy client at {{copilot_base_url}}")
        else:
            copilot_client = None
        # === end paperbanana-multibackend-patch ===
        """)

    # Insert the block right after the existing OpenAI client init block.
    insertion_point = src.index(openai_client_anchor)
    next_blank = src.index("\n\n", insertion_point)
    src = src[:next_blank] + client_block + src[next_blank:]

    # 2) Wrap call_gemini_with_retry_async with a routing front door.
    gemini_anchor = (
        'async def call_gemini_with_retry_async(\n'
        '    model_name, contents, config, max_attempts=5, retry_delay=5, error_context=""\n'
        '):'
    )
    if gemini_anchor not in src:
        raise RuntimeError(
            "Could not find call_gemini_with_retry_async signature anchor — "
            "upstream layout may have changed."
        )

    routing_insert = dedent('''\
        async def call_gemini_with_retry_async(
            model_name, contents, config, max_attempts=5, retry_delay=5, error_context=""
        ):
            # === paperbanana-multibackend-patch: front-door routing ===
            # If the requested text model isn't a Gemini id, transparently route
            # the call through the local copilot/OpenAI-compatible proxy so that
            # claude-*, gpt-*, etc. can drive the Planner/Stylist/Critic agents
            # without per-agent code changes.
            if not ("gemini" in model_name and "/" not in model_name):
                return await _call_copilot_chat_async(
                    model_name=model_name,
                    contents=contents,
                    config=config,
                    max_attempts=max_attempts,
                    retry_delay=retry_delay,
                    error_context=error_context,
                )
            # === end paperbanana-multibackend-patch ===
        ''')

    src = src.replace(
        gemini_anchor,
        routing_insert.rstrip("\n") + "\n",
        1,
    )

    # 3) Append helper functions at end of file.
    src += "\n\n" + PATCH_MARKER_FULL + "\n" + _IMAGE_CHAT_HELPER + "\n\n" + _COPILOT_CHAT_HELPER + "\n# === end paperbanana-multibackend-patch ===\n"

    util_path.write_text(src)
    return True


_IMAGE_CHAT_HELPER = '''\
async def call_openrouter_image_chat_with_retry_async(
    model_name,
    prompt,
    config,
    max_attempts=5,
    retry_delay=30,
    error_context="",
):
    """Generate an image via an OpenRouter chat-completions image model.

    Returns a list with one base64-encoded PNG (no data URL prefix), to mirror
    the return shape of `call_openai_image_generation_with_retry_async`.
    """
    if openrouter_client is None:
        print("[Error] OpenRouter client is not initialized.")
        return ["Error"]

    aspect_ratio = config.get("aspect_ratio") or config.get("size")
    quality = config.get("quality")

    hints = []
    if aspect_ratio:
        hints.append(f"Aspect ratio: {aspect_ratio}.")
    if quality:
        hints.append(f"Quality: {quality}.")
    full_prompt = prompt + ("\\n\\n" + " ".join(hints) if hints else "")

    for attempt in range(max_attempts):
        try:
            response = await openrouter_client.chat.completions.create(
                model=model_name,
                modalities=["image", "text"],
                messages=[{"role": "user", "content": full_prompt}],
            )
            msg = response.choices[0].message
            images = getattr(msg, "images", None) or []
            for img in images:
                if isinstance(img, dict):
                    image_url = img.get("image_url", {})
                else:
                    image_url = getattr(img, "image_url", None)
                    if image_url is not None and not isinstance(image_url, dict):
                        image_url = {"url": getattr(image_url, "url", "")}
                    image_url = image_url or {}
                url = image_url.get("url", "")
                if isinstance(url, str) and url.startswith("data:image"):
                    return [url.split(",", 1)[1]]

            print(
                f"[Warning] OpenRouter image response had no image payload "
                f"(model={model_name}, attempt={attempt + 1})."
            )
            if attempt < max_attempts - 1:
                await asyncio.sleep(retry_delay)
            continue

        except Exception as e:
            context_msg = f" for {error_context}" if error_context else ""
            print(
                f"Attempt {attempt + 1} for OpenRouter image chat model "
                f"{model_name} failed{context_msg}: {e}. Retrying in {retry_delay} seconds..."
            )
            if attempt < max_attempts - 1:
                await asyncio.sleep(retry_delay)
            else:
                print(f"Error: All {max_attempts} attempts failed{context_msg}")
                return ["Error"]

    return ["Error"]
'''


_COPILOT_CHAT_HELPER = '''\
async def _call_copilot_chat_async(
    model_name, contents, config, max_attempts=5, retry_delay=5, error_context=""
):
    """Run a text-generation request against a local OpenAI-compatible proxy.

    Maps a Gemini-style call onto an OpenAI ChatCompletion. Returns a list of
    `candidate_count` strings padded with "Error" on failure to mirror
    `call_gemini_with_retry_async`'s contract.
    """
    if copilot_client is None:
        raise RuntimeError(
            "Copilot client is not initialized. Set COPILOT_BASE_URL or "
            "configure api_keys.copilot_base_url in configs/model_config.yaml."
        )

    user_text_parts = []
    for item in contents:
        if isinstance(item, dict) and item.get("type") == "text":
            user_text_parts.append(item.get("text", ""))
    user_message = "\\n\\n".join(p for p in user_text_parts if p)

    messages = []
    system_instruction = getattr(config, "system_instruction", None)
    if system_instruction:
        messages.append({"role": "system", "content": str(system_instruction)})
    messages.append({"role": "user", "content": user_message})

    target_candidate_count = getattr(config, "candidate_count", 1) or 1
    temperature = getattr(config, "temperature", None)
    max_output_tokens = getattr(config, "max_output_tokens", None)

    request_kwargs = {"model": model_name, "messages": messages}
    if temperature is not None:
        request_kwargs["temperature"] = temperature
    if max_output_tokens:
        request_kwargs["max_tokens"] = int(max_output_tokens)

    result_list = []
    for attempt in range(max_attempts):
        try:
            tasks = [
                copilot_client.chat.completions.create(**request_kwargs)
                for _ in range(target_candidate_count - len(result_list))
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            for r in responses:
                if isinstance(r, Exception):
                    raise r
                content = r.choices[0].message.content or ""
                if content.strip():
                    result_list.append(content)
            if len(result_list) >= target_candidate_count:
                result_list = result_list[:target_candidate_count]
                break
        except Exception as e:
            context_msg = f" for {error_context}" if error_context else ""
            current_delay = min(retry_delay * (2 ** attempt), 30)
            print(
                f"Attempt {attempt + 1} for copilot model {model_name} "
                f"failed{context_msg}: {e}. Retrying in {current_delay} seconds..."
            )
            if attempt < max_attempts - 1:
                await asyncio.sleep(current_delay)
            else:
                print(f"Error: All {max_attempts} attempts failed{context_msg}")

    if len(result_list) < target_candidate_count:
        result_list.extend(["Error"] * (target_candidate_count - len(result_list)))
    return result_list
'''


def patch_visualizer_or_vanilla(agent_path: Path) -> bool:
    """Add OpenRouter image-chat branch and tighten Gemini branch.

    Idempotent: skips files that already have:
      * the patch marker (re-run on our own output), OR
      * an upstream OpenRouter dispatch branch (newer PaperBanana releases
        ship vanilla_agent.py with the OpenRouter branch + guarded gemini
        condition built in — nothing to do).
    Also avoids double-appending the `and "/" not in self.model_name` guard
    by skipping lines that already contain it.
    """
    src = agent_path.read_text()
    if PATCH_MARKER in src:
        return False
    # Upstream-already-patched detection: file already has both the guarded
    # gemini branch AND an OpenRouter image dispatch.
    has_guarded_gemini = '"gemini" in self.model_name and "/" not in self.model_name' in src
    has_openrouter = (
        'self.model_name.startswith("openai/")' in src
        and 'and "image" in self.model_name' in src
    )
    if has_guarded_gemini and has_openrouter:
        # Stamp marker on top so re-runs report "already patched".
        _backup_once(agent_path)
        agent_path.write_text(
            "# === paperbanana-multibackend-patch: upstream already patched ===\n"
            + src
        )
        return True

    _backup_once(agent_path)

    # Tighten Gemini branch: require "/" not in model_name. Skip lines that
    # already contain the guard.
    new_lines = []
    for line in src.splitlines(keepends=True):
        if (
            '"gemini" in self.model_name' in line
            and '"/" not in self.model_name' not in line
        ):
            line = line.replace(
                '"gemini" in self.model_name',
                '"gemini" in self.model_name and "/" not in self.model_name',
            )
        new_lines.append(line)
    src = "".join(new_lines)

    # Insert OpenRouter elif immediately before the final `else:` of the
    # model dispatch chain. We anchor on the unsupported-model raise.
    raise_line = 'raise ValueError(f"Unsupported model: {self.model_name}")'
    if raise_line in src:
        elif_block = dedent('''\
                elif (
                    self.model_name.startswith("openai/")
                    and "image" in self.model_name
                ) or (
                    "/" in self.model_name and "image" in self.model_name
                ):
                    # === paperbanana-multibackend-patch ===
                    # OpenRouter chat-completions image models
                    # (e.g. openai/gpt-5.4-image-2,
                    #       google/gemini-3.1-flash-image-preview)
                    aspect_ratio = "1:1"
                    if "additional_info" in data and "rounded_ratio" in data["additional_info"]:
                        aspect_ratio = data["additional_info"]["rounded_ratio"]
                    image_config = {
                        "aspect_ratio": aspect_ratio,
                        "quality": "high",
                    }
                    response_list = await generation_utils.call_openrouter_image_chat_with_retry_async(
                        model_name=self.model_name,
                        prompt=prompt_text,
                        config=image_config,
                        max_attempts=5,
                        retry_delay=30,
                    )
                    # === end paperbanana-multibackend-patch ===
                else:
                    ''')
        for indent in ("            ", "                "):
            anchor = f"{indent}else:\n{indent}    {raise_line}"
            replacement = elif_block.replace("                ", indent, 1) + raise_line
            if anchor in src:
                src = src.replace(anchor, replacement, 1)
                break
    else:
        src = (
            "# === paperbanana-multibackend-patch: gemini branch tightened ===\n"
            + src
        )

    agent_path.write_text(src)
    return True


def patch_yaml(yaml_path: Path) -> bool:
    """Add commented placeholder keys for the new providers (idempotent)."""
    src = yaml_path.read_text()
    if "openrouter_api_key" in src:
        return False
    _backup_once(yaml_path)
    addition = dedent('''\

        # === paperbanana-multibackend-patch: extra providers ===
        # Set these via env vars (preferred) or fill in below.
        #   openrouter_api_key: ""            # or env: OPENROUTER_API_KEY
        #
        # OPTIONAL local OpenAI-compatible proxy (vLLM / ollama / copilot-api etc.)
        # Off by default; only enabled when copilot_base_url is set.
        #   copilot_base_url: ""               # or env: COPILOT_BASE_URL
        #   copilot_api_key:  ""               # or env: COPILOT_API_KEY
        # === end paperbanana-multibackend-patch ===
    ''')
    yaml_path.write_text(src.rstrip() + "\n" + addition)
    return True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--paperbanana-root",
        required=True,
        type=Path,
        help="Path to the PaperBanana checkout to patch.",
    )
    ap.add_argument(
        "--check",
        action="store_true",
        help="Only report what would change; don't write.",
    )
    args = ap.parse_args()

    root = args.paperbanana_root.expanduser().resolve()
    if not root.is_dir():
        print(f"error: {root} is not a directory", file=sys.stderr)
        return 1

    targets = {
        "utils/generation_utils.py": patch_generation_utils,
        "agents/visualizer_agent.py": patch_visualizer_or_vanilla,
        "agents/vanilla_agent.py": patch_visualizer_or_vanilla,
        "configs/model_config.yaml": patch_yaml,
    }

    if args.check:
        for rel in targets:
            f = root / rel
            if not f.exists():
                print(f"  MISSING  {rel}")
                continue
            txt = f.read_text()
            # Our marker present → patched.
            ours = PATCH_MARKER in txt
            yaml_ok = rel.endswith(".yaml") and "openrouter_api_key" in txt
            # Upstream-already-patched detection (matches the same heuristics
            # used by the patch functions themselves).
            upstream_utils = (
                rel == "utils/generation_utils.py"
                and "openrouter_client = AsyncOpenAI" in txt
                and "call_openrouter_image_chat_with_retry_async" in txt
            )
            upstream_agent = (
                rel.startswith("agents/")
                and '"gemini" in self.model_name and "/" not in self.model_name' in txt
                and 'self.model_name.startswith("openai/")' in txt
                and 'and "image" in self.model_name' in txt
            )
            if ours or yaml_ok or upstream_utils or upstream_agent:
                tag = "upstream" if (upstream_utils or upstream_agent) and not ours else "patched "
                print(f"  {tag}  {rel}")
            else:
                print(f"   needs patch  {rel}")
        return 0

    changed = 0
    for rel, fn in targets.items():
        f = root / rel
        if not f.exists():
            print(f"skip: {rel} not found in {root}")
            continue
        try:
            if fn(f):
                print(f"patched: {rel}")
                changed += 1
            else:
                print(f"already patched: {rel}")
        except RuntimeError as e:
            print(f"error patching {rel}: {e}", file=sys.stderr)
            return 2

    print(f"\nDone. {changed} file(s) modified.")
    if changed:
        print(
            "Backups written as <file>.bak.before-multibackend; remove or "
            "restore as needed."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
