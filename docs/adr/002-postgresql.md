# ADR-002 PostgreSQL

Status: PROPOSED

选择 PostgreSQL；未选 SQLite。理由：依赖 GiST 排除约束、事务和行级锁；SQLite 无法提供相同机制。代价：需管理数据库服务。

评审状态：待团队评审；批准信息尚未填写。关联业务补充见 [规则审查](../rule-review.md)；实际验证见 [验证记录](../verification.md)。
