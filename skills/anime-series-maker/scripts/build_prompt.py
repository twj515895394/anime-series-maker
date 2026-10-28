#!/usr/bin/env python3
"""Compile a portable, offline V1 prompt pack from approved-or-draft text assets.

No Renoise, API, MCP, model routing, external imports or generation calls.
This command compiles drafts; final release approval is enforced by export_prompt_pack.py.

Usage:
 python build_prompt.py my-series/series.json my-series/episodes/ep001/episode.json \
     --shots my-series/episodes/ep001/shots.json --out my-series/episodes/ep001/prompts
"""
import argparse
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from validate_project import load_bundle, validate_bundle

COMPILER_VERSION = "1.0.0"
PLACEHOLDER = re.compile(r"\b(?:TODO|TBD)\b|\{\{[^}]*\}\}|material:0+\b", re.I)


def stable_text(value):
    if isinstance(value, str):
        return value.strip()
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def format_state(state):
    return "; ".join(f"{k}: {stable_text(v)}" for k, v in sorted((state or {}).items())) or "No special state specified"


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def assets_for_shot(series, shot):
    """Explicit ref assets first. Otherwise prefer relevant view for each character."""
    asset_map = {}
    per_character = {}
    for actor in series["characters"]:
        per_character[actor["id"]] = actor.get("reference_assets", [])
        for ref in actor.get("reference_assets", []):
            asset_map[ref["asset_id"]] = ref
    explicit = shot.get("references", [])
    if explicit:
        return [asset_map[r] for r in explicit if r in asset_map]
    text = (shot.get("framing","") + " " + shot.get("camera",{}).get("angle","")).lower()
    if any(x in text for x in ("close-up", "close up", "face", "特写")):
        preference = ["face_closeup", "three_quarter", "front", "montage"]
    elif any(x in text for x in ("back", "rear", "背")):
        preference = ["back", "three_quarter", "front", "montage"]
    elif any(x in text for x in ("side", "profile", "侧")):
        preference = ["side", "three_quarter", "front", "montage"]
    else:
        preference = ["front", "three_quarter", "side", "montage"]
    selected = []
    for cid in shot.get("cast", []):
        refs = per_character.get(cid, [])
        for kind in preference:
            candidate = next((a for a in refs if a.get("type") == kind), None)
            if candidate:
                selected.append(candidate)
                break
    return selected


def render_common(series, episode, shot, refs):
    cast = {c["id"]: c for c in series["characters"]}
    locations = {s["id"]:s for s in series.get("locations",[])}
    scenes = {s["id"]:s for s in episode.get("scenes",[])}
    scene = scenes[shot["scene_id"]]
    location = locations.get(scene.get("location_id"), {})
    vs = series["visual_style"]
    lines = [
        f"[SHOT] {shot['shot_id']} | {shot['time']['start_s']}–{shot['time']['end_s']} seconds",
        f"[INTENT] {shot['action']['goal']}",
        "[REFERENCE ASSETS]"
    ]
    if refs:
        for ref in refs:
            lines.append(f"- {ref['asset_id']} ({ref['type']}): {ref['path']} — design reference only; never render reference-sheet panels")
    else:
        lines.append("- No file references provided; use the character identity description below. Do not invent reference assets.")
    lines += ["[CHARACTERS / IDENTITY LOCK]"]
    for cid in shot["cast"]:
        actor = cast[cid]
        lock = actor["identity_lock"]
        profile = actor.get("performance_profile", {})
        lines += [
            f"- {actor['label']} [id={cid}; species={actor.get('species','unspecified')}; form={actor.get('form','unspecified')}]:",
            "  KEEP: " + "; ".join(lock.get("must_keep", [])),
            "  AVOID: " + "; ".join(lock.get("must_avoid", [])),
            "  PERFORMANCE: " + stable_text(profile),
            "  PERSONALITY: " + actor.get("personality", ""),
        ]
    lines += [
        "[STYLE]",
        vs["description"],
        "Medium: " + vs["medium"] + "; aspect ratio: " + vs["aspect_ratio"],
        "[ENVIRONMENT]",
        location.get("description", "Setting follows the episode storyboard."),
        "[START STATE]", format_state(shot["action"].get("continuity_in", {})),
        "[ACTION BEATS]",
    ]
    for i, action in enumerate(shot["action"].get("beats", []), 1):
        lines.append(f"{i}. {action}")
    cam = shot["camera"]
    lines += [
        "[CAMERA]",
        f"Framing: {shot['framing']}; angle: {cam.get('angle','static')}; movement: {cam.get('motion','static')}.",
        "[PERFORMANCE]",
        f"Expression: {shot.get('expression','')} ; gaze: {shot.get('gaze','')}.",
    ]
    dialogues = {line.get("id"):line for line in episode.get("dialogue",[])}
    lines.append("[DIALOGUE / AUDIO GUIDANCE — TEXT ONLY, NO AUDIO GENERATED]")
    for rid in shot.get("dialogue_refs", []):
        line = dialogues.get(rid, {})
        lines.append(f"{line.get('speaker','')}: {line.get('text','')} [{line.get('delivery','natural')}]")
    if not shot.get("dialogue_refs"):
        lines.append("No required dialogue.")
    if shot.get("sound_cues"):
        lines.append("SFX: " + "; ".join(shot["sound_cues"]))
    lines += [
        "[END STATE]",
        format_state(shot["action"].get("continuity_out", {})),
        "Transition: " + shot.get("transition_to_next", "end"),
        "[NEGATIVE CONSTRAINTS]",
        "; ".join(vs.get("negative_style", [])) + "; avoid extra limbs, anatomy drift, unintended captions or logos.",
    ]
    return "\n".join(lines).strip()+"\n"


