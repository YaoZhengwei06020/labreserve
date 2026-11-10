# US-05 管理员新增和编辑设备

状态：DRAFT。负责人：郑焰；复核人：姚政伟；候选估点：3 SP。

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

- [ ] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；未批准项已标明。
- [ ] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：待完成。自动测试：待执行。复核意见：待填写。验收结论：待形成。

本卡中的测试名称为计划，不表示已执行；技术spike证据不替代本Story完整验收。
