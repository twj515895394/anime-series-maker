#!/usr/bin/env python3
"""Record explicit human approval of offline artifacts with source hash provenance.

Invocation of this command represents user approval, not an automated decision.
After a change upstream, downstream approvals become stale even if the prompt
compiler has already been re-run.
"""
import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from build_prompt import sha256

ORDER = ("series","episode","shots","prompts")
SOURCE = {
    "series": ("series",),
    "episode": ("series","episode"),
    "shots": ("series","episode","shots"),
    "prompts": ("series","episode","shots","manifest","prompt_files"),
}


def source_hashes(episode_dir):
    ep=Path(episode_dir)
    root=ep.parents[1]
    paths={"series":root/"series.json","episode":ep/"episode.json",
           "shots":ep/"shots.json","manifest":ep/"prompt-manifest.json"}
    hashes={name:sha256(p) for name,p in paths.items() if p.is_file()}
    if paths["manifest"].is_file():
        manifest=json.loads(paths["manifest"].read_text(encoding="utf-8"))
        check=hashlib.sha256()
        for item in manifest.get("prompts",[]):
            p=(ep/item["path"]).resolve()
            try:
                p.relative_to(ep.resolve())
            except ValueError as exc:
                raise ValueError("Unsafe prompt path") from exc
            if not p.is_file():
                raise ValueError(f"Missing prompt for review: {p}")
            check.update(item["path"].encode("utf-8"))
            check.update(p.read_bytes())
        hashes["prompt_files"]=check.hexdigest()
    return hashes


def expected_hashes(episode_dir,artifact):
    keys=SOURCE[artifact]
    found=source_hashes(episode_dir)
    missing=[key for key in keys if key not in found]
    if missing:
        raise ValueError(f"Cannot approve {artifact}; missing files: {', '.join(missing)}")
    return {key:found[key] for key in keys}


def read_review(episode_dir):
    path=Path(episode_dir)/"review.json"
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"schema_version":"1.0","artifacts":[
        {"artifact_id":name,"revision":1,"status":"needs_review","dependencies":list(SOURCE[name][:-1])}
        for name in ORDER
    ]}


def approve(episode_dir,artifact):
    """Only call upon explicit human approval in the interactive skill."""
    if artifact not in SOURCE:
        raise ValueError(f"Unknown artifact: {artifact}")
    review=read_review(episode_dir)
    entries={item["artifact_id"]:item for item in review["artifacts"]}
    for dep in ORDER[:ORDER.index(artifact)]:
        prior=entries.get(dep,{})
        if prior.get("status")!="approved" or prior.get("source_hashes")!=expected_hashes(episode_dir,dep):
            raise ValueError(f"Cannot approve {artifact}; dependency {dep} needs current approval")
    current=expected_hashes(episode_dir,artifact)
    item=entries.setdefault(artifact,{"artifact_id":artifact,"revision":0})
    previous=item.get("source_hashes")
    item.update({"status":"approved","source_hashes":current,
                 "revision":item.get("revision",0)+(1 if previous!=current else 0),
                 "approved_at":datetime.now(timezone.utc).isoformat()})
    for dep in ORDER[ORDER.index(artifact)+1:]:
        old=entries.get(dep)
        if old and old.get("status")=="approved" and previous!=current:
            old["status"]="stale"
    review["artifacts"]=list(entries.values())
    path=Path(episode_dir)/"review.json"
    path.write_text(json.dumps(review,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return review


def main():
    ap=argparse.ArgumentParser(description="Record explicit artifact approval with hash checks")
    ap.add_argument("episode_dir",type=Path)
    ap.add_argument("--artifact",choices=ORDER,required=True)
    args=ap.parse_args()
    try:
        approve(args.episode_dir,args.artifact)
        print(f"APPROVED {args.artifact} (explicit review recorded)")
        return 0
    except (ValueError,OSError,KeyError,TypeError) as exc:
        print(f"ERROR {exc}",file=sys.stderr)
        return 1


if __name__=="__main__":
    sys.exit(main())
