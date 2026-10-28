# Anime Series Maker · V1 Prompt-only

**Character references + a story idea → series bible → script → textual storyboards → portable per-shot video prompts and optional frame prompts.**

This fork is now a **local prompt planning skill**. It does not call Renoise, MCP, ComfyUI, a generation API, or a billing service. It does not generate actual images, video, audio or edited MP4. Outputs are editable text and JSON for use in tools of your choice.

[简体中文](README.zh-CN.md) · [Product SPEC](docs/SPEC-V1-ANTHRO-STORYBOARD-PROMPT-ONLY.md) · [Implementation design](docs/SKILL-V1-REFACTOR-DESIGN.md)

## Install

~~~bash
git clone https://github.com/twj515895394/anime-series-maker.git
cd anime-series-maker
git switch codex/anthro-v1-implementation
mkdir -p ~/.codex/skills
cp -R skills/anime-series-maker ~/.codex/skills/
~~~

You may also install the folder at ~/.claude/skills/anime-series-maker in Claude Code. Python 3 is the only required local runtime for validating/compiling/exporting prompts.

## Workflow

1. Import real character reference files or start with text-only character descriptions.
2. Review a reusable series bible (species, appearance, costumes, visual style, asset IDs).
3. Pick one of three premises and approve the screenplay.
4. Approve timed shot breakdowns and action continuity states.
5. Validate files, compile per-shot prompts, inspect and approve the result.
6. Export a copy-ready Markdown prompt pack. Nothing is rendered or submitted.

### Offline CLI

Create a project directory holding series.json and episodes/ep001/{episode.json,shots.json,review.json}; copies of the JSON templates are provided under skills/anime-series-maker/templates/.

~~~bash
cd skills/anime-series-maker
python scripts/validate_project.py my-series --episode ep001
python scripts/build_prompt.py my-series/series.json my-series/episodes/ep001/episode.json --shots my-series/episodes/ep001/shots.json
python scripts/export_prompt_pack.py my-series/episodes/ep001 --draft
# After explicit human confirmation, record hash-bound approvals in order:
python scripts/review_artifact.py my-series/episodes/ep001 --artifact series
python scripts/review_artifact.py my-series/episodes/ep001 --artifact episode
python scripts/review_artifact.py my-series/episodes/ep001 --artifact shots
python scripts/review_artifact.py my-series/episodes/ep001 --artifact prompts
python scripts/export_prompt_pack.py my-series/episodes/ep001
~~~

The template is text-only and has no bundled image files. Real reference asset IDs and paths must point to existing local files; missing assets are errors. Prompts from a text-only character receive a warning.

The final exporter checks approval and the source hashes stored by the compiler; modified storyboards must be recompiled. It writes shot-list.md, prompt-pack.md and continuity-report.md under export/.

### Run tests

~~~bash
python -m unittest discover -s skills/anime-series-maker/tests -v
~~~

## Intended uses

Stylized 3D anthropomorphic characters (e.g., bipedal animal roles acting in human dramas), 2D originals, dialogue scenes, action choreography storyboards, ongoing episodic series, and reusable character identity across shots. Medium-specific styles are configurable; no default "no 3D" clause is injected into 3D work.

Original upstream FFmpeg utilities remain available as legacy helpers but are not used in the V1 Skill.

## Rights

Recognizable copyrighted characters may still require rights clearances for public or commercial derivatives. Hiding franchise names in prompts does not grant rights.

MIT License.
