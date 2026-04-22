#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Minimal CLI wrapper around the PaperBanana / PaperVizAgent pipeline.

Reads a method text file + a figure caption, hands them to a local
PaperBanana checkout, and writes N candidate PNGs to an output dir.

This wrapper does NOT touch model selection, API keys, or routing — that
all comes from PaperBanana's own configs/model_config.yaml. Set up the
yaml once (image_model_name, model_name, api keys) and this script just
feeds inputs in and pulls images out.

Usage:

    /path/to/PaperBanana/.venv/bin/python scripts/generate.py \\
        --method-file ./method.md \\
        --caption "Figure 1: Overview of our framework" \\
        --out-dir ./figures/v1 \\
        --candidates 3
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
import sys
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List


def _b64_to_png_bytes(b64_jpg: str) -> bytes:
    from PIL import Image  # local import: PIL ships with PaperBanana's venv
    raw = base64.b64decode(b64_jpg)
    img = Image.open(BytesIO(raw))
    out = BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


async def _run(
    project_root: Path,
    method: str,
    caption: str,
    candidates: int,
    max_concurrent: int,
    exp_mode: str,
    aspect_ratio: str,
    max_critic_rounds: int,
) -> List[Dict[str, Any]]:
    sys.path.insert(0, str(project_root))

    from utils import config  # type: ignore
    from utils.paperviz_processor import PaperVizProcessor  # type: ignore
    from agents.vanilla_agent import VanillaAgent  # type: ignore
    from agents.planner_agent import PlannerAgent  # type: ignore
    from agents.visualizer_agent import VisualizerAgent  # type: ignore
    from agents.stylist_agent import StylistAgent  # type: ignore
    from agents.critic_agent import CriticAgent  # type: ignore
    from agents.retriever_agent import RetrieverAgent  # type: ignore
    from agents.polish_agent import PolishAgent  # type: ignore

    exp = config.ExpConfig(
        dataset_name="PaperBananaBench",
        task_name="diagram",
        split_name="demo",
        exp_mode=exp_mode,
        retrieval_setting="none",
        max_critic_rounds=max_critic_rounds,
        main_model_name="",       # use yaml defaults
        image_gen_model_name="",   # use yaml defaults
        work_dir=project_root,
    )

    processor = PaperVizProcessor(
        exp_config=exp,
        vanilla_agent=VanillaAgent(exp_config=exp),
        planner_agent=PlannerAgent(exp_config=exp),
        visualizer_agent=VisualizerAgent(exp_config=exp),
        stylist_agent=StylistAgent(exp_config=exp),
        critic_agent=CriticAgent(exp_config=exp),
        retriever_agent=RetrieverAgent(exp_config=exp),
        polish_agent=PolishAgent(exp_config=exp),
    )

    data_list = [
        {
            "filename": f"candidate_{i}",
            "candidate_id": i,
            "caption": caption,
            "content": method,
            "visual_intent": caption,
            "additional_info": {"rounded_ratio": aspect_ratio},
            "max_critic_rounds": max_critic_rounds,
        }
        for i in range(candidates)
    ]

    results: List[Dict[str, Any]] = []
    async for item in processor.process_queries_batch(
        data_list,
        max_concurrent=max(1, min(max_concurrent, candidates)),
        do_eval=False,
    ):
        results.append(item)
    results.sort(key=lambda x: int(x.get("candidate_id", 0)))
    return results


def _save_pngs(results: List[Dict[str, Any]], out_dir: Path) -> List[Path]:
    saved: List[Path] = []
    for r in results:
        cid = int(r.get("candidate_id", 0))
        key = r.get("eval_image_field")
        if not key:
            for k in (
                "target_diagram_critic_desc2_base64_jpg",
                "target_diagram_critic_desc1_base64_jpg",
                "target_diagram_critic_desc0_base64_jpg",
                "target_diagram_stylist_desc0_base64_jpg",
                "target_diagram_desc0_base64_jpg",
                "vanilla_diagram_base64_jpg",
            ):
                if r.get(k):
                    key = k
                    break
        b64 = r.get(key, "") if key else ""
        if not isinstance(b64, str) or len(b64) < 200:
            continue
        path = out_dir / f"candidate_{cid}.png"
        path.write_bytes(_b64_to_png_bytes(b64))
        saved.append(path)
    return saved


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Generate academic figures via a local PaperBanana checkout.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    ap.add_argument("--paperbanana-root", type=Path, required=True,
                    help="Path to your PaperBanana checkout (the dir containing agents/, utils/, configs/).")
    ap.add_argument("--method-file", type=Path, required=True,
                    help="Markdown/text file with the paper's Method section.")
    ap.add_argument("--caption", required=True, help="Target figure caption.")
    ap.add_argument("--out-dir", type=Path, required=True, help="Where to write candidate PNGs.")
    ap.add_argument("--candidates", type=int, default=3)
    ap.add_argument("--max-concurrent", type=int, default=2)
    ap.add_argument("--exp-mode", default="demo_full",
                    choices=["demo_planner_critic", "demo_full", "dev_planner", "dev_full", "vanilla"],
                    help="demo_full = Planner+Stylist+Visualizer+Critic (recommended); "
                         "demo_planner_critic = skip Stylist (faster); "
                         "vanilla = single-shot (fastest, lowest quality).")
    ap.add_argument("--aspect-ratio", default="16:9", choices=["21:9", "16:9", "3:2", "1:1"])
    ap.add_argument("--max-critic-rounds", type=int, default=2)
    args = ap.parse_args()

    project_root = args.paperbanana_root.expanduser().resolve()
    if not project_root.is_dir():
        print(f"error: {project_root} is not a directory", file=sys.stderr)
        return 2
    if not args.method_file.is_file():
        print(f"error: --method-file {args.method_file} does not exist", file=sys.stderr)
        return 2

    method = args.method_file.read_text(encoding="utf-8").strip()
    if not method:
        print("error: method file is empty", file=sys.stderr)
        return 2

    out_dir = args.out_dir.expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    results = asyncio.run(_run(
        project_root=project_root,
        method=method,
        caption=args.caption,
        candidates=args.candidates,
        max_concurrent=args.max_concurrent,
        exp_mode=args.exp_mode,
        aspect_ratio=args.aspect_ratio,
        max_critic_rounds=args.max_critic_rounds,
    ))

    (out_dir / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    pngs = _save_pngs(results, out_dir)
    if pngs:
        print(f"\n✓ generated {len(pngs)} candidate(s):")
        for p in pngs:
            print(f"  - {p}")
        return 0

    print(f"\nwarn: no candidate PNGs produced. See {out_dir / 'results.json'} for raw responses.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
