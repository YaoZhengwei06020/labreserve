# US-02 角色权限控制

状态：REVIEW。负责人：郑焰；复核人：姚政伟；候选估点：3 SP。

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

- [x] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；当前仍为PROPOSED，未批准项已标明。
- [x] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：`910b8a9`（基础模块）、`a195203`（生产配置集成）。

自动测试：2026-11-24 完整测试 146 项通过，覆盖 MEMBER/ADMIN、越权、参数篡改及 `is_staff` 非业务管理员场景。证据：[控制台输出](../evidence/integration/pytest.txt)、[JUnit](../evidence/integration/tests.xml)、[验收摘要](../evidence/integration/acceptance-summary.md)。

复核意见：待指定复核人姚政伟填写。验收结论：当前为 REVIEW，未标记 DONE。
