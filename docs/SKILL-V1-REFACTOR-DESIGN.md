# Anime Series Maker — Skill V1 重构设计（Prompt-only）

> 状态：设计基线 / 尚未实施  
> 版本：V1.0  
> 日期：2026-10-28  
> 适用 Fork：twj515895394/anime-series-maker  
> 对应需求文档：[SPEC-V1-ANTHRO-STORYBOARD-PROMPT-ONLY.md](./SPEC-V1-ANTHRO-STORYBOARD-PROMPT-ONLY.md)

## 0. 决策摘要

原项目主要解决“固定角色 2D 短剧 → Renoise 生成视频片段 → QA → FFmpeg 合成”。本 Fork 的 V1 必须把它重构成“可审查的角色设定 → 剧情 → 剧本 → 分镜 → 动作连续性 → **模型中立、可复制的生图/生视频提示词**”。

V1 不调用 Renoise MCP，不接其他 MCP、ComfyUI 或 API，也不实际生成图像、视频、音频。生成后端留给未来版本，当前不必为一个未选定的供应商实现模拟接口。系统的真实交付物是本地可读的 Markdown、JSON 和 Prompt 文本。

不把功能专门写死成某个既有动画 IP：以风格化 3D 双足拟人犬类角色作为主要测试案例，同时兼容 2D、其他动物拟人和原创卡通角色。

## 1. 当前源码诊断与改造清单

基于 Fork 的 main 分支检查结果，关键文件与上游一致。

| 当前文件 | 实际职责 | 存在问题 | 改造决定 |
|---|---|---|---|
| skills/anime-series-maker/SKILL.md | 0–10 阶段创作/生成指导 | 将账余额、Renoise、生成、成片制作作为主流程 | **重写**为纯创作阶段 S0–S6 |
| templates/series.json | 角色、声线、风格、参考图 | 默认强制 2D 画风；引用绑定 material；塞有 model/resolution | **重建** series v1 模型 |
| templates/episode.json | 一集的 clips/shots | 创作镜头与云端视频 clip 混合；默认 15 秒 | **拆成** episode.json 与 shots.json |
| scripts/build_prompt.py | 验证 + 拼 Prompt + tasks.json | 强校验 material:数字；写 Renoise tasks 结构 | **重构**为中性镜头 Prompt 编译器 |
| references/prompt-framework.md | 原 Prompt 模板 | 角色引用、2D clamp、音频、clip 耦合 | **重写**多媒介/镜头级规范 |
| references/style-presets.md | 2D、Live Action 风格 | 缺风格化 3D 和拟人角色 | **扩展**预设 |
| references/hooks.md | Instagram 爆点、封面、文案经验 | 默认故事节奏容易过度绑定短喜剧 | **保留作可选策略** |
| references/pitfalls.md | 视频生成及后期踩坑经验 | Prompt 风险与具体平台编码问题混合 | **分离**到创作与 legacy 经验 |
| scripts/assemble.py | ffmpeg 合片、音频与接缝检查 | 已不属于 V1 主线 | **保留但不调用** |
| scripts/cover_check.py | Pillow 预览 IG 封面裁切 | 已不属于 V1 主线 | **保留但不调用** |
| README.md / README.zh-CN.md | 安装和使用说明 | 依赖 Renoise 说明成为默认入口 | **新增** Prompt-only 快速开始 |

### 1.1 具体耦合点与处理方式

1. 原 build_prompt.py 在 validate() 中要求每个角色拥有 material:[1-9]数字，并要求角色 look 至少 120 字符；应改为按 schema 验证真实 asset_id、路径和可描述的设计特征。外观详尽程度作为警告和人工审核，而不单独以字数判定。
2. 原 build_clip() 生成 @material:id 映射；V1 使用相对路径 + 角色 ID + 参考资产类型，绝不强制任何模型平台引用语法。
3. 原 tasks.json 含 audioGeneration=true、references.role=reference_image、idempotencyKey、model、resolution 等 Renoise 任务字段。V1 改写成仅描述产物/引用的 prompt-manifest.json；不含远程执行指令。
4. 原 series.style 默认英文写有 hand-drawn 2D / no 3D render。改为依赖 visual_style.medium 选择 2D、stylized_3d、realistic 等对应模板，媒介禁令不能跨类型串用。
5. 原 max_clip_seconds 和 clips[].duration 是生成模型任务约束。V1 以故事时间轴和镜头为单位，单镜头时长可以建议但不由 Renoise 上限决定。
6. 原 SKILL.md 要求 get_account、model-routing、list_models、estimate_cost、create_tasks、wait_tasks、download_results、analyze_media；V1 将这些调用完整移出依赖清单。
7. 原“每集 1–6 clips、每镜头 2–3 秒、优先日语、Instagram 钩子”改成可选预设，不作为全局硬规则。

