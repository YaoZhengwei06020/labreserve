# US-12 取消个人预约

状态：REVIEW。负责人：刘昊文；复核人：罗永煌；候选估点：3 SP。

关联：FR-12；E-04；sprint-2。状态以[sprint-status.yaml](../../sprint-status.yaml)为准。

## 用户价值与验收计划

作为成员，我希望取消本人尚未开始的预约。

验收：
- AC1：本人取消未开始 ACTIVE 预约后变为 CANCELLED，保留记录。
- AC2：取消后其他用户可在其他条件满足时预约该时段。
- AC3：不能取消其他用户预约，返回403且原记录不变。
- AC4：不能取消已经开始的预约。
- AC5：重复取消不产生额外有效占用或重复状态变更。

测试：test_cancel_own_reservation、test_rebook_after_cancel、test_cancel_other_user_forbidden、test_cancel_started_reservation、test_cancel_idempotent_state。

## 开发前检查

- [x] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；当前仍为PROPOSED，未批准项已标明。
- [x] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：`b264c2b`（取消模块）、`a195203`（取消入口与生产配置集成）。

自动测试：2026-11-24 完整测试 146 项通过，覆盖本人取消、越权、开始后拒绝、幂等、审计回滚及取消后重订。证据：[控制台输出](../evidence/integration/pytest.txt)、[JUnit](../evidence/integration/tests.xml)、[验收摘要](../evidence/integration/acceptance-summary.md)。

复核意见：待指定复核人罗永煌填写。验收结论：当前为 REVIEW，未标记 DONE。
