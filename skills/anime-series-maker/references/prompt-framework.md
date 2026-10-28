# V1 per-shot prompt framework

The source of truth is series.json (identity/style/assets), episode.json (story/dialogue), shots.json (timing/continuity/camera). build_prompt.py creates one portable textual video prompt for each shot and optional image prompt files for first_frame, last_frame or keyframe. The tool does not call generation platforms.

Blocks:
1. [SHOT] stable ID and timeline in seconds.
2. [INTENT] shot action goal.
3. [REFERENCE ASSETS] actual local asset IDs and relative paths, not vendor handles.
4. [CHARACTERS / IDENTITY LOCK] stable face/species/body/clothing and performance profile.
5. [STYLE] one coherent visual medium, no contradictory 2D/3D restrictions.
6. [ENVIRONMENT] location description.
7. [START STATE] action continuity entry state.
8. [ACTION BEATS] specific ordered physical actions.
9. [CAMERA] framing, angle and movement.
10. [PERFORMANCE] emotion, gaze and anatomy expression cues.
11. [DIALOGUE / AUDIO GUIDANCE] text description only.
12. [END STATE] outgoing state and transition.
13. [NEGATIVE CONSTRAINTS] relevant drift and text artifacts.

Avoid packaging an entire episode into one massive universal prompt. Each shot must remain self-contained, traceable and copyable.

For hand/object close-ups include which paw holds the prop. For face close-ups prefer a separate character face reference if one exists. For multi-shot action track direction, support and momentum. Optional image prompts are scene frames, not character sheets. Refer to storyboard.md and action-continuity.md.

Draft prompts can be built before approval for iterative review; final export is gated by review.json and source hashes. Files are preparation assets, not claims of successful video generation.
