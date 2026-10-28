# Anime Series Maker · V1 分镜与提示词工作流

**角色设定图 + 剧情需求 → 系列设定 → 剧本 → 文字分镜 → 每镜头视频提示词 / 可选首尾帧提示词。**

目前 Fork 默认采用 **Prompt-only（纯文本交付）**：不调用 Renoise、不调用其他 MCP 或 API，不生图、生视频、配音或剪辑。你可以把生成出来的 Prompt 和参考图复制到任何自己选择的工具。适用于风格化 3D 拟人动物、原创 2D 动漫以及其他画风，不绑定特定角色/IP。

[English](README.md) · [产品 SPEC](docs/SPEC-V1-ANTHRO-STORYBOARD-PROMPT-ONLY.md) · [Skill 重构设计](docs/SKILL-V1-REFACTOR-DESIGN.md)

## 安装

~~~bash
git clone https://github.com/twj515895394/anime-series-maker.git
cd anime-series-maker
git switch codex/anthro-v1-implementation
mkdir -p ~/.codex/skills
cp -R skills/anime-series-maker ~/.codex/skills/
~~~

Windows PowerShell：

~~~powershell
git clone https://github.com/twj515895394/anime-series-maker.git
cd anime-series-maker
git switch codex/anthro-v1-implementation
New-Item -ItemType Directory -Force "$HOME\.codex\skills" | Out-Null
Copy-Item -Recurse ".\skills\anime-series-maker" "$HOME\.codex\skills\"
~~~

Claude Code 可将对应 Skill 目录复制到 ~/.claude/skills/。使用本功能只需要 Python 3；无需 FFmpeg、Pillow、账户或联网视频接口。

## 如何开始创作

向 Agent 说：

> 使用 anime-series-maker 帮我做一个 24 秒 3D 拟人动物短剧。上传的三视图是犬类警员，保留犬耳、口鼻、尾巴和蓝色制服，但以双足直立、手爪持物的方式演绎人类剧情。先完成角色设定，再给 3 个剧情方案，确定后做剧本、分镜、动作衔接和每个镜头的视频提示词。只写文本，不要调用生成模型。

Agent 应将角色图放在用户自己的项目目录，准确记录已有视角和缺失视角。角色特写必须优先调用真实存在的面部参考图；未上传时不能编造文件。每个阶段都要让用户确认。

## 完整离线脚本操作示例

在 skills/anime-series-maker 目录中：

~~~bash
# 准备工作目录。Unix 示例：
mkdir -p my-series/episodes/ep001
cp templates/project.json my-series/project.json
cp templates/series.json my-series/series.json
cp templates/episode.json my-series/episodes/ep001/episode.json
cp templates/shots.json my-series/episodes/ep001/shots.json
cp templates/review.json my-series/episodes/ep001/review.json

# 修改 JSON 中的角色/场景/剧情/镜头及真实参考图路径
python scripts/validate_project.py my-series --episode ep001

# 生成每镜头视频/可选帧提示词和 prompt-manifest.json
python scripts/build_prompt.py my-series/series.json my-series/episodes/ep001/episode.json --shots my-series/episodes/ep001/shots.json

# 未审批时，明确导出 DRAFT 文本包
python scripts/export_prompt_pack.py my-series/episodes/ep001 --draft

# 人工确认每个产物后，逐阶段记录带内容哈希的审批（勿自行只改 status 字段）
python scripts/review_artifact.py my-series/episodes/ep001 --artifact series
python scripts/review_artifact.py my-series/episodes/ep001 --artifact episode
python scripts/review_artifact.py my-series/episodes/ep001 --artifact shots
python scripts/review_artifact.py my-series/episodes/ep001 --artifact prompts
python scripts/export_prompt_pack.py my-series/episodes/ep001
~~~

注意：模板含演示用的**文字角色设定**，不包含也不伪造任何角色图片；要使用参考图必须填入实际存在的 asset_id/path。模板可在没有图片时生成 Prompt，但会报告 NO_REFERENCE_ASSETS 警告。

输出包含 shot-list.md、prompt-pack.md、continuity-report.md、prompts/*.md 和 prompt-manifest.json。所有输出只是文字准备资产，**不是视频文件**。修改了任何系列、单集或镜头源文件，都需要重新编译提示词并重新审批受影响的产物；正式导出会校验源文件和审批哈希，阻止过期包发布。

## 测试

~~~bash
python -m unittest discover -s skills/anime-series-maker/tests -v
~~~

用例覆盖：基础 Prompt 编译、参考图选择、缺失图片、路径安全、时轴与动作连续性冲突、审批和陈旧文件拦截、2D 风格兼容。

## 当前边界与演进

- V1：仅结构化剧本、文字分镜、动作状态、Prompt 编译和本地审核导出。
- 后续：更细的审核版本链、可视化资产管理。
- 更后续：根据实际需求再接 ComfyUI/API/MCP；目前**完全没有必要选择生成后端**。

原上游保留的 assemble.py 和 cover_check.py 是历史媒体处理工具，不属于 V1 主工作流。任何依赖 Renoise 的旧教程与接口都不再适用于默认 Skill。

## 版权与使用

若使用已有作品中可识别的角色进行二创，外观拟人化或提示词省略名字并不等同于获得授权。公开发布/商业使用前请自行核查相关权利和平台规则。

License: MIT（继承仓库原许可证）。
