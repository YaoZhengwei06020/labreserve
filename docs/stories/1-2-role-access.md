# US-02 角色权限控制

状态：DRAFT。负责人：郑焰；复核人：姚政伟；候选估点：3 SP。

关联：FR-02；E-01；sprint-1。状态以[sprint-status.yaml](../../sprint-status.yaml)为准。

## 用户价值与验收计划

作为管理员，我希望系统区分 MEMBER 和 ADMIN，避免成员修改设备配置。

验收：
- AC1：MEMBER 可访问被允许的设备和预约功能。
- AC2：MEMBER 调用新增/编辑设备接口返回403且数据库不变。
- AC3：ADMIN 可访问授权管理功能。
- AC4：篡改前端参数不能绕过服务端授权。

测试：test_member_allowed_access、test_member_admin_forbidden、test_admin_allowed_access、test_role_parameter_tampering。

## 开发前检查

- [ ] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；未批准项已标明。
- [ ] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：待完成。自动测试：待执行。复核意见：待填写。验收结论：待形成。

本卡中的测试名称为计划，不表示已执行；技术spike证据不替代本Story完整验收。
