# Anime Series Maker V1 SPEC：角色驱动的分镜与提示词生产

> 状态：设计基线 / 待实现  
> 版本：V1.0（Prompt-only）  
> 日期：2026-10-28  
> 适用仓库：`twj515895394/anime-series-maker`  
> 配套技术设计：[SKILL-V1-REFACTOR-DESIGN.md](./SKILL-V1-REFACTOR-DESIGN.md)

## 1. 背景与产品定位

原项目服务于“固定角色 + 剧情构思 + 2D 动漫片段生成 + 视频拼接”的端到端短剧创作，核心生成能力绑定 Renoise MCP。Fork 的 V1 目标**不是换一个视频供应商**，而是先将其重构为**模型无关、生成执行无关、可复用的创作规划 Skill**。

输入一组角色图、角色设定及一句或一段剧情需求；输出可审核的系列设定、剧情方案、剧本、文字分镜、动作状态、图像参考帧提示词（可选）和镜头级视频提示词，用户之后自行选择任何生成工具执行。

主要示例：使用上传的“风格化 3D 双足拟人犬类警员”三视图制作具有较多人类行为和互动的短剧。**示例仅用于设计数据合同，不把产品绑定到特定角色/IP，也不将图片上传进仓库。**

### 1.1 V1 必须达到的结果

1. 按系列复用角色身份、外观、服装、声线、世界观、画风；支持多个角色与同一角色的不同服装/状态版本。
2. 从剧情意图生成三案候选，用户选择后形成完整剧情节拍、剧本、镜头分解和逐镜头交付物。
3. 同时支持“剧情型分镜”（人物关系、冲突、反转、对白）和“动作型分镜”（起点、接触、动作阶段、终点、惯性/疲劳、道具转移）。
4. 默认输出文本分镜；首帧、尾帧和关键帧只**编写生图提示词**，不生成图片。
5. 根据参考图元数据给出人物与机位的映射；不强制模型厂商专用的 `material:<id>`。
6. 用确定性程序校验结构、时间轴、引用有效性、连续性字段、必需产物和占位符。
7. 导出跨模型可复制的提示词与机器可读清单；即使没有网络、账户、积分、FFmpeg、ComfyUI，仍能完成 V1 全流程。
8. 每个可审核阶段有产物状态，用户修改上游内容时明确标出需要重新生成的下游文本产物。

### 1.2 明确不做（硬边界）

- 不发起图像、视频、配音任务；不接 Renoise MCP / ComfyUI / 第三方 API；不查询余额、不估价、不调度任务。
- 不下载视频、不自动剪辑、不导出真实 MP4、不制作真实封面；仅可提供封面构图文案或封面提示词。
- 不承诺提示词让模型“绝对一致”或能自动解决所有复杂动作。
- 不做图像自动识别、自动标注三视图的方位，无法可靠判断时必须由用户确认。
- 不把生成式图片或截图直接写入仓库；用户提供的角色图在用户工作目录中引用。
- 不自动发布、抓取平台数据；`episodes.json` 如存在仅作为人工录入的历史参考。
- 不将特定受版权保护角色名、标志或“绕过审核”的措辞写成通用提示词规则；公开发布与商业化需确认相关权利与平台要求。

### 1.3 目标用户与使用模式

- **原创/二创短剧创作者**：上传角色图 + 简述剧情，交互式拿到分镜及可复制 Prompt。
- **已有素材的创作人员**：跳过角色图生成阶段，导入既有三视图/面部特写/场景资产。
- **多模型使用者**：输出中性规范 Prompt，用户自行复制到不同的视频或图片生成环境。
- **已有剧情/分镜的团队**：直接从指定阶段进入，只更新必要的下游产物。

## 2. 产品工作流（人工审核关口）

| 阶段 | 输入 | 输出 | 必须审核 |
|---|---|---|---|
| S0 项目初始化 | 用户需求、创作模式 | `project.json`、项目目录 | 否 |
| S1 系列圣经 | 角色图、身份/体态、画风、世界观 | `series.json`、资产清单 | **是**，尤其三视图映射 |
| S2 故事构思 | 主题、长度、风格、已有剧集 | 三个候选 premise、推荐理由、剧情大纲 | **是** |
| S3 剧本与节拍 | 选定 premise、系列圣经 | `episode.json` 的剧情节拍、台词、场景 | **是** |
| S4 分镜与动作 | 剧本、角色/场景状态 | `shots.json`、文字分镜表、连续性链 | **是** |
| S5 提示词编译 | 已通过的系列/单集/分镜 | `prompts/*.md`、`prompt-manifest.json` | **是** |
| S6 导出与归档 | 校验通过的文本产物 | `export/shot-list.md`、`export/prompt-pack.md`、`review.json` | 否 |

