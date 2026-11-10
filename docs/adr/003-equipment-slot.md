# ADR-003 统一 EquipmentSlot

Status: PROPOSED

选择统一预约/维护占用模型；未选 Reservation 与 Maintenance 分表。理由：统一资源时间冲突可在数据库层约束。代价：需要 kind/status 约束和业务校验。

评审状态：待团队评审；批准信息尚未填写。关联业务补充见 [规则审查](../rule-review.md)；实际验证见 [验证记录](../verification.md)。
