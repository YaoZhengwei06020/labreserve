# US-01 用户登录和退出

状态：DRAFT。负责人：郑焰；复核人：姚政伟；候选估点：3 SP。

关联：FR-01；E-01；sprint-1。状态以[sprint-status.yaml](../../sprint-status.yaml)为准。

## 用户价值与验收计划

作为实验室成员，我希望通过有效账户登录并退出系统。

验收：
- AC1：有效凭据登录成功，建立会话并进入设备列表。
- AC2：错误密码登录失败，不建立有效会话。
- AC3：未登录访问受保护页面重定向登录；JSON接口不返回业务数据。
- AC4：退出后会话失效，再次访问需认证。

测试：test_login_success、test_login_invalid_credentials、test_anonymous_access、test_logout_invalidates_session。

## 开发前检查

- [ ] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；未批准项已标明。
- [ ] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：待完成。自动测试：待执行。复核意见：待填写。验收结论：待形成。

本卡中的测试名称为计划，不表示已执行；技术spike证据不替代本Story完整验收。