## 2. 目标架构

    用户剧情需求 + 用户本地角色资产
                    |
                    v
       SKILL.md 规划、提问与审核
                    |
                    v
      project.json / series.json
      episode.json / shots.json
                    |
            references 规范库
                    |
                    v
        validate_project.py
                    |
                    v
         build_prompt.py
                    |
                    v
       export_prompt_pack.py
                    |
          +---------+----------+
          |                    |
     结构化 JSON          可复制 Markdown
     prompt-manifest      shot-list / prompts
     review / diagnostics continuity-report
          |
          v
     用户自行使用任意生成工具（V1 之外）

系统将“创作决策”“确定性校验”“提示词编译”“人工交付”解耦。单集设定文件是源数据，不允许 Agent 直接手工修改已审批的最终 Prompt 却不更新来源。

## 3. Skill 触发与阶段交互设计

### 3.1 Frontmatter

名称沿用 anime-series-maker，避免现有安装路径和召回关键词失效。description 改为“角色驱动的连续短剧规划、结构化分镜、可移植图像/视频 Prompt”，支持 3D 拟人、2D 动漫及其他受控风格。明确输出为 Prompt-only，不调用生成或计费服务。

触发词覆盖：动漫短片、番剧、下一集、连续剧、角色一致性、拟人化角色、3D 动画、剧情短剧、剧本、分镜、镜头、视频提示词。仅需要分镜/Prompt 的用户，允许载入既有 series + episode 后从中间阶段开始。

### 3.2 目标阶段 S0–S6

| 阶段 | 输入 | 必须输出 | 审核规则 |
|---|---|---|---|
| S0 Setup | 项目目录和已有文件 | project.json、文件清单 | 不要求联网 |
| S1 Series Bible | 人物参考图、身份、体态、画风、场景 | series.json + asset 清单 | 角色图方向与外观须确认 |
| S2 Premise | 故事要求、既有世界观 | 三案+推荐+大纲 | 确认选题 |
| S3 Screenplay | 选定选题、角色关系 | episode.json：节拍/对白/场景 | 确认剧本 |
| S4 Storyboard | 剧本和人物初始状态 | shots.json+可读镜头表 | 确认时间与动作 |
| S5 Prompt compiler | 已批准的分镜和角色设定 | 镜头 Prompt + manifest | 校验并确认 |
| S6 Export | 有效 Prompt 集 | prompt-pack.md、shot-list.md、诊断报告、审核记录 | 只导出文本 |

默认每个主要阶段需要明确用户审批；若用户要求跳过某阶段，记录跳过理由和来源版本。禁止因 Agent 认为“可以”就擅自调整前面被用户确定的剧情、台词或角色设计。

### 3.3 审核与修改传播

为每份阶段产物记录 artifact_id、revision、hash、status、dependencies。状态集：draft、needs_review、approved、stale、rejected。

- series 外观变化 → 标记依赖的 Prompt stale；是否需要重审剧本视具体变更而定。
- episode 剧情变化 → 标记 shots/Prompt/export stale。
- shots 时序/姿势/镜头变化 → 标记 Prompt/export stale。
- 仅调整 Prompt 文案表述 → 不强制重写已审批剧情，但需重审该 Prompt。
- 断点恢复先读取 review.json 和文件版本，不凭聊天历史推测审批结果。

V1 可由 Skill + 本地 JSON 实现轻量状态管理，不需要新建后端服务。

## 4. 数据合同与文件组织

建议目录：

    skills/anime-series-maker/
      SKILL.md
      references/
        prompt-framework.md       # 改造
        style-presets.md          # 扩展
        hooks.md                  # 可选保留
        pitfalls.md               # 精简分类
        anthro-character.md       # 新建
        storyboard.md             # 新建
        action-continuity.md      # 新建
        prompt-portability.md     # 新建
      templates/
        project.json              # 新建
        series.json               # 升级
        episode.json              # 升级
        shots.json                # 新建
        review.json               # 新建
      schemas/
        project.v1.schema.json
        series.v1.schema.json
        episode.v1.schema.json
        shots.v1.schema.json
        prompt-manifest.v1.schema.json
      scripts/
        validate_project.py       # 新建
        build_prompt.py           # 改造
        export_prompt_pack.py     # 新建
        assemble.py               # 保留/legacy
        cover_check.py            # 保留/legacy
      tests/
        fixtures/
        test_validation.py
        test_prompt_compile.py
        test_exports.py