**关键原则：**阶段推进由明确产物及审核标记决定，不因 Agent 说“完成”就自动跨过审核。V1 可由 Agent 对话引导并将审核记录写入本地文件；不要求实现常驻服务或 UI 状态机。

### 2.1 首轮信息收集

一次集中询问缺失的关键项：作品类型（独立/连续）、角色资产是否齐全、3D/2D/写实风格、片长区间、画幅、对白语言、剧情题材、目标动作复杂度。优先沿用已存在的系列配置，禁止每集重复询问同一设定。信息不足时用清晰标记的默认值或待确认项，禁止伪造参考图细节。

### 2.2 审批策略

- S1/S2/S3/S4/S5 的批准对象分别绑定 `artifact_id + revision + content_hash`。
- 编辑 S1（角色样式）会使依赖它的剧本/分镜/提示词标记为 `stale`，但允许用户明确选择仅重编译 Prompt。
- 编辑 S4（分镜动作/时序）只使 S5/S6 的导出失效；剧情级内容不必全部重写。
- 用户可选择“自动按既定约束继续”，但不能在用户没有要求时声称最终成片已生成。

## 3. 核心内容模型

### 3.1 角色：身份锁定 ≠ 动作能力

角色需要两套正交约束：

1. **identity_lock**：头部物种、口鼻、耳朵、毛色、体型、服装、标志、配件、尾巴、眼睛、手脚样式；包含必保留项与禁止漂移项。
2. **performance_profile**：直立/四足、关节活动范围、抓握方式、走跑坐卧、耳朵尾巴情绪表达、表情范围、嘴型、语音/台词限制；允许动作而不改变外观物种。

默认采用风格化 3D 角色时：保留犬类头脸及毛发，躯干双足直立且可以完成较多人类动作；禁止突然变成人脸、人类裸露手掌或多余肢体。**手掌抓握能否准确生成仍要由使用者后续验证。**

### 3.2 角色参考资产分类

| 类型 | 作用 | V1 要求 |
|---|---|---|
| `front` | 正面比例、服装主细节 | 推荐 |
| `back` | 背包、尾巴、服装背面 | 可选 |
| `side` | 口鼻深度、耳朵、足部体态 | 可选 |
| `three_quarter` | 立体转向与常用构图 | 可选 |
| `face_closeup` | 所有脸部近景优先引用 | 强烈建议 |
| `expressions` | 常用情绪、张嘴/闭嘴等 | 可选 |
| `pose` | 复杂身体动作示范 | 可选 |
| `outfit_variant` | 换装与剧情状态 | 按需 |

若上传的是拼接三视图，记录 `asset_type=montage` 和子视图的裁切标识；可输出裁切建议，但不声称已完成裁切或看到不存在的角度。镜头的 `face_closeup` 优先级高于全身远景参考；全身镜头则优先对应视角参考。

### 3.3 世界观与连续性

系列层记录地点库、光照基调、角色关系与口头禅、长期剧情状态；单集层记录剧情前提、时间地点、角色服装/受伤/疲劳/持有道具等初始状态；镜头层记录明确的入场和出场状态。

连续性最低字段：`actor_id`、`position`、`orientation`、`pose`、`left_hand`、`right_hand`、`prop_owner`、`expression`、`gaze`、`outfit_id`、`tail_state`（对有尾巴角色）以及 `scene_id`。无关字段可省略，但涉及手持物品、接触或动作承接时不得缺少关键字段。

**剪辑规则：**同一动作跨镜头时应明确连续动作或动作终点；有意跳切需用 `transition=hard_cut` 并描述状态变化，不能把“硬切”误当作姿态逻辑豁免。

## 4. 数据与目录规范

