# N4 门禁

完整规则见 [../gate-policy.md](../gate-policy.md)，本节只列执行顺序。

1. **① 确定性层**：跑 `scripts/check_gate.py`（阈值来自控制卡与门禁配置）+ story-deslop `check-ai-patterns.js --fail-on=blocking`。输出与预算存 `追踪/门禁/{章号}-R{轮}.json`。
2. **② 语义自审**：对照控制卡逐项核对（禁止事项/必埋伏笔/出场人物/钩子/beat 完整性），再对照 `追踪/` 查事实冲突。solo 模式先做③再做②（先冷读后对卡）。
3. **③ 冷读轻量版**：按 [../cold-read-review.md](../cold-read-review.md) 执行并对账。
4. **判定与修复**：按分级处置（blocking 计轮修复 / 预算类算出数字修复不计轮 / advisory 留痕放行）。修复由写手子代理执行（重派发，指令=失败项+精确预算+控制卡约束）；修复顺序先内容后风格，**deslop 终检在全部改写完成后单独跑**。
5. **轮次与分流**：语义 blocking 2 轮上限，超限按类型分流（人工决策卡 / waive 留痕）；预算类连续 3 轮不收敛 → 查工具和卡，不是继续改稿。
6. 每轮更新 `.flow-status.json`（rounds 字段 +1，detail 写大白话，如"第 2 轮：还差 120 字对话"）。
