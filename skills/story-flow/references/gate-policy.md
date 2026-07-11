# 门禁分级与轮次规则

N4 按本文件执行。每轮门禁结果写入 `追踪/门禁/{章号}-R{轮}.json`（check_gate.py 输出 + 语义/冷读结论摘要），供 METRICS 与阶段审查引用。**本文件是门禁规则的唯一正典**：其他文档提到门禁时以此为准，不重复数值。

## 字数口径（全流程统一）

字数 = `len(全文文本)` 全码点计数，与仓库钦定口径一致（`scripts/test-charcount-portable.sh` 的 `len(Path.read_text())`、check-prose-after-write hook、细纲情节点序列的字数预算同源）。**禁止混用"仅中文字符数"口径**；check_gate.py 输出的 `cn_chars` 仅供参考。

## 阈值放哪里（两层）

- **全书级**：`设定/门禁配置.json`（初始化 Step 4 生成），存对话占比区间、各容差、超长段阈值。改全书阈值只改这一个文件。
- **单章级**：控制卡「字数预算」区间 = [细纲目标, 细纲目标×1.1]（继承 `skills/story-long-write/references/artifact-protocols.md` 情节点序列的 Σ预算契约），经 CLI `--min-chars/--max-chars` 传入。

容差默认值以 check_gate.py 内置 DEFAULTS 与配置模板为准（当前：字数 ±2%、对话占比 ±3pt）。

## 工具路径与调用

- check_gate.py：仓库内 `skills/story-flow/scripts/check_gate.py` → 已部署项目 `.claude/skills/story-flow/scripts/check_gate.py`，按序探测；调用必须走仓库解释器探测惯例（`for PYBIN in python3 python py; do ...`），禁止裸调 python3。
- linter：`story-deslop` 的 `check-ai-patterns.js --fail-on=blocking`，同样按 仓库内 → 已部署 顺序找；node 或脚本不可用时跳过该项并在门禁产物中记 `linter:skipped`，不得假装跑过。

## 三层门禁（按序执行，前层不过不进后层）

| 层 | 工具/方式 | 检查什么 |
|----|-----------|----------|
| ① 确定性 | check_gate.py + linter | 字数区间、对话占比、超长段落（advisory）；AI 风格指纹（blocking 级） |
| ② 语义自审 | 调度员对照控制卡与正典 | 禁止事项未违反、必埋伏笔已埋、出场人物未越界、钩子按卡兑现、与 `追踪/` 无事实冲突、细纲情节点未漏；通用维度（一致性/对话质量）的判据向 story-review 的内置审查基准对齐，不另立标准 |
| ③ 冷读 | 冷读代理（见 cold-read-review.md） | 追读意愿、记忆点、跳读点；与控制卡承诺情绪对账 |

## 分级与处置

| 级别 | 例 | 处置 |
|------|----|------|
| **blocking** | linter blocking 指纹；违反控制卡禁止事项；与正典事实冲突；漏埋必埋伏笔 | 必修，计入轮次 |
| **预算类** | 欠字/超字、对话占比出带（容差后仍出界） | 必修但**不计轮次上限**：用 check_gate.py 输出的修复预算改 |
| **advisory** | linter advisory；冷读 3 分；超长段落 | 记入门禁产物放行，不回炉；聚集时交 N6 |

## 修复规则

1. **预算类必须带数字**。直接使用 check_gate.py `repair_budget` 输出（need_chars / need_dialog_chars / cut_chars），指定补在哪个情节点、补什么类型内容；禁止手算公式、禁止无预算重写。
2. **修复受控制卡约束**。不得为凑对话让计划外角色登场，不得为凑字数提前消费爽点/伏笔。控制卡覆盖不了的修复需求 → 属于卡的缺陷，回 N3 修卡；**修卡记 1 轮，计入语义 blocking 轮次账**（卡缺陷属语义层问题）。
3. **修复顺序**：先内容（预算类、事实类）后风格；**deslop 终检必须在所有扩写/改写完成后单独执行一次**（依据见 architecture.md 实测：扩写轮会引入新指纹）。

## 轮次上限与分流

- **语义 blocking：2 轮上限**。第 1 轮全项修复；第 2 轮只修复仍失败项。仍不过 → 分流：
  - 一致性/事实/伏笔/安全类 → `state:"paused_for_human"`，出决策卡（现状、可选项、各自后果、推荐项）；
  - 纯风格/表达类 → 留痕放行：门禁产物记 `waived`+理由，**同时在 METRICS 该章 waive 列记 `w:{维度}`**（维度=失败项的 check 类别，如 风格/钩子/节奏）。METRICS waive 列近 5 章内同一维度出现 ≥3 次 → N6 强制触发。
- **预算类不限轮**，但同一指标连续 3 轮未收敛说明预算或口径有错 → 停下检查工具、配置与卡，而不是继续改稿。
- 连续 2 章发生人工分流 → 暂停整条流水线（全局规则），大概率是卷纲或文风基线问题，不是章的问题。
