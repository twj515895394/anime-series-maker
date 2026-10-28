# Storyboard and story design · 剧本与分镜

## Story stages

1. Present 3 concise premises. Offer a recommendation based on the user's requested genre, not mandatory viral formulas.
2. Write beats: situation → trigger → escalation → decision/turn → consequence/end.
3. Produce screenplay per scene: setting, characters, motivation, action, dialogue and estimated pacing.
4. Convert scenes into stable shot IDs. Each shot has one main narrative/action goal; more than one action beat is allowed when they naturally form one continuous movement.
5. Associate shot ID → episode beat → camera → reference assets → start/end body state → Prompt targets.

## Shot design checklist

- Shot ID and exact start_s/end_s in episode timeline.
- Scene, cast, framing, angle, camera movement, screen direction.
- Visible action (not an emotional adjective alone), performance and gaze.
- Object interaction: who holds what before/after.
- Lines linked by dialogue_refs, SFX instructions as optional text.
- Cut type: continuous_cut, hard_cut, scene_change, end; explain any meaningful transition.
- Select actual character views; a composite turnaround is a design reference and should not appear in the resulting frame.
- Optional first_frame/last_frame/keyframe prompts only when they add camera/animation control.

## Shot duration

Do not impose original 15s provider clip limits on the writer. A shot can be a few seconds or longer according to its dramatic function. Note excessive combinations of fast actions and dialogue as risky. The future generation backend may impose stricter limits, but that must not alter current narrative facts invisibly.

## Storyboard output table

| Shot | Time | Camera | Actor | Start → motion → end | Dialogue | Reference | Transition |
|---|---|---|---|---|---|---|---|

Compiling must retain the exact user-approved lines. The storyboard is the source of truth; each prompt merely translates it to a model-friendly description.
