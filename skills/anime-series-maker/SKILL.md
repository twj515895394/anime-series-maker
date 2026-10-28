---
name: anime-series-maker
description: Plan character-driven animation and episodic series; maintain reusable character identity, design premise/script/storyboards, track motion continuity, and export portable shot-level image/video prompts. Includes stylized 3D anthropomorphic characters, 2D anime and other styles. Prompt-only and offline: does not create images, videos or audio, and never requires Renoise MCP or any generation API. Use for 动漫短剧、番剧、拟人化角色、3D动画、角色一致性、剧情、剧本、分镜、逐镜头提示词、下一集.
---

# Anime Series Maker · V1 Prompt-only

**Goal:** deliver a complete, reviewable text production pack; NOT a finished video. No generation, model routing, account lookup, billing, uploads, backend tasks, downloading, editing or publishing. The author may copy prompts into any external tool later, outside this skill.

Read the key references when applicable:
- references/anthro-character.md — 3D anthropomorphic identity, anatomy, hand/paw, ears and tail.
- references/storyboard.md — story beats, shot grammar, pacing and frame planning.
- references/action-continuity.md — multi-shot motion, prop handoff, orientation, fatigue.
- references/prompt-portability.md — backend-neutral prompt composition.
- references/style-presets.md — optional medium-specific style choices.
- references/hooks.md — optional social-media comedy hooks only when suitable.

## Input and project organization

Default workspace: ./my-series/ (user may choose another directory).

    my-series/
      project.json
      series.json
      assets/characters/<id>/...
      episodes.json                    # optional manually maintained history
      episodes/ep001/
        episode.json
        shots.json
        review.json
        prompts/
          sh001.video.md
          sh001.first-frame.md         # optional
          sh001.last-frame.md          # optional
        prompt-manifest.json
        export/
          shot-list.md
          prompt-pack.md
          continuity-report.md

