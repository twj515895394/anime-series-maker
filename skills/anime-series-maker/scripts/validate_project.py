#!/usr/bin/env python3
"""Offline checks for V1 series, episode, storyboards and assets.

No cloud calls or external dependencies. Both this CLI and build_prompt.py
use validate_bundle(); diagnostic severity is ERROR or WARN.
"""
import argparse
import json
import sys
from pathlib import Path

VERSION = "1.0"
ALLOWED_TARGETS = {"video", "first_frame", "last_frame", "keyframe"}
CONTINUOUS = {"continuous_cut", "match_cut", "continue"}


def diagnostic(severity, code, artifact, field, message, shot_id=None):
    return {"severity": severity, "code": code, "artifact": artifact,
            "field": field, "shot_id": shot_id, "message": message}


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def is_relative_asset(root, relative_path):
    if not isinstance(relative_path, str) or not relative_path.strip():
        return False
    p = Path(relative_path)
    if p.is_absolute():
        return False
    root, candidate = Path(root).resolve(), (Path(root) / p).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def validate_bundle(series, episode, shots, root, check_assets=True):
    """Validate plain dictionaries. root is the directory holding series.json."""
    errors = []
    def add(level, code, file, field, message, shot_id=None):
        errors.append(diagnostic(level, code, file, field, message, shot_id))
    if any(not isinstance(x, dict) for x in (series, episode, shots)):
        add("ERROR", "INVALID_OBJECT", "bundle", "", "All inputs must be JSON objects")
        return errors

    for name, obj in (("series", series), ("episode", episode), ("shots", shots)):
        if obj.get("schema_version") != VERSION:
            add("ERROR", "SCHEMA_VERSION", name, "schema_version", "Expected schema_version 1.0")

    if not series.get("series_id") or not series.get("title"):
        add("ERROR", "SERIES_REQUIRED", "series", "series_id/title", "Series needs id and title")
    style = series.get("visual_style", {})
    if not isinstance(style, dict) or not all(style.get(k) for k in ("medium", "description", "aspect_ratio")):
        add("ERROR", "STYLE_REQUIRED", "series", "visual_style", "Specify medium, description, aspect_ratio")
        style = {}
    if episode.get("series_id") != series.get("series_id"):
        add("ERROR", "SERIES_MISMATCH", "episode", "series_id", "Episode references a different series")
    if shots.get("episode_id") != episode.get("episode_id"):
        add("ERROR", "EPISODE_MISMATCH", "shots", "episode_id", "Shot list belongs to another episode")
    try:
        duration = float(episode.get("target_duration_s", 0))
        if duration <= 0:
            raise ValueError()
    except (TypeError, ValueError):
        duration = 0
        add("ERROR", "INVALID_DURATION", "episode", "target_duration_s", "Target duration must be positive")

    characters, assets = {}, {}
    for ci, char in enumerate(series.get("characters", []) or []):
        cid = char.get("id", "")
        if not cid or cid in characters:
            add("ERROR", "DUPLICATE_CHARACTER", "series", f"characters[{ci}].id", "Missing or duplicated character id")
            continue
        characters[cid] = char
        lock = char.get("identity_lock", {})
        profile = char.get("performance_profile", {})
        if not isinstance(lock, dict) or not lock.get("must_keep"):
            add("ERROR", "IDENTITY_REQUIRED", "series", f"characters[{ci}].identity_lock", "At least one stable identity detail required")
        if not isinstance(profile, dict) or not profile.get("locomotion"):
            add("WARN", "PERFORMANCE_INCOMPLETE", "series", f"characters[{ci}].performance_profile", "Specify locomotion and usable hands/paws")
        for ri, asset in enumerate(char.get("reference_assets", []) or []):
            aid, p = asset.get("asset_id"), asset.get("path")
            if not aid or aid in assets:
                add("ERROR", "DUPLICATE_ASSET", "series", f"characters[{ci}].reference_assets[{ri}]", "Reference asset id missing or duplicated")
                continue
            if not is_relative_asset(root, p):
                add("ERROR", "UNSAFE_ASSET_PATH", "series", f"characters[{ci}].reference_assets[{ri}].path", "Use a relative file within project root")
                continue
            assets[aid] = asset
            if check_assets and not (Path(root) / p).is_file():
                add("ERROR", "MISSING_ASSET", "series", f"characters[{ci}].reference_assets[{ri}].path", f"Reference file not found: {p}")
        refs = char.get("reference_assets", []) or []
        if refs and not any(x.get("type") == "face_closeup" for x in refs):
            add("WARN", "NO_FACE_CLOSEUP", "series", f"characters[{ci}].reference_assets", "Face close-up recommended for facial shots")
        if not refs:
            add("WARN", "NO_REFERENCE_ASSETS", "series", f"characters[{ci}].reference_assets", "Text-only character description; add real design sheets for greater consistency")
    if not characters:
        add("ERROR", "NO_CHARACTERS", "series", "characters", "A series needs at least one character")

    locations = {}
    for index, item in enumerate(series.get("locations", []) or []):
        lid = item.get("id")
        if not lid or lid in locations:
            add("ERROR", "DUPLICATE_LOCATION", "series", f"locations[{index}].id", "Missing/duplicate location id")
        else:
            locations[lid] = item
    scenes = {}
    for i, scene in enumerate(episode.get("scenes", []) or []):
        sid = scene.get("id")
        if not sid or sid in scenes:
            add("ERROR", "DUPLICATE_SCENE", "episode", f"scenes[{i}].id", "Missing/duplicate scene id")
            continue
        scenes[sid] = scene
        if scene.get("location_id") not in locations:
            add("ERROR", "UNKNOWN_LOCATION", "episode", f"scenes[{i}].location_id", "Scene location id not in series")
        for cid in scene.get("cast", []):
            if cid not in characters:
                add("ERROR", "UNKNOWN_CHARACTER", "episode", f"scenes[{i}].cast", f"Unknown character {cid}")

    dialogue_ids = {d.get("id") for d in episode.get("dialogue", []) if isinstance(d, dict)}
    timeline, shot_ids = [], set()
    for idx, shot in enumerate(shots.get("shots", []) or []):
        sid = shot.get("shot_id")
        if not sid or sid in shot_ids:
            add("ERROR", "DUPLICATE_SHOT", "shots", f"shots[{idx}].shot_id", "Missing or duplicate shot id")
            sid = sid or f"index-{idx}"
        shot_ids.add(sid)
        if shot.get("scene_id") not in scenes:
            add("ERROR", "UNKNOWN_SCENE", "shots", "scene_id", "Unknown scene id", sid)
        cast = shot.get("cast", [])
        if not cast:
            add("ERROR", "EMPTY_CAST", "shots", "cast", "Shot cast cannot be empty", sid)
        for cid in cast:
            if cid not in characters:
                add("ERROR", "UNKNOWN_CHARACTER", "shots", "cast", f"Unknown character {cid}", sid)
        for ref in shot.get("references", []) or []:
            if ref not in assets:
                add("ERROR", "UNKNOWN_ASSET", "shots", "references", f"Unknown asset id {ref}", sid)
            elif not any(ref == a.get("asset_id") for cid in cast for a in characters.get(cid, {}).get("reference_assets", [])):
                add("WARN", "ASSET_OUTSIDE_CAST", "shots", "references", f"Asset {ref} not attached to an on-screen character", sid)
        for ref in shot.get("dialogue_refs", []) or []:
            if ref not in dialogue_ids:
                add("ERROR", "UNKNOWN_DIALOGUE", "shots", "dialogue_refs", f"Unknown dialogue id {ref}", sid)
        if not shot.get("framing") or not isinstance(shot.get("camera"), dict) or not shot["camera"].get("angle"):
            add("ERROR", "SHOT_CAMERA", "shots", "framing/camera", "Shot needs framing and camera angle", sid)
        action = shot.get("action")
        if not isinstance(action, dict) or not action.get("goal") or not action.get("beats"):
            add("ERROR", "SHOT_ACTION", "shots", "action", "Shot needs goal and ordered action beats", sid)
            action = {}
        if not isinstance(action.get("continuity_in"), dict) or not isinstance(action.get("continuity_out"), dict):
            add("ERROR", "SHOT_STATES", "shots", "action", "Specify continuity_in and continuity_out dictionaries", sid)
        targets = shot.get("prompt_targets", ["video"])
        if not targets or any(t not in ALLOWED_TARGETS for t in targets):
            add("ERROR", "INVALID_TARGETS", "shots", "prompt_targets", "Unsupported prompt target", sid)
        times = shot.get("time", {})
        try:
            start, end = float(times["start_s"]), float(times["end_s"])
            if start < 0 or end <= start:
                raise ValueError()
            timeline.append((start, end, shot))
        except (ValueError, TypeError, KeyError):
            add("ERROR", "SHOT_TIME", "shots", "time", "Invalid start_s or end_s", sid)
    if not timeline:
        add("ERROR", "NO_SHOTS", "shots", "shots", "At least one valid shot required")
    timeline.sort(key=lambda x: (x[0], x[1]))
    if timeline and abs(timeline[0][0]) > .05:
        add("ERROR", "START_NOT_ZERO", "shots", "time", "First shot must start at 0")
    for (a, b, current), (c, d, nxt) in zip(timeline, timeline[1:]):
        if abs(b - c) > .05:
            add("ERROR", "TIMELINE_GAP_OR_OVERLAP", "shots", "time", f"Previous end={b}; next start={c}", nxt.get("shot_id"))
        if current.get("transition_to_next", "continuous_cut") in CONTINUOUS and current.get("scene_id") == nxt.get("scene_id"):
            out_state = current.get("action", {}).get("continuity_out", {})
            in_state = nxt.get("action", {}).get("continuity_in", {})
            for key in ("position", "orientation", "left_hand", "right_hand"):
                if key in out_state and key in in_state and out_state[key] != in_state[key]:
                    add("ERROR", "CONTINUITY_STATE_CONFLICT", "shots", f"action.continuity_in.{key}",
                        f"Previous {key}={out_state[key]!r}, next {key}={in_state[key]!r}", nxt.get("shot_id"))
            old_props, new_props = out_state.get("prop_owner", {}), in_state.get("prop_owner", {})
            for prop in set(old_props) & set(new_props):
                if old_props[prop] != new_props[prop]:
                    add("ERROR", "CONTINUITY_PROP_OWNER_CONFLICT", "shots", f"action.continuity_in.prop_owner.{prop}",
                        f"Prop {prop} holder changes without transfer", nxt.get("shot_id"))
    if timeline and duration and abs(timeline[-1][1] - duration) > .05:
        add("ERROR", "DURATION_MISMATCH", "shots", "time", "Last shot end does not equal target_duration_s")
    return errors


