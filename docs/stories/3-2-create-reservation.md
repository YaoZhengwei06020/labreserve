# US-08 创建合法预约

状态：DRAFT。负责人：刘昊文；复核人：罗永煌；候选估点：5 SP。

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

- [ ] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；未批准项已标明。
- [ ] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：待完成。自动测试：待执行。复核意见：待填写。验收结论：待形成。

本卡中的测试名称为计划，不表示已执行；技术spike证据不替代本Story完整验收。
