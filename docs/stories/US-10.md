# US-10 管理员设置维护时段

状态：DRAFT。负责人：罗永煌；复核人：刘昊文；候选估点：5 SP。

关联：FR-14；E-03；sprint-2。状态以[sprint-status.yaml](../../sprint-status.yaml)为准。

## 用户价值与验收计划

作为管理员，我希望设置设备维护时间。

验收：
- AC1：合法空闲时段可创建 MAINTENANCE ACTIVE 占用。
- AC2：与已有预约重叠时拒绝，原预约不变。
- AC3：维护时段阻止新预约。
- AC4：MEMBER 创建维护返回403。
- AC5：预约和维护同时竞争同一设备同一时段，最多一个成功，数据库无重叠 ACTIVE 占用。
- AC6：管理员可在维护开始前以非空原因取消；保存操作者/时间/目标/原因；普通用户和已开始维护拒绝。
- AC7：维护取消仅释放该维护，重复取消保留首次审计，不恢复历史预约。
- AC8：不提供原地修改时段；取消后另建是独立操作，失败不得隐式恢复旧记录。

测试：test_create_maintenance、test_maintenance_conflicts_reservation、test_booking_conflicts_maintenance、test_member_cannot_create_maintenance、test_booking_maintenance_race。

## 开发前检查

- [ ] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；未批准项已标明。
- [ ] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：待完成。自动测试：待执行。复核意见：待填写。验收结论：待形成。

本卡中的测试名称为计划，不表示已执行；技术spike证据不替代本Story完整验收。