### 4.1 关键字段职责

- **project.json**：项目 ID、默认语言、根路径、workflow_mode=prompt_only、激活的系列 ID、文件版本。
- **series.json**：系列 ID、视觉媒介、风格、角色身份锁定、参考图和场景；是角色唯一事实源。
- **episode.json**：剧情前提、题材、节拍、场景、对白、开始/结束世界状态；不定义平台任务。
- **shots.json**：镜头 ID、时间轴、场景/角色 ID、动作阶段、景别、摄影机、入出状态、参考图、镜头间衔接。
- **review.json**：审批人确认内容、状态、hash、依赖和失效记录。
- **prompt-manifest.json**：shot_id、prompt_type、prompt_path、reference_asset_ids、时长、画幅、输入修订号和编译版本。

素材采用 asset_id + 相对路径，不能出现“存在一个没提供的 face.png”的隐式假设。可选的原始拼接三视图记录 montage 及方位标注；用户未提供单独切图时不得声称已裁切完成。

### 4.2 Legacy 迁移规则

为旧 series/episode 模板保留只读副本到 templates/legacy，避免已使用原版的用户丢失参考。

- 旧 series.series → 新 series.title；series.style → visual_style.description。
- 旧 characters[].sheet、material → reference_assets 的来源信息；material 只存 legacy_metadata，不进入新 Prompt。
- 旧 episode.clips[].shots[] → 按 clips 累计时长展平为全局 shots 时间轴。
- 旧 settings 的整数下标 → 稳定 location_id；cast 角色 ID 继承。
- 旧 voice 文本保留为 voice_description（不代表已经配音）。
- model/resolution/max_clip_seconds → legacy_metadata，而非通用 series 约束。
- 无法判断的镜头动作状态、参考图方位与 hand-off 标为待确认，不自作主张自动填充。

旧数据没有 schema_version 时识别为 v0，先备份再迁移。实施迁移脚本可排 P1；P0 可以先支持全新 v1 模板。

## 5. 3D 拟人化角色规则

### 5.1 身份、动作与状态分层

- **identity_lock（身份不变）**：物种头部、口鼻、耳朵、尾巴、毛色/花纹、眼睛、躯干比例、衣服版型、背包、鞋、重要徽章。
- **performance_profile（动作能力）**：双足直立、关节与手爪能力、行走、奔跑、坐下、拾物、开门、双人互动、耳尾表演、表情与口型。
- **shot_state（镜头状态）**：位置、朝向、重心、左右手状态、持物者、视线、表情、情绪、受伤或疲劳、服装变化。

约束强度区分 hard（同一造型不能变的人物识别特征）、preferred（推荐姿势）、situational（受情节影响的换装/污损）。禁止简单地写“全场所有服装永不改变”，而应通过版本和状态记录让正常剧情换装成为可能。

### 5.2 参考图优先级

- 面部特写：face_closeup → three_quarter → front；缺失时警告。
- 背面/尾巴镜头：back → three_quarter → montage 中已确认的背面子视图。
- 侧面口鼻/动作：side → three_quarter；缺失时警告。
- 手爪拿物、双人接触：pose/hand_detail，若无则提示需人工 QA。
- 正面全身动作：front，并附当前场景/动作构图。

用户上传的示例具有正面、背面和偏侧动态姿态；不应该未经确认将其写成“标准正侧背 + 面部特写齐备”。用户新补充的独立面部特写应成为脸部镜头首选身份资产。

### 5.3 动作规划层

一个复杂动作拆为：意图 → 准备/起势 → 位移 → 接触/受力 → 回收/反应 → 结束姿态。要记录支撑腿、躯干朝向、肢体接触对象、道具所有权、衣服尾巴交互、速度与体力消耗。打斗/追逐可以支持，但不得依赖单一 15 秒长 Prompt 精确完成所有复杂动作。

对话镜头和简单情绪镜头允许较短动作说明；不是每个镜头都必须产生多张关键帧。困难的握持、碰撞、双人接触优先建议额外 first/last/keyframe 的文字提示词。

## 6. 分镜数据与镜头连续性

每一镜头至少包含：shot_id、scene_id、start_s/end_s、cast、framing、camera、action.goal、action.beats、continuity_in/out、transition_to_next、reference IDs 和 dialogue_refs。

