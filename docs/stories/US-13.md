# US-13 管理员查询与处理异常预约

状态：DRAFT。负责人：姚政伟；复核人：郑焰；候选估点：5 SP。

关联：FR-13、FR-15；E-04；sprint-2。状态以[sprint-status.yaml](../../sprint-status.yaml)为准。

## 用户价值与验收计划

作为管理员，我希望查询全部预约并取消异常预约，保留原因。

验收：
- AC1：管理员可查询不同成员的全部预约。
- AC2：可按设备、用户、状态筛选。
- AC3：MEMBER 访问管理接口返回403。
- AC4：管理员只能取消尚未开始的预约，必须填写非空原因（含自己的预约），状态改为 CANCELLED 并保存日志；开始后拒绝；重复取消保留首次审计。
- AC5：未填写原因时操作失败，预约不变。
- AC6：取消事务失败时，不留下与最终状态不一致的成功日志。

测试：test_admin_list_reservations、test_admin_filter_reservations、test_member_admin_reservation_forbidden、test_admin_cancel_with_reason、test_admin_cancel_requires_reason、test_admin_cancel_transaction_rollback。

## 开发前检查

- [ ] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；未批准项已标明。
- [ ] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：待完成。自动测试：待执行。复核意见：待填写。验收结论：待形成。

本卡中的测试名称为计划，不表示已执行；技术spike证据不替代本Story完整验收。
