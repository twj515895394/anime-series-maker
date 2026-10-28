# Anthropomorphic character rules · 拟人化角色

This is a reusable style-specific reference. It is NOT tied to any franchise.

## Character identity: three layers

- Identity lock (usually immutable): species, skull/muzzle, eyes, ears, fur colors, tail, clothing silhouette, boots, backpack, badge and fixed accessories.
- Performance profile (possible actions): upright stance, paw grip, normal walking, sitting, holding a phone, facial expression, ear/tail emotional cues, speech acting.
- Shot state (changes): pose, facing, expression, gaze, support foot, prop location/owner, fatigue, injuries, wardrobe variant.

Don't accidentally force changes to species or human facial features when requesting human-like story actions. Never write a prompt saying both "3D render" and "no 3D render" for the same shot.

## Asset views

Prefer actual separate files: front, back, side, three_quarter, face_closeup, expressions and pose. A montage reference can still be used, but it is not the same as an isolated camera view. Never guess that a nonstandard dynamic three-quarter side is a perfect orthographic side; ask or annotate uncertainty.

Face close-up shots: face_closeup > three_quarter > front. Back shots: back > three_quarter > front. Object grasping shots benefit from hand/paw pose references. If an image is missing, do not create its path in JSON; issue a warning.

## Anatomy consistency

- A stylized bipedal dog has a canine head and muzzle, raised ears, fur, an expressive tail, and hands that remain visually stylized paws.
- A readable action specifies the active paw, contact point, grip, counterbalance, body orientation and support foot as needed.
- A tail cannot pass through rigid backpacks or pants without narrative/design explanation. If the back of the costume is important, include the back view in reference selection.
- Use ear rotation, tail lift/stillness, head tilt and eye focus to express emotion while preserving face identity.
- Object interaction: specify where the object is before and after a shot; once the right paw takes a phone, maintain that ownership and hand occupancy in contiguous shots.
- If the shot changes an outfit, explicitly name its costume variant and why it changed. A scene without wardrobe change keeps the same variant.

## Prompt example (description only)

"Stylized 3D anthropomorphic canine officer: keep brown fur, tan muzzle, upright pointy ears and fluffy tail, blue uniform with cap and backpack; walks upright to the desk, releases the door handle with right paw, then stops with both feet planted, gazes at the phone. Keep stylized paws instead of human bare hands, no new fingers or extra limbs."

Avoid pretending one textual constraint guarantees a future model's output. V1 only writes and statically validates prompts.