镜头分类可为 dialogue、reaction、action、establishing、transition；根据镜头类型调整检查规则。可用“单镜头一个明确的动作目标”作为默认建议，但不强制 2–3 秒一镜头。

连续性验证重点：

1. 同一连续场景的人物位置和走向合理；越轴或反打需有清晰说明。
2. 左右手持有的物品不能无事件突然交换。
3. 人物有意转身、起身、坐下、接触或脱离应显式体现动作过程。
4. 套装、帽子、背包、尾巴状态在同一时间线上有据可依。
5. 受击、奔跑后的疲劳、喘息、步态和反应按情节承接。
6. first_frame 与入场状态、last_frame 与出场状态一致。
7. hard_cut 不等于可以忽略叙事与道具连续性；有意省略需声明。

静态验证只证明结构化状态自洽，不能声称生成画面中的肢体和面容已经正确。

## 7. 提示词编译设计

### 7.1 输出单位

优先按 shot 编译，而不是按某个平台的 clip 编译。单个镜头可有：

- shot001.video.md：完整版视频提示词和精简版可选。
- shot001.first-frame.md：可选首帧图片提示词。
- shot001.last-frame.md：可选尾帧图片提示词。
- shot001.keyframe-01.md：可选中间关键动作图片提示词。

用户不需要生成所有帧时，禁止自动要求必须编写所有图片 Prompt。Prompt 是文本而非实际图片。

### 7.2 生成文本的逻辑顺序

    SHOT INTENT       本镜头唯一的核心目标
    REFERENCE MAP     角色、场景资产的 ID 与可读相对路径
    CHARACTER LOCK    物种头脸、毛色、服装、耳尾、道具身份
    STYLE             2D/3D、材质、光线、影调、清晰度目标
    SETTING           场景布局和固定元素
    START STATE       角色入镜的姿势/位置/手部/道具/目光
    ACTION BEATS      连续动作阶段与表现节奏
    CAMERA            景别、视角、镜头运动、人物画面位置
    EXPRESSION        表情、耳尾、眼神、情绪和语音描述
    DIALOGUE / SFX    可选；不触发配音服务
    END STATE         最终姿态、动作结果和衔接方式
    NEGATIVE          关键漂移/人体结构/风格排除项

编译器根据源字段自动组合每镜都需要的身份块。角色称谓、身份和引用路径的来源只能是 series 与 asset-manifest；不允许 Agent 每镜重新自由改写人物辨识特征。

同一输入内容与编译器版本必须尽可能输出确定性文件名与字段顺序，并记录 source_hashes、compiler_version、source_revision。

### 7.3 验证器分级

- **L0 文件与 Schema**：JSON/UTF-8/版本/文件存在性。
- **L1 引用完整性**：角色、地点、资产和镜头 ID 可解析。
- **L2 时轴**：正数时长、连续场景的时间结构、目标时长。
- **L3 连续性**：结构化道具归属、手爪状态、人物位置、服装。
- **L4 Prompt 完整性**：镜头目标、参考映射、风格、动作、起止状态、无遗留占位符。
- **L5 人工创意 QA**：剧情可信度、动作负载、镜头可生成性，属于审查意见，不伪装成程序确定性判断。

ERROR 直接阻断“final”导出，WARN 需要明确展示给用户，可标注“确认接受”后继续。

错误建议包含 severity、code、artifact、shot_id、field、message、suggestion，输出机器可读 JSON 和 Markdown 报告。必须能指出错误在哪一镜、哪一字段，而不是只有“提示词质量不佳”。

### 7.4 CLI 目标

    python scripts/validate_project.py my-series/
    python scripts/build_prompt.py my-series/series.json my-series/episodes/ep001/episode.json --shots my-series/episodes/ep001/shots.json --out my-series/episodes/ep001/prompts
    python scripts/export_prompt_pack.py my-series/episodes/ep001/ --out my-series/episodes/ep001/export

以上均为后续实施目标接口，**并非当前仓库已经实现**。建议 0 成功、1 校验失败、2 文件/参数错误。Windows/macOS/Linux 均须可运行，Prompt-only 的核心依赖仅为本地 Python 与文本文件。

## 8. V1 对外边界与未来模型适配

必须先有稳定的 prompt-manifest.json，未来 ComfyUI、自定义 API 或其他平台才有明确的消费接口。

示意请求结构（只描述数据，不会在 V1 中发送）：

    {
      "shot_id": "sh001",
      "prompt_file": "prompts/shot001.video.md",
      "duration_s": 4,
      "aspect_ratio": "16:9",
      "references": [
        {"asset_id": "a_front",
         "path": "assets/characters/dog_officer_a/front.png"}
      ]
    }

