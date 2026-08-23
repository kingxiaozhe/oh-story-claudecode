# Story Flow 运行策略

## 状态机

```text
N1 初始化 → N2 进卷/批次 → N3 控制卡与写章 → N4 门禁
→ N5 回写落账 → N6 阶段审查 → N7 上下文管理 → N8 收尾
```

批次未完成时从 N5/N6 回到 N3；还有下一批或卷时从 N7 回到 N2。每到一个节点只读取 `references/nodes/` 对应文件，不预读全部。

## 状态落盘

每进入一个节点，覆盖写入项目 `.flow-status.json` 单行 JSON：

```json
{"node":"N4","volume":"卷1","chapter":"C-0012","detail":"第2轮门禁：还差120字对话","state":"running","rounds":2,"at":"2026-07-11 16:05:00"}
```

`node/state/at` 必写，`at` 使用完整日期时间；已知时写 `volume/chapter/rounds`。`detail` 用大白话。等人时为 `paused_for_human`，完成为 `done`。

## 暂停条件

只在以下情况暂停：大纲未明确的主线级歧义或不可逆角色转折、平台红线风险、连续两章门禁转人工、环境阻塞、配置的作者巡检点。计划内巡检不计人工介入；其他暂停在 METRICS 记录原因并将人工介入加一。

## 任务、代理与降级

- N2 将本批章节镜像到任务清单；N3 置进行中，N5 置完成。断点恢复跳过已完成章。
- 写手/冷读代理按 `.claude/agents/`、`.opencode/agents/`、`.codex/agents/*.toml` 查找。
- 无代理时 solo，并记录 `Fallback: agent unavailable -> solo`；N4 必须换视角冷读后再对控制卡。
- story-long-write、story-review、story-deslop 引用缺失时，先从对应 SKILL 的参考表重新定位；仍缺失则记录 `linter:skipped` 或 `fallback:协议缺失`，禁止凭记忆默写。

## 度量与文件边界

`追踪/METRICS.md` 每章记录轮次、失败项、最终全码点字数、人工介入、waive 和备注，是验收与 N6 waive 计数的数据源。

写入只限当前书项目的控制卡、大纲、正文、设定、追踪、门禁和 `.flow-status.json`。已发布章节不可重写；冲突以 `设定/` 与 `追踪/` 正典为准。

## Git 边界

N5 可在项目既定工作流已授权本地提交时，为本章及其同步追踪文件创建范围明确的本地 commit。不得夹带其他改动，不得自动 push、merge、发布或改写历史；未获得提交授权时只完成文件和验证并报告未提交状态。
