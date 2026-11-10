# US-06 启用与停用设备

状态：DRAFT。负责人：郑焰；复核人：姚政伟；候选估点：3 SP。

关联：FR-06；E-02；sprint-2。状态以[sprint-status.yaml](../../sprint-status.yaml)为准。

## 用户价值与验收计划

作为管理员，我希望停用故障设备并在恢复后启用。

验收：
- AC1：AVAILABLE 设备停用后为 DISABLED。
- AC2：DISABLED 设备不能创建新预约。
- AC3：重新启用后，在其他条件满足时可以预约。
- AC4：停用不自动删除或取消历史/未来预约及维护；提示仍保留的未来占用。
- AC5：停用同时拒绝新维护；仍可取消未来既有占用；重新启用不恢复取消记录。
- AC6：与预约创建竞争时锁同一设备，结果符合提交先后，无绕过停用状态的新占用。

测试：test_disable_equipment、test_disabled_equipment_rejects_booking、test_enable_equipment、test_disable_preserves_reservations。

## 开发前检查

- [ ] 对应业务规则和接口边界已明确。
- [ ] 相关ADR已评审；未批准项已标明。
- [ ] 验收条件可转为断言，测试数据与失败路径已定义。

## 实施与复核证据

实施提交：待完成。自动测试：待执行。复核意见：待填写。验收结论：待形成。

本卡中的测试名称为计划，不表示已执行；技术spike证据不替代本Story完整验收。
