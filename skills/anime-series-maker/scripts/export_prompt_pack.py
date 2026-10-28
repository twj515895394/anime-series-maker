#!/usr/bin/env python3
"""Export storyboards and copy-ready prompt files; never invoke generators.

By default final export requires human-approved review statuses and current
input hashes. Use --draft only when explicitly exporting an unapproved draft.
"""
import argparse
import json
import sys
from pathlib import Path
from validate_project import load_bundle, validate_bundle, render_report
from build_prompt import sha256
from review_artifact import expected_hashes


def check_approval(review_path, allow_draft):
    if allow_draft:
        return
    if not review_path.is_file():
        raise ValueError("review.json missing: final export requires approved artifacts; use --draft for draft")
    review = json.loads(review_path.read_text(encoding="utf-8"))
    entries = {a.get("artifact_id"): a for a in review.get("artifacts", [])}
    for key in ("series", "episode", "shots", "prompts"):
        entry = entries.get(key, {})
        if entry.get("status") != "approved":
            raise ValueError(f"{key} is not approved in review.json; use --draft for draft")
        if entry.get("source_hashes") != expected_hashes(review_path.parent, key):
            raise ValueError(f"Approval for {key} is stale; request new human approval before final export")


def export_episode(episode_dir, out, allow_draft=False):
    episode_dir = Path(episode_dir)
    root = episode_dir.parents[1]
    series_path, episode_path, shots_path = root/"series.json", episode_dir/"episode.json", episode_dir/"shots.json"
    series, episode, shots = load_bundle(series_path, episode_path, shots_path)
    diagnostics = validate_bundle(series, episode, shots, root)
    if any(d["severity"]=="ERROR" for d in diagnostics):
        raise ValueError("Validation failed; fix all structural errors before export")
    manifest_path = episode_dir/"prompt-manifest.json"
    if not manifest_path.is_file():
        raise ValueError("prompt-manifest.json missing; run build_prompt.py first")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected = {"series":sha256(series_path),"episode":sha256(episode_path),"shots":sha256(shots_path)}
    if manifest.get("source_hashes") != expected:
        raise ValueError("Prompt pack is stale: source files have changed; re-run build_prompt.py")
    check_approval(episode_dir/"review.json", allow_draft)
    rows = [
        "# " + episode.get("title",episode["episode_id"]) + " — 分镜表",
        "",
        f"> 模式：{'DRAFT — NOT APPROVED' if allow_draft else 'APPROVED TEXT-ONLY'}；不是已生成视频。",
        "",
        "| 镜头 | 时间（秒） | 场景 | 景别 | 动作目标 | 摄影机 | 衔接 |",
        "|---|---|---|---|---|---|---|",
    ]
    for shot in shots["shots"]:
        clean = lambda v: str(v).replace("|","/").replace("\n"," ")
        rows.append("| " + " | ".join(map(clean,[
            shot["shot_id"], f"{shot['time']['start_s']}–{shot['time']['end_s']}",
            shot["scene_id"], shot["framing"], shot["action"]["goal"],
            shot["camera"].get("motion","static"),shot.get("transition_to_next","end")])) + " |")
    rows.append("")
    pack = ["# " + episode.get("title",episode["episode_id"]) + " — 镜头 Prompt Pack",
            "","> 此文件只有分镜和可复制提示词，不包含真实图片、视频或音频。",""]
    for item in manifest["prompts"]:
        prompt_path = (episode_dir / item["path"]).resolve()
        try:
            prompt_path.relative_to(episode_dir.resolve())
        except ValueError as exc:
            raise ValueError("Unsafe prompt path in manifest") from exc
        if not prompt_path.is_file():
            raise ValueError(f"Missing prompt {prompt_path}")
        text = prompt_path.read_text(encoding="utf-8")
        pack += [f"## {item['shot_id']} · {item['prompt_type']}", "",
                 f"参考素材 ID：{', '.join(item['reference_asset_ids']) or '无'}",
                 "", "~~~text", text.rstrip(), "~~~", ""]
    out = Path(out)
    out.mkdir(parents=True,exist_ok=True)
    (out/"shot-list.md").write_text("\n".join(rows)+"\n",encoding="utf-8")
    (out/"prompt-pack.md").write_text("\n".join(pack),encoding="utf-8")
    (out/"continuity-report.md").write_text(render_report(diagnostics),encoding="utf-8")
    return len(manifest["prompts"])


def main():
    ap = argparse.ArgumentParser(description="Export prompt-only review pack (offline)")
    ap.add_argument("episode_dir",type=Path)
    ap.add_argument("--out",type=Path)
    ap.add_argument("--draft",action="store_true",help="Explicitly export an unapproved draft")
    args = ap.parse_args()
    try:
        n=export_episode(args.episode_dir,args.out or args.episode_dir/"export",args.draft)
        print(f"OK: exported {n} copy-ready prompts (no media generated)")
        return 0
    except (OSError,KeyError,ValueError,TypeError) as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        return 1


if __name__=="__main__":
    sys.exit(main())