```text
my-series/
  project.json
  series.json
  assets/
    characters/<character_id>/{front,back,side,face,poses}...
    scenes/<scene_id>/...
  episodes.json                  # 可选的历史索引
  episodes/ep001/
    episode.json                 # 故事节拍、剧本、场景及对白
    shots.json                   # 镜头、时间、动作、机位及连续性
    review.json                  # 产物版本及审核状态
    prompts/
      shot001.image.md           # 可选的首/尾/关键帧提示词
      shot001.video.md           # 镜头级视频提示词
      shot002.video.md
    prompt-manifest.json
    export/
      shot-list.md
      prompt-pack.md
      continuity-report.md
```

所有路径均相对项目根目录，使用 UTF-8 编码；角色 ID、场景 ID、镜头 ID 稳定且不能重用。视频镜头的时间单位统一为秒（数值型），内部数据不得以字符串“3s”代替数值。

### 4.1 最小系列数据样例（`series.json`）

```json
{
  "schema_version": "1.0",
  "series_id": "anthro-police-demo",
  "title": "拟人警员短剧示例",
  "visual_style": {
    "medium": "stylized_3d",
    "rendering": "family-friendly stylized 3D animated feature look",
    "aspect_ratio": "16:9",
    "negative_style": ["photorealistic human face", "2D cel-only look"]
  },
  "language": "zh-CN",
  "characters": [{
    "id": "dog_officer_a",
    "species": "canine",
    "form": "anthropomorphic_biped",
    "reference_assets": [
      {"asset_id": "a_front", "type": "front", "path": "assets/characters/dog_officer_a/front.png"},
      {"asset_id": "a_face", "type": "face_closeup", "path": "assets/characters/dog_officer_a/face.png"}
    ],
    "identity_lock": {
      "must_keep": [
        "brown fur and tan muzzle",
        "pointed canine ears and fluffy tail",
        "blue uniform, cap and boots"
      ],
      "must_avoid": ["human facial replacement", "extra fingers or limbs", "missing ears or tail"]
    },
    "performance_profile": {
      "locomotion": "upright_bipedal",
      "hand_type": "stylized_paws",
      "object_grasping": "allowed_with_pose_reference",
      "emotional_features": ["ears", "tail", "eyes", "muzzle"]
    }
  }],
  "locations": [],
  "series_continuity": {}
}
```

说明：这里使用描述性英文以便跨模型复用，角色图须是用户持有的工作目录内真实文件，缺少的 `face_closeup` 应标为待补充，而不是自动编造。上例是**新提议 Schema**，不是现有脚本已经支持的 Schema。

### 4.2 单集与镜头最小合同

```json
{
  "schema_version": "1.0",
  "episode_id": "ep001",
  "series_id": "anthro-police-demo",
  "target_duration_s": 24,
  "premise": "警员接到一条令人意外的消息",
  "beats": [
    {"id": "b1", "purpose": "建立场景"},
    {"id": "b2", "purpose": "意外出现"},
    {"id": "b3", "purpose": "人物反应"}
  ],
  "scenes": [{"id": "sc01", "location_id": "office", "cast": ["dog_officer_a"]}]
}
```

```json
{
  "schema_version": "1.0",
  "episode_id": "ep001",
  "shots": [{
    "shot_id": "sh001",
    "scene_id": "sc01",
    "time": {"start_s": 0, "end_s": 4},
    "cast": ["dog_officer_a"],
    "framing": "medium shot",
    "camera": {"angle": "eye_level", "motion": "slow_push_in"},
    "action": {
      "goal": "走到办公桌前停下",
      "beats": ["推开门", "迈步", "在桌前停住"],
      "continuity_in": {"right_hand": "on_door_handle", "prop_owner": {}},
      "continuity_out": {"right_hand": "free", "prop_owner": {}}
    },
    "dialogue": [],
    "sound_cues": [],
    "references": ["a_front"],
    "transition_to_next": "hard_cut",
    "prompt_targets": ["video", "optional_first_frame"]
  }]
}
```

上例用最小字段表示合同，正式实现需补充所有字段的类型、必填条件、枚举值、跨文件引用及迁移规则，并用对应的 JSON Schema 文件提供机器校验。

### 4.3 Prompt 导出清单

`prompt-manifest.json` 最少包含：`schema_version`、`episode_id`、`compiler_version`、`shot_id`、`prompt_type`（`video`/`first_frame`/`last_frame`/`keyframe`）、`path`、`reference_asset_ids`、`duration_s`、`aspect_ratio`、`source_revision`。不出现平台专属的任务 ID、充值积分、`audioGeneration` 或 `material:<id>` 强依赖。

