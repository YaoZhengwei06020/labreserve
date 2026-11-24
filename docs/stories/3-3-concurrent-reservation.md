# US-09 冲突检测与并发保护

状态：REVIEW。负责人：刘昊文；复核人：罗永煌；候选估点：8 SP。

关联：FR-09、FR-10；E-03；sprint-1。状态以[sprint-status.yaml](../../sprint-status.yaml)为准。

## 用户价值与验收计划

作为成员，我希望系统可靠阻止重叠预约。

验收：
- AC1：09:00–11:00已存在，09:00–11:00申请拒绝。
- AC2：09:00–11:00已存在，10:00–12:00申请拒绝。
- AC3：09:00–11:00已存在，11:00–12:00在其他条件合法时成功。
- AC4：20个独立请求竞争同一空闲时段，恰好1个成功、19个业务冲突，最终只有1条对应 ACTIVE 记录。
- AC5：连续20轮，每轮满足 AC4。
- AC6：绕过应用层查询的非法重叠写入仍被数据库约束阻止。

测试：test_exact_overlap、test_partial_overlap、test_adjacent_intervals、test_concurrent_booking、test_concurrency_repeated、test_database_exclusion_constraint。

## 开发前检查

- [x] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；当前仍为PROPOSED，未批准项已标明。
- [x] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：`f48e71e`（预约模块）、`a195203`（集成）、`c8567e8`（独立测试）、`7b6af62`（独立验证证据）。

自动测试：2026-11-24 完整测试 146 项通过；独立验证 35 项通过。20 个独立连接连续 20 轮均为 1 成功、19 业务冲突、最终 1 条 ACTIVE。证据：[完整 JUnit](../evidence/integration/tests.xml)、[独立验收矩阵](../evidence/us09/acceptance-matrix.md)、[独立验证 JUnit](../evidence/us09/tests.xml)。

复核意见：待指定复核人罗永煌填写。验收结论：当前为 REVIEW，未标记 DONE；技术验证和独立 Agent 结论不代替指定复核人的接受结论。
