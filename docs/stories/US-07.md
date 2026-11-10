# US-07 查看设备预约日程

状态：DRAFT。负责人：罗永煌；复核人：刘昊文；候选估点：3 SP。

关联：FR-07；E-03；sprint-2。状态以[sprint-status.yaml](../../sprint-status.yaml)为准。

## 用户价值与验收计划

作为成员，我希望查看设备占用时间。

验收：
- AC1：09:00–11:00 ACTIVE 预约在查询中展示。
- AC2：CANCELLED 记录不再作为占用。
- AC3：14:00–15:00 ACTIVE 维护时段显示为维护占用。
- AC4：日程不泄露其他成员不必要个人信息。

测试：test_schedule_active_slots、test_schedule_cancelled_slots、test_schedule_maintenance、test_schedule_privacy。

## 开发前检查

- [ ] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；未批准项已标明。
- [ ] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：待完成。自动测试：待执行。复核意见：待填写。验收结论：待形成。

本卡中的测试名称为计划，不表示已执行；技术spike证据不替代本Story完整验收。
