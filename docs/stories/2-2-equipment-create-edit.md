# US-05 管理员新增和编辑设备

状态：REVIEW。负责人：郑焰；复核人：姚政伟；候选估点：3 SP。

关联：FR-05；E-02；sprint-1。状态以[sprint-status.yaml](../../sprint-status.yaml)为准。

## 用户价值与验收计划

作为管理员，我希望添加设备和修改信息。

验收：
- AC1：提交合法设备信息后可查询新设备。
- AC2：重复设备编号创建失败，数据库无重复记录。
- AC3：修改名称或位置后查询反映更新。
- AC4：MEMBER 创建/编辑请求返回403。

测试：test_equipment_create、test_equipment_code_unique、test_equipment_edit、test_member_cannot_edit_equipment。

## 开发前检查

- [x] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；当前仍为PROPOSED，未批准项已标明。
- [x] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：`910b8a9`（基础模块）、`a195203`（生产配置集成）。

自动测试：2026-11-24 完整测试 146 项通过，覆盖新增、编辑、编号唯一、权限及普通表单不可修改设备状态。证据：[控制台输出](../evidence/integration/pytest.txt)、[JUnit](../evidence/integration/tests.xml)、[验收摘要](../evidence/integration/acceptance-summary.md)。

复核意见：待指定复核人姚政伟填写。验收结论：当前为 REVIEW，未标记 DONE。
