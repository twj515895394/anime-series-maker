# Style presets · 可选画风（V1 Prompt-only）

Choose exactly one primary medium/style for a series; store it in visual_style. These are starting points, not model performance guarantees.

## Stylized 3D anthropomorphic animation (recommended for user example)

Medium: stylized_3d
Description: High-quality stylized 3D animated feature look, expressive character acting, soft detailed fur, appealing facial proportions, physically coherent costumes, saturated but balanced colors, soft global illumination, clean cinematic blocking. Preserve recognizable animal muzzle, ears, fur and tail while allowing upright human-like movement. All shots preserve the same character model and costume details.
Negative style: photorealistic human face; unintended 2D cel rendering; rubbery extra limbs; missing animal features.

## 3D toy-like/cartoon

Medium: stylized_3d
Description: Clear 3D cartoon modeling, clean silhouettes, smooth stylized materials, bright family-friendly lighting and readable poses, consistent character proportions and wardrobe.
Negative style: lifelike human skin; deformed paws; excessive realism.

## Soft watercolor 2D

Medium: 2d_anime
Description: 2D Japanese anime, gentle watercolor backgrounds, thin clean linework, soft cel shading, restrained bloom, expressive anime facial acting, consistent character designs. All backgrounds remain hand-painted 2D.
Negative style: photoreal backgrounds; 3D character rendering.

## Flat cel 2D

Medium: 2d_anime
Description: Flat two-tone 2D cel-shaded animation, clear uniform outlines, simple stylized faces, bright limited palette, readable silhouettes and fluid key poses.
Negative style: photoreal human skin; 3D render look.

## Cinematic stylized drama

Medium: stylized_3d
Description: Stylized cinematic 3D character animation, deep yet soft shadows, textured surroundings, natural directional light, restrained grading, physically grounded poses and camera movement.
Negative style: hyper-real human features; visual identity drift.

## Live action (optional)

Medium: live_action
Description: Photographed actors, natural physical behavior, coherent cinematography and lighting; do not impose animal-animation appearance unless the user deliberately requests a creature/puppet treatment.
Negative style: anime cel render; cartoon lineart.

Do not paste old "EVERYTHING ... hand-drawn 2D ... no 3D render" into stylized_3d series.