def render_frame(series, episode, shot, refs, target):
    content = render_common(series, episode, shot, refs)
    action = shot["action"]
    if target == "first_frame":
        instruction = f"STILL IMAGE ONLY — first frame of shot {shot['shot_id']}. Show exactly the START STATE, before the action begins."
    elif target == "last_frame":
        instruction = f"STILL IMAGE ONLY — final frame of shot {shot['shot_id']}. Show exactly the END STATE after the described action."
    else:
        instruction = f"STILL IMAGE ONLY — key action pose of shot {shot['shot_id']}; capture its central beat: {action['beats'][len(action['beats'])//2]}."
    return instruction+"\n\n"+content


def compile_bundle(series, episode, shots, series_path, episode_path, shots_path, out):
    """Compile all files after validation. Return manifest dictionary."""
    refs = [series_path, episode_path, shots_path]
    source_hashes = {name: sha256(path) for name, path in zip(("series","episode","shots"), refs)}
    manifest = {"schema_version": "1.0", "episode_id": episode["episode_id"],
                "compiler_version": COMPILER_VERSION, "source_hashes": source_hashes, "prompts": []}
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    for shot in shots["shots"]:
        shid = shot["shot_id"]
        references = assets_for_shot(series,shot)
        for target in dict.fromkeys(shot.get("prompt_targets", ["video"])):
            content = render_common(series,episode,shot,references) if target == "video" else render_frame(series,episode,shot,references,target)
            if PLACEHOLDER.search(content):
                raise ValueError(f"Unresolved placeholder in shot {shid} ({target})")
            filename = f"{shid}.{target.replace('_','-')}.md"
            path = out / filename
            path.write_text(content, encoding="utf-8")
            manifest["prompts"].append({
                "shot_id":shid, "prompt_type":target,
                "path":os.path.relpath(path, Path(episode_path).parent).replace(os.sep,"/"),
                "reference_asset_ids":[r["asset_id"] for r in references],
                "duration_s":shot["time"]["end_s"]-shot["time"]["start_s"],
                "aspect_ratio":series["visual_style"]["aspect_ratio"],
                "source_hashes":source_hashes
            })
    (Path(episode_path).parent/"prompt-manifest.json").write_text(
        json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return manifest


def main():
    ap = argparse.ArgumentParser(description="Offline, model-neutral shot prompt compiler")
    ap.add_argument("series",type=Path)
    ap.add_argument("episode",type=Path)
    ap.add_argument("--shots",type=Path,required=True)
    ap.add_argument("--out",type=Path)
    args=ap.parse_args()
    try:
        series,episode,shots=load_bundle(args.series,args.episode,args.shots)
        diagnostics=validate_bundle(series,episode,shots,args.series.parent)
        failures=[d for d in diagnostics if d["severity"]=="ERROR"]
        for d in diagnostics:
            print(f"{d['severity']} {d['code']} [{d.get('shot_id') or d['artifact']}]: {d['message']}", file=sys.stderr)
        if failures:
            print(f"Not built: {len(failures)} structural errors",file=sys.stderr)
            return 1
        out=args.out or args.episode.parent/"prompts"
        manifest=compile_bundle(series,episode,shots,args.series,args.episode,args.shots,out)
        print(f"OK {len(manifest['prompts'])} prompts → {out} (text only; nothing generated)")
        return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(f"ERROR {exc}",file=sys.stderr)
        return 2


if __name__=="__main__":
    sys.exit(main())
