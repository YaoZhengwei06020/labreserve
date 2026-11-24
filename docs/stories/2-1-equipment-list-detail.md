# US-04 查看设备列表与详情

状态：REVIEW。负责人：郑焰；复核人：姚政伟；候选估点：3 SP。

关联：FR-04；E-02；sprint-1。状态以[sprint-status.yaml](../../sprint-status.yaml)为准。

## 用户价值与验收计划

作为成员，我希望浏览设备列表和详情。

验收：
- AC1：数据库有3台设备时，列表展示3台设备名称、位置、状态。
- AC2：查询 E001 返回正确编号、名称、描述、位置、状态。
- AC3：不存在设备返回404而非服务端异常。

测试：test_equipment_list、test_equipment_detail、test_equipment_not_found。

## 开发前检查

- [x] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；当前仍为PROPOSED，未批准项已标明。
- [x] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：`910b8a9`（基础模块）、`a195203`（设备详情预约入口与真实配置集成）。

自动测试：2026-11-24 完整测试 146 项通过，覆盖设备列表、详情、空状态、404 及生产模板和路由。证据：[控制台输出](../evidence/integration/pytest.txt)、[JUnit](../evidence/integration/tests.xml)、[验收摘要](../evidence/integration/acceptance-summary.md)。

复核意见：待指定复核人姚政伟填写。验收结论：当前为 REVIEW，未标记 DONE。