## 5. 文字分镜与提示词交付标准

### 5.1 分镜表必含

镜头编号、时间段/时长、场景、出场人物、景别、视角、机位运动、动作开始状态、动作过程、结束状态、视线/表情、台词、音效、参考图 ID、镜头衔接说明、预计风险点。按用户需要展示适当精简表格，但存储的 `shots.json` 必须完整。

### 5.2 视频 Prompt 组织顺序

1. 任务指令（此镜头的**唯一关键事件**及画面意图）。
2. 角色引用（角色 ID + 图像路径/别名；按景别选择正面/侧面/特写，不包含平台专用引用语法）。
3. 角色锁定（不变的物种、头部、耳尾、服装、体型、道具）。
4. 环境与风格（3D 渲染、材质、光照、色调；不能沿用原 2D 强制块）。
5. 分镜构图、摄影机、动作节拍与运动方向。
6. 入场/出场状态、道具所有权及跨镜头一致性。
7. 台词和声音指导（**仅为后续模型提供说明**；V1 不生成声音）。
8. 负向限制（与角色/风格直接相关，避免空泛堆砌）。
9. 可选的短版 Prompt（适合指令较短的模型）和完整长版 Prompt。

镜头提示词必须**独立可读**，不能依赖上一段对话才能理解；但人物设定和世界观的重复块须由编译器自动复用，避免 Agent 手工逐次粘贴导致漂移。

### 5.3 首帧 / 尾帧 / 关键帧提示词

- **first_frame**：进入镜头时角色位置、四肢姿势、表情、道具、环境、镜头高度和构图。
- **last_frame**：动作结束后的站姿/视线/接触关系，必须与 `continuity_out` 一致。
- **keyframe**：只对复杂动作、遮挡、道具交换、双人接触等添加，不必每镜头都有。
- “角色设定图”和“生成首帧”用途不同：角色设定图锁定身份，首帧负责当前场景构图；不能拿拼接三视图直接当剧情帧。
- 如果镜头是简单对话，允许仅输出视频 Prompt，不强制生产所有帧提示词。

### 5.4 动作与对话控制

- V1 不写死 2–3 秒一个镜头、每片段不得超过 15 秒；镜头与时长由作品节奏决定，生成时长限制留给未来模型适配器。
- 一镜头尽量聚焦一个动作目标；复杂动作拆分为起势→位移/接触→结果，并在状态中记录手脚、道具、视线及方位。
- 台词必须附说话人、情绪和预估语音时长；两人同时说话需显式记录。
- 近景优先使用单独面部参考；手部抓握、尾巴遮挡与服装穿插是风险项，加入人工 QA 提示。
- 多镜头动作衔接须说明“同轴连续”“省略跳切”或“切换场景”，不凭空假设运动完成。

### 5.5 内容自由度

不要将原项目的“15–90 秒、固定 2–3 角色、恋爱喜剧、3 秒必反转、日语默认、Instagram 安全区”写成全局硬规则。它们可作为可选的 `short_comedy` 预设，而非通用基础合同。

## 6. 程序化校验与文本 QA

### 6.1 阻断项（错误）

- JSON 无法解析、版本不兼容、必需字段缺失、镜头 ID 或资产 ID 重复。
- 出场角色/场景/参考资产引用不存在，或要求特写但只映射到不存在的参考图。
- 镜头时间倒序、负时长、时间段非预期重叠/空洞、单集目标时长不吻合（容差 0.05 秒）。
- 动作依赖中的关键道具凭空出现/消失、持有者在相邻连续镜头中无交接说明。
- `first_frame` 与 `continuity_in`、`last_frame` 与 `continuity_out` 在结构化字段上冲突。
- Prompt 为空、残留 `TODO`/`TBD` 等未确认占位符；误注入 `material:<id>` 等默认 Renoise 模板残留。
- 审核状态未通过却尝试标记输出为最终版。

### 6.2 提示项（警告）

- 缺少面部近景参考、缺少对应方位图、对话估时可能超长。
- 单镜头同时包含多重复杂动作、高速肢体/接触/抓握而缺少关键帧提示。
- 长段落剧情与动作节奏不匹配，角色外观文字约束过短。
- 跨场景光照/服装变化没有剧情说明。
- 超过软推荐时长或镜头数量，提醒但不简单拒绝。

### 6.3 校验报告