未来适配器可转换平台专有参数（参考图格式、最多时长、分辨率、音频开关、估价、任务状态）。生成后端不得反向成为 series/episode 核心 Schema 的强制依赖。

V1 既不实现这些适配器，也不写伪代码冒充完成了 API 集成。

## 9. 测试矩阵

| 编号 | 测试 | 期待结果 |
|---|---|---|
| T01 | 单角色 24 秒短剧 | 3 案→剧本→分镜→可复制 Prompt |
| T02 | 双角色多角度/特写 | 正确引用人物 ID，近景优先面部参考 |
| T03 | 拟人犬类开门、拿手机 | 物种/服装不漂移；手部/道具/尾巴状态可追溯 |
| T04 | 追逐、停步、喘息 | 运动方向、体力/情绪与镜头承接 |
| T05 | 缺 face_closeup | 给出提示，不伪造图片或路径 |
| T06 | 时间重叠、空洞、错误角色 ID | 有定位明确的结构化错误 |
| T07 | 右手物品无故转左手 | 连续性错误或明确审查警告 |
| T08 | 修改系列服装后重编译 | 依赖 Prompt 标记 stale 并更新 |
| T09 | 2D 原创短剧回归 | 不强制 3D 拟人画风 |
| T10 | 无网络、无 MCP/FFmpeg | 仍能完整导出文字分镜/Prompt |
| T11 | 重新进入已审核的单集 | 读取 review.json，保留修订与批准状态 |
| T12 | 既有 IP 二创案例 | 提示相关权利/平台风险，不提供绕过内容审核方案 |

## 10. 实施顺序和验收门槛

**P0 必须完成：**

1. 锁定本文与 SPEC 为实现基线。
2. 编写 v1 schema + 样例 fixture；定义稳定 IDs。
3. 改写 SKILL.md，仅规划文本创作和人工审核。
4. 增加拟人化角色、动作、连续性 reference 规则。
5. 重构 Prompt 编译器；增加基本结构/时间/引用校验。
6. 增加离线 Prompt 包导出；文档标清“待生成”。
7. 跑通 20–30 秒拟人化犬类场景和 2D 原创场景回归。

**P1 质量提升：**

- review.json 的 hash/revision 与自动失效链。
- 完整连续性报告，包括道具、四肢、体力与镜头方向。
- full/compact 双 Prompt 视图与镜头表导出。
- v0 到 v1 的迁移脚本及 legacy 文档。
- README 中补充“无 API 使用方法”和 Windows 测试示例。

**推迟到 V2/V3：**自动生成首尾帧/视频、ComfyUI/API/MCP、实际媒体 QA、费用估算、视频后期、发布、图形界面、多用户运行环境。

V1 DoD：零外部生成依赖、角色/故事/镜头结构一致、完整文本产物、镜头与参考资产一一可追踪、错误能阻断最终导出、用户能独立复制到任意模型、同时覆盖 3D 拟人和 2D 测试；不把任何文本包标为“已生成视频”。

## 11. 风险与决策记录（ADR）

| 决策 | 理由 | 需要防范 |
|---|---|---|
| V1 Prompt-only | 优先解决剧本与分镜质量 | 不能以静态校验代替视觉 QA |
| 拆分 episode 与 shots | 消除片段模型限制对镜头的绑架 | 旧数据必须有迁移路径 |
| 角色 identity_lock 为事实源 | 一致性强于逐镜自由描述 | 初始信息缺失必须向用户说明 |
| asset_id + 相对路径 | 平台无关 | 未来平台适配转换需要独立实现 |
| 3D 拟人是可选预设 | 既能覆盖示例也不损失原 2D 用途 | 提示词风格块必须隔离 |
| 显式连续性 + review.json | 支持增量修改和跨会话恢复 | 简单静态模型不代表动作物理准确 |
| 保留 assemble/cover_check | 不损失上游工程资产 | V1 主流程不能隐式调用 |
| 公开二创增加合规提示 | 改造角色仍可能存在权利问题 | 不等于因为描述外观就获得授权 |

## 12. 开发分支与交接

本次只在 codex/anthro-v1-spec 分支新增 docs/ 下两份设计文档；不编辑现有 SKILL.md、模板或脚本，不创建 PR。后续代码改造建议按 schema → validator → compiler → Skill/reference → export/tests/README 的顺序小步提交，每个阶段记录已实现与待实现项目。

**本文件是整改设计，不是代码已实施说明。所有新增脚本、字段和 CLI 均属于未来实现目标。**
