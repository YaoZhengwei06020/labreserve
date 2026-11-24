# US-08 创建合法预约

状态：REVIEW。负责人：刘昊文；复核人：罗永煌；候选估点：5 SP。

关联：FR-08、FR-10；E-03；sprint-1。状态以[sprint-status.yaml](../../sprint-status.yaml)为准。

## 用户价值与验收计划

作为成员，我希望选择设备和时间并提交预约。

验收：
- AC1：设备可用且时段无冲突时，创建当前用户的 ACTIVE 预约并返回标识。
- AC2：结束时间≤开始时间时拒绝。
- AC3：时长短于30分钟或长于4小时拒绝（数值待团队确认）。
- AC4：开始时间在过去或超出7天提前预约上限时拒绝（数值待团队确认）。
- AC5：成功后重新查询能看到预约。

测试：test_create_reservation、test_invalid_time_range、test_reservation_duration_limit、test_reservation_advance_limit、test_reservation_persisted。

## 开发前检查

- [x] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；当前仍为PROPOSED，未批准项已标明。
- [x] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：`f48e71e`（预约模块）、`a195203`（页面与生产配置集成）。

自动测试：2026-11-24 完整测试 146 项通过，覆盖时间边界、当前用户归属、冲突反馈、权限和创建后查询。证据：[控制台输出](../evidence/integration/pytest.txt)、[JUnit](../evidence/integration/tests.xml)、[验收摘要](../evidence/integration/acceptance-summary.md)。

复核意见：待指定复核人罗永煌填写。验收结论：当前为 REVIEW，未标记 DONE；30 分钟、4 小时、7 天仍为 PROPOSED，团队批准状态不因实现和测试通过而改变。