Templates are in templates/*.json; v1 schemas in schemas/*.schema.json. Always use actual local relative file paths and stable asset IDs. NEVER invent image files, claim that montage views were already cropped, or silently replace a user-provided face reference.

Series is the single source of truth for a character's fixed identity. Episode describes story beats, scene and dialogue. Shots describe camera, time, actions, state and reference mapping. Never make a shot an immutable cloud-model clip; its duration is a storytelling choice.

## Stage S0 — Prepare the workspace (no remote setup)

Check existing project files. If nothing exists, ask for the minimum missing information in one compact message: character images/assets, the intended story, format (standalone or ongoing), medium (2D/3D/stylized), aspect ratio, dialogue language, approximate runtime and desired motion complexity. User-supplied references take precedence; use a neutral default for any optional input.

Create a project.json with workflow_mode = prompt_only, plus series.json, episode.json and shots.json from the v1 templates. If restoring a project, inspect the previous files and review status; do not overwrite approved content.

No Renoise, no MCP, no ffmpeg, no GPU or API credentials are required.

## Stage S1 — Series Bible and asset mapping [APPROVAL]

Record character name/ID, species, anthropomorphic form, style, outfit, color/fur, face, eyes, ears, tail, hands/paws, body proportions, personality, voice description and recurring wardrobe/props. For each actual reference, record its asset_id, view type and path. View types include front, back, side, three_quarter, face_closeup, expressions, pose and montage.

Show a readable summary of the character identity and reference coverage. Ask for approval before downstream writing. Explain missing views without hallucinating them. For close-up face shots, prefer a real face_closeup asset; if unavailable, warn and fall back to an existing known view.

Visual medium must be explicit: the 3D anthropomorphic preset does NOT inherit 2D constraints such as "everything hand drawn" or "no 3D render". Other 2D and live-action styles remain opt-in.

## Stage S2 — Premises and story outline [APPROVAL]

Offer 3 concise premise choices and recommend one; their purpose is exploration, not a mandatory viral template. Respect user genre, story length, tone and audience. For episodic projects, check series continuity and any available episodes.json to avoid contradictions.

After selection, write an outline: setup, inciting incident, escalation, decision/turn, consequence and ending. Do not force a romance/comedy or 3-second twist when the story is dramatic/action-driven.

## Stage S3 — Screenplay and beats [APPROVAL]

Populate episode.json from the selected outline: episode_id/series_id, target_duration_s, premise, beats, scenes, dialogue with stable ids/speakers and optional duration estimates, start/end story state.

Script dialogue must follow the approved language, personalities, relationships and rhythm. Give all supporting characters IDs before reference. Identify important object transfers and costume changes in the script. Present a human-readable screenplay and wait for explicit approval.

## Stage S4 — Storyboard and action continuity [APPROVAL]

Populate shots.json with each shot's shot_id, scene_id, start/end seconds, cast IDs, framing, camera angle/motion, one primary action goal and ordered action beats, expression/gaze, reference_asset_ids, dialogue_refs, transition, continuity_in/out, and prompt_targets.

For a complex action, split into preparation, locomotion, contact/impact, reaction and recovery. Record support foot/pose, left/right paws, prop owners, facing direction and fatigue when relevant. For repeated shots of the same person, maintain their animal ears/muzzle/tail and fixed costume. For cut-to-reverse-shot scenes, explain gaze and screen direction. Avoid arbitrary 2–3-second / 15-second model limits.

Display a compact shot table plus continuity risks. User approves S4 before creating the final prompt pack. Optional first/last/keyframe *prompts* (not image files) should be requested for complex camera/action shots, not mandatory for every shot.

## Stage S5 — Validate and compile portable prompts [APPROVAL]

The following commands are local, deterministic text operations only (run from the skill directory, or use equivalent absolute script paths):

~~~bash
python scripts/validate_project.py my-series --episode ep001 --report my-series/episodes/ep001/export/continuity-report.md
python scripts/build_prompt.py my-series/series.json my-series/episodes/ep001/episode.json --shots my-series/episodes/ep001/shots.json --out my-series/episodes/ep001/prompts
~~~

Errors block building or final export; warnings require user review, especially missing face assets or high-complexity pose assumptions. The generated prompts contain descriptive paths/asset IDs, not Renoise material tokens. One .video.md per shot, plus optional .first-frame.md, .last-frame.md or .keyframe.md. Inspect generated prompts with the user and record approval in review.json.

Do NOT call any video/image/audio generation backend at this stage, even if a connector is installed. No fabricated media preview. If the user's goal is to obtain actual clips, explicitly explain that V1 only prepares prompts.

## Stage S6 — Export text pack and archive

The reviewer records status=approved for series, episode, shots and prompts in review.json, with notes/revisions as desired. Final export requires these approvals, and build source hashes must still match. Incomplete projects can be exported with --draft and marked visibly as NOT APPROVED:

~~~bash
python scripts/export_prompt_pack.py my-series/episodes/ep001 --out my-series/episodes/ep001/export
# For explicitly requested unapproved text drafts:
python scripts/export_prompt_pack.py my-series/episodes/ep001 --draft
~~~

Delivery: export/shot-list.md, export/prompt-pack.md, export/continuity-report.md, prompts/*.md, prompt-manifest.json and source JSON. The package is ready to copy to a user-chosen tool, but it is NOT a produced video. Optionally log completed planning episodes in episodes.json; do not claim distribution performance without actual user data.

## Review semantics and resumption

A review.json artifact status is draft / needs_review / approved / stale / rejected. On any material upstream modification, mark dependent artifacts as stale and regenerate affected prompts. Source-hash comparison in the exporter detects out-of-date compiled prompts even if someone forgot to mark stale. For a new episode reuse series.json; never rewrite its cast silently.

Current v1 implementation provides basic approval gating and source-hash freshness; automatic incremental invalidation of all content dependencies is a later enhancement. If review history is absent, do not infer approval from the chat conversation.

## Output quality guardrails

- A character's identity does not mutate merely because they stand or gesture like a human. For anthropomorphic characters keep species-specific face, fur, ears, tail and stylized paws; do not invent human fingers or human skin.
- Action state is explicit, not just adjectives. The right paw holding a phone at a shot's end must remain consistent in the next continuous shot.
- Storyboard and compiled prompt both carry shot IDs. Every chosen reference file must exist if named as a local asset; if missing, show a warning or validation failure.
- Don't inject a nonexistent face close-up, unauthorized source reference, camera view, costume, or invented scene.
- No default soundtrack, lip-sync or subtitles are generated. Dialogue/SFX text is guidance only.
- Distinguish deterministic JSON checks from subjective artistic QA: no claim that real video visual quality was inspected.
- For recognizable existing copyrighted characters: modifying appearance or omitting names does not establish rights. Recommend rights review before commercial/public release.
- Never trigger create_tasks / upload_files / estimate_cost / wait_tasks or any cloud model. V1 does not have a generation step.

## Implementation references

The output contracts and acceptance criteria are in docs/SPEC-V1-ANTHRO-STORYBOARD-PROMPT-ONLY.md and docs/SKILL-V1-REFACTOR-DESIGN.md at the repository root (outside the installed skill folder). These are implementation specifications, not promises of video generation.
