# N4 门禁

完整规则见 [../gate-policy.md](../gate-policy.md)，本节只列执行顺序。

1. **① 确定性层**：跑 check_gate.py（字数区间来自控制卡，占比/容差来自 `设定/门禁配置.json`；路径与调用惯例见 gate-policy.md）+ story-deslop `check-ai-patterns.js --fail-on=blocking`。输出与预算存 `追踪/门禁/{章号}-R{轮}.json`。
2. **② 语义对卡审查**：v0.2 起优先派发**对卡审查子代理**（输入=控制卡+正文+`追踪/上下文.md` 最新两节+细纲；输出=固定结构：禁止事项逐条✓✗/必埋伏笔/出场越界/钩子兑现/情节点完整/事实冲突清单），调度员只读结论做裁决，**不通读正文**——这是调度员上下文不随章数膨胀的关键。代理不可用时降级为调度员亲审（solo 模式先做③再做②，先冷读后对卡），并接受上下文成本。
3. **③ 冷读**：按 [../cold-read-review.md](../cold-read-review.md) 执行并对账；执行频率按 `设定/门禁配置.json` 的 `cold_read_mode`（见 gate-policy.md「冷读抽检」）。
4. **判定与修复**：按 gate-policy.md 的分级处置与修复规则执行。修复由写手子代理执行（重派发，指令=失败项+check_gate 输出的精确预算+控制卡约束）。
5. **轮次与分流**：按 gate-policy.md「轮次上限与分流」执行（含 waive 的 METRICS 记账）。
6. 每轮更新 `.flow-status.json`（rounds 字段 +1，detail 写大白话，如"第 2 轮：还差 120 字对话"）。
