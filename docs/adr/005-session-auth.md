# ADR-005 Session Authentication

Status: PROPOSED

选择 Django Session；未选自行实现 JWT。理由：同源 Web 应用，无需 Token 刷新和撤销体系。代价：未来独立客户端需重新评估。

评审状态：待团队评审；批准信息尚未填写。关联业务补充见 [规则审查](../rule-review.md)；实际验证见 [验证记录](../verification.md)。
