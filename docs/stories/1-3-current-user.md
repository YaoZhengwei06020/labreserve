# US-03 当前用户信息

状态：DRAFT。负责人：郑焰；复核人：姚政伟；候选估点：1 SP。

关联：FR-03；E-01；sprint-2。状态以[sprint-status.yaml](../../sprint-status.yaml)为准。

## 用户价值与验收计划

作为登录成员，我希望查看当前账户名称和角色。

验收：
- AC1：返回当前会话对应用户名、显示名和角色。
- AC2：未登录不能获得账户信息。
- AC3：不得通过修改参数查询他人私有账户数据。

测试：test_current_user_profile、test_anonymous_profile_access、test_profile_data_isolation。

## 开发前检查

- [ ] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；未批准项已标明。
- [ ] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：待完成。自动测试：待执行。复核意见：待填写。验收结论：待形成。

本卡中的测试名称为计划，不表示已执行；技术spike证据不替代本Story完整验收。
