# Action and continuity · 动作与连续性

## Explicit states across cuts

Track at minimum when applicable: scene_id, actor position, facing/orientation, gaze, pose, support foot, left_hand, right_hand, prop_owner, outfit variant, tail_state, injury and fatigue. State fields refer to story facts, not model-specific 3D joint values.

For continuous cuts in the same scene, the next shot's entry state must match the previous shot's exit state for any explicitly tracked common field. Hard cuts can omit steps, but prop transfers, outfit changes or location changes must be plausible and documented. The V1 validator checks basic explicit contradictions, not full physical validity.

## Complex action composition

Use: intent → preparation → initial motion → contact/impact → resulting motion → recovery/reaction. For a chase or fight, specify location and orientation for both actors, who starts each action, who receives it, relative distance and whether momentum carries into the next frame.

Physical effort matters: after repeated strenuous movement or impacts, note breathing rhythm, posture and slowing movements. It is not necessary to introduce exhaustion in a light dialogue shot; reserve it for narrative continuity.

## Camera continuity

Keep screen travel direction unless a motivated angle change is shown. In dialogue shot/reverse-shot, document eyelines so left/right speaking positions stay recognizable. Don't combine an orbiting camera with complex multi-character contact in a single prompt unless the user explicitly wants the risk.

## Example: handoff

S1: character A ends with right_hand=holding phone, prop_owner.phone=A.
S2 continuous: starts with right_hand=holding phone, prop_owner.phone=A.
S2 action: passes phone to B, then exits with prop_owner.phone=B and B's corresponding paw holding it.
S3: B starts holding phone. Never allow unexplained teleportation from A to B.

## Confidence boundaries

These rules make descriptions consistent, but do not guarantee a downstream video model's motion or anatomy. Mark high-risk shots for additional image keyframe prompts or later human visual review.
