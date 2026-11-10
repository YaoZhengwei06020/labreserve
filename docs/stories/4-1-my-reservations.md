# US-11 查看个人预约

状态：DRAFT。负责人：罗永煌；复核人：刘昊文；候选估点：3 SP。

关联：FR-11；E-04；sprint-2。状态以[sprint-status.yaml](../../sprint-status.yaml)为准。

## 用户价值与验收计划

作为成员，我希望查看自己的预约记录。

验收：
- AC1：成员 A 有2条记录时，个人页面返回2条。
- AC2：A 不会看到 B 的私有预约。
- AC3：CANCELLED 显示已取消。
- AC4：结束时间早于当前时间的 ACTIVE 记录显示已结束；不要求自动改变持久化状态。

测试：test_my_reservations、test_reservation_owner_isolation、test_cancelled_status_display、test_completed_status_display。

## 开发前检查

- [ ] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；未批准项已标明。
- [ ] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：待完成。自动测试：待执行。复核意见：待填写。验收结论：待形成。

本卡中的测试名称为计划，不表示已执行；技术spike证据不替代本Story完整验收。
