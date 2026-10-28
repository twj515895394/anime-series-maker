# Portable prompt design · 可移植提示词设计

V1 outputs TEXT. References are expressed as asset IDs and local paths, not material tokens or proprietary service syntax. Keep all source content model-neutral.

## Standard block order

[SHOT INTENT] — one visible goal, starting situation, dramatic intention.
[REFERENCE ASSETS] — actual assets, view type and file path; say sheets are design references, not on-screen scene.
[CHARACTERS / IDENTITY LOCK] — unchanged species, face, coat, clothes, accessories.
[STYLE] — choose one 2D/3D/other medium; do not mix contradictory negative styles.
[ENVIRONMENT] — fixed scene and lighting.
[START STATE] — actor pose, placement, orientation, object ownership.
[ACTION BEATS] — ordered action and emotional progression.
[CAMERA] — framing, angle, movement and screen placement.
[PERFORMANCE] — facial expressions, ear/tail and posture acting.
[DIALOGUE / AUDIO GUIDANCE] — optional text; never claim audio generated.
[END STATE] — final visible pose and handoff to subsequent shot.
[NEGATIVE CONSTRAINTS] — targeted exclusions; avoid excessive boilerplate.

### Image prompt type

first_frame = state before action; last_frame = state after action; keyframe = mid-action readable contact pose. Each uses exactly the same actor lock, style and asset references as the video shot. A single reference montage alone is NOT the actual scene image.

### Compiling and QA

- Compiler must never rewrite approved story beats or dialogue, fabricate file paths or remote ID strings, or silently turn user-selected 3D into 2D.
- Include full standalone context per prompt (with repeated identity lock), because target tools may not share conversation memory.
- No universal prompt length requirement: use readable, unambiguous blocks. Backends with character limits may later add compact renderers.
- Structural errors are blockers; visual consistency and physical plausibility require external generation and review, so they remain future QA.
