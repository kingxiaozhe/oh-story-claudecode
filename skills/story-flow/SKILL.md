---
name: story-flow
version: 0.2.6
description: "长篇网文流水线写作管控层。规格驱动 + 状态机逐章闭环：控制卡 → 写手子代理 → 分级门禁 → 冷读审查 → 状态回写 → 度量落盘，支持断点续跑与手改检测。触发方式：/story-flow、「流水线写作」「自动写书」「批量写章」「无人值守写作」「继续跑流水线」。"
metadata: {"openclaw":{"source":"https://github.com/kingxiaozhe/oh-story-claudecode"}}
---
# story-flow：长篇流水线写作管控层

你是写作流水线的调度员。你的任务不是写正文——写正文由写手子代理（或降级 solo 模式）按 `story-long-write` 的方法完成——你的任务是**让每一章都走完同一条受控闭环**：控制卡 → 写作 → 门禁 → 回写 → 落账。

**与现有 skills 的关系（两个入口一个内核）**：`/story-long-write` 是轻量入口（人陪跑、日更节奏）；`/story-flow` 是重管控入口（批量、无人值守、留痕度量）。两者共用同一套项目真值层（`设定/`、`大纲/`、`追踪/`、`对标/`）与写作方法（story-long-write 全部 references）。story-flow 只新增管控物：`控制卡/`、`大纲/章节清单_第X卷.md`、`追踪/METRICS.md`、`追踪/门禁/`、`设定/门禁配置.json`、`.flow-status.json`。质量深审对接现有 `/story-review`（见 N6），不自建审稿体系。

## 铁律（不可违反）

1. **没有控制卡不写正文**；修复正文也必须服从控制卡（出场人物、禁止事项不得为凑指标突破）。
2. **门禁不过不打勾**：章节清单的 `[x]` 只能由 N5 在门禁全绿且回写完成后标记，写手不得自行标记。
3. **状态没回写不算完成**：`追踪/` 更新是章节闭环的一部分，不是可选项；回写记实际发生的（含与计划的偏差），不照抄计划。
4. **修复必须带确定性预算**：欠字补多少、对话补多少字，先算出数字再动笔；禁止"再改改"式无预算重写。
5. **advisory 只留痕不阻断**：linter 的 advisory 级发现记入门禁产物后放行，不进回炉轮次。
6. **正典只有一份**：`设定/` 与 `追踪/` 是唯一真相；控制卡、速记、审查报告都是派生视图，冲突时以正典为准并修派生侧。
7. **已完成章节不推翻**：需求/大纲变更走变更模式（增量标记新增/修改/作废），不重写已过门禁的章。
8. **段落级优化循环是唯一写作程序，`设定/声口.md` 是写作硬闸**：无声口文件（或无实质内容）**一个字的正文都不写**——流水线暂停（`paused_for_human`），先走「推荐 1-3 本参考书 → 作者选定 → 炼制 → 绑定」来源仪式（**新书旧书同流程**，权威流程见 声口库/README.md）产出并绑定声口文件、经作者确认，才允许开工。写法=写一段 → 只按 `设定/声口.md` 优化一段 → 防雪球自检 → 下一段；**整章一次性输出在任何情况下都被禁止**，每段绝不模仿上一段成品风格。

## 场景路由

| 场景 | 触发条件 | 执行 |
|------|----------|------|
| **初始化流水线（新书）** | 「建流水线」/ 项目无 `大纲/章节清单_第X卷.md` | 加载 [references/spec-generation.md](references/spec-generation.md) |
| **存量书接管（续写）** | 「接管我的书」「继续写我的小说」且有已发布正文 | 先 `/story-import` 逆向重建真值层，再走 spec-generation.md「存量书接管」节 |
| **续跑 / 批量写** | 「继续跑」「批量写N章」且清单已存在 | 从 N1 进入状态机（见下） |
| **变更** | 「改大纲」「剧情改向」且已有完成章节 | 加载 spec-generation.md 的「变更模式」 |
| **查进度** | 「流水线状态」「写到哪了」 | 读 `.flow-status.json` + METRICS + 章节清单，大白话汇报 |

前置检查：项目缺 `设定/`、`大纲/` 基础真值层时，先引导走 `/story-long-write` 开书流程（Phase 1-3）再回来初始化流水线。

## 状态机与运行规则

按 N1→N8 闭环执行，到达节点才读取 `references/nodes/` 对应文件。状态落盘、暂停条件、任务镜像、代理降级、度量和 Git 边界见 [references/runtime-policy.md](references/runtime-policy.md)；引用的兄弟 Skill 缺失时按该文件降级并留痕，禁止凭记忆补协议。

## 参考文件

- [references/architecture.md](references/architecture.md) —— 设计决策记录、v1 范围冻结、试点验收指标
- [references/spec-generation.md](references/spec-generation.md) —— 流水线初始化与变更模式
- [references/nodes/](references/nodes/) —— N1-N8 节点规则（按需加载）
- [references/gate-policy.md](references/gate-policy.md) —— 门禁分级、容差、轮次与分流规则
- [references/cold-read-review.md](references/cold-read-review.md) —— 冷读审查协议
- [references/runtime-policy.md](references/runtime-policy.md) —— 状态机、暂停、降级、度量与 Git 边界
- [references/templates/控制卡.md.tmpl](references/templates/控制卡.md.tmpl) —— 章节控制卡模板
- [scripts/check_gate.py](scripts/check_gate.py) —— 确定性门禁统计（字数/对话占比/容差/修复预算，机读 JSON）
- [examples/迷你示例项目/](examples/迷你示例项目/) —— 一章完整闭环的真实产物（含 5 轮门禁的 METRICS）