def load_bundle(series_path, episode_path, shots_path):
    try:
        return [read_json(path) for path in (series_path, episode_path, shots_path)]
    except (OSError, ValueError) as exc:
        raise ValueError(f"Cannot read JSON bundle: {exc}") from exc


def render_report(diagnostics):
    count = sum(d["severity"] == "ERROR" for d in diagnostics)
    lines = [f"# Offline validation report", "", f"Errors: {count}, warnings: {len(diagnostics)-count}", ""]
    for d in diagnostics:
        label = d.get("shot_id") or d["artifact"]
        lines.append(f"- **{d['severity']} {d['code']}** [{label}] {d['field']}: {d['message']}")
    if not diagnostics:
        lines.append("No structural or continuity issues detected. This does not certify generated media.")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description="Validate storyboard/project files without external services")
    ap.add_argument("project_root", type=Path)
    ap.add_argument("--episode", default="ep001", help="Episode directory name beneath episodes/")
    ap.add_argument("--json", action="store_true", help="Machine-readable diagnostics")
    ap.add_argument("--report", type=Path, help="Optional Markdown report output")
    args = ap.parse_args()
    root = args.project_root
    episode_dir = root / "episodes" / args.episode
    try:
        series, episode, shots = load_bundle(root/"series.json", episode_dir/"episode.json", episode_dir/"shots.json")
        diagnostics = validate_bundle(series, episode, shots, root)
    except ValueError as exc:
        print(f"ERROR {exc}", file=sys.stderr)
        return 2
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(render_report(diagnostics), encoding="utf-8")
    if args.json:
        print(json.dumps(diagnostics, ensure_ascii=False, indent=2))
    else:
        print(render_report(diagnostics))
    return 1 if any(d["severity"] == "ERROR" for d in diagnostics) else 0


if __name__ == "__main__":
    sys.exit(main())