`export/continuity-report.md` 对每条诊断输出 `severity`、`code`、`shot_id`、`field`、`reason`、`suggested_fix`。错误阻断正式导出；警告允许人工确认并在 `review.json` 留痕。程序 QA 是静态检查，不能声称已经验证视频画面。

## 7. V1 CLI 和离线操作体验（目标接口）

```bash
python scripts/validate_project.py my-series/
python scripts/build_prompt.py my-series/series.json my-series/episodes/ep001/episode.json --shots my-series/episodes/ep001/shots.json --out my-series/episodes/ep001/prompts
python scripts/export_prompt_pack.py my-series/episodes/ep001/ --out my-series/episodes/ep001/export
```

命令属于**拟设计的实现目标，不是当前仓库已具备的参数接口**。CLI 应支持 Windows/Linux/macOS，纯文本编译不依赖外部平台和 GPU；生成工具存在时也不得自动调用。退出码：`0` 成功、`1` 校验失败、`2` 调用/文件错误。

## 8. 验收与测试案例

### 8.1 必须通过的样例场景

| 案例 | 输入 | 预期 |
|---|---|---|
| T01 基础单角色 | 角色正/背/侧图 + 24 秒剧情 | 三案→剧本→分镜→镜头级 Prompt 导出，无生成调用 |
| T02 双人对话 | A/B 的独立面部图和全身参考 | 说话人正确、特写引用正确、镜头反打方向可核验 |
| T03 拟人动作 | 双足犬类拿手机、开门、坐下 | 角色特征保留，手部/道具/尾巴状态写入分镜和 Prompt |
| T04 多镜头追逐 | 转身→奔跑→停下→喘息 | 位移方向/动作阶段/体力变化按镜头承接 |
| T05 资料不全 | 缺面部特写、侧面图 | 仅提出缺口与可用替代，不编造资产 |
| T06 数据错误 | 角色 ID 不存在或镜头时间断裂 | CLI 非零退出，指出具体错误位置 |
| T07 改角色设定 | 已审核后更改帽子/服装 | 标记受影响提示词 stale，并要求重新审核 |
| T08 多平台使用 | 同一套素材供两个不同视频模型 | 导出中性、可复制文本，无 Renoise 标签依赖 |
| T09 用户中断恢复 | 只批准到 S3 后重新进入 | 从已批准的产物继续，不丢失剧情选择 |
| T10 版权边界 | 用户提及既有 IP 二创 | 提示合理权利风险，不提供绕过审核方案 |

### 8.2 完成定义（DoD）

- 所有 P0 流程能在无 Renoise、无 API、无网络、无 FFmpeg 的本地环境中完成文字交付。
- 至少形成 `series.json`、`episode.json`、`shots.json`、镜头提示词、`prompt-manifest.json`、可读分镜表、审核与校验报告。
- 每个镜头具有稳定 ID、非空动作描述、明确时间、可选参考图映射以及与相邻镜头的连续性说明。
- 角色头脸/耳尾/服装等约束在生成 Prompt 中可追溯到系列圣经。
- 自动化测试覆盖正向样例、结构异常、时间轴、引用缺失、连续性冲突、改动失效和离线运行。
- 文档、例子和 CLI 帮助完全不要求配置 Renoise。
- 结果为**待后续模型执行的内容包**，界面与文档不得误标为“已生成视频”。

## 9. 实施里程碑

- **M0 文档基线**：本 SPEC + 重构设计落档；确定 V1 不接 API/MCP。
- **M1 Schema 与验证器**：项目/系列/单集/分镜及引用 Schema，结构校验与最小样例。
- **M2 Skill 与提示词编译器**：改写 Skill 路由和角色规则，输出中性镜头提示词。
- **M3 连续性与审核**：动作状态检查、审核记录、增量失效标记及导出清单。
- **M4 验收测试**：用拟人犬类示例跑通 20–30 秒单集；再用非拟人角色作一次回归，确保没有把 Skill 写死为某 IP。

## 10. 后续版本边界

V2 可增强动作/角色一致性 QA 与图形化资产管理；V3 才引入可插拔的 ComfyUI / 自定义 API / 其他生成平台适配器。未来插件仅消费 V1 标准化产物，不应该反向污染剧情、角色和提示词核心数据合同。

---
**本文件是设计规范，不代表已完成代码改造或已有成片能力。**