# US-09 冲突检测与并发保护

状态：DRAFT。负责人：刘昊文；复核人：罗永煌；候选估点：8 SP。

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

- [ ] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；未批准项已标明。
- [ ] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：待完成。自动测试：待执行。复核意见：待填写。验收结论：待形成。

本卡中的测试名称为计划，不表示已执行；技术spike证据不替代本Story完整验收。
