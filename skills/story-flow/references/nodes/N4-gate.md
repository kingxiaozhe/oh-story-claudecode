# N4 门禁

完整规则见 [../gate-policy.md](../gate-policy.md)，本节只列执行顺序。

1. **① 确定性层**：跑 check_gate.py（字数区间来自控制卡，占比/容差来自 `设定/门禁配置.json`；路径与调用惯例见 gate-policy.md）+ story-deslop `check-ai-patterns.js --fail-on=blocking`。输出与预算存 `追踪/门禁/{章号}-R{轮}.json`。
2. **② 语义自审**：对照控制卡逐项核对（禁止事项/必埋伏笔/出场人物/钩子/beat 完整性），再对照 `追踪/` 查事实冲突。solo 模式先做③再做②（先冷读后对卡）。
3. **③ 冷读轻量版**：按 [../cold-read-review.md](../cold-read-review.md) 执行并对账。
4. **判定与修复**：按 gate-policy.md 的分级处置与修复规则执行。修复由写手子代理执行（重派发，指令=失败项+check_gate 输出的精确预算+控制卡约束）。
5. **轮次与分流**：按 gate-policy.md「轮次上限与分流」执行（含 waive 的 METRICS 记账）。
6. 每轮更新 `.flow-status.json`（rounds 字段 +1，detail 写大白话，如"第 2 轮：还差 120 字对话"）。
