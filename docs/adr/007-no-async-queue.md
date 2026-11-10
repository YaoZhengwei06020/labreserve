# ADR-007 不引入异步队列

Status: PROPOSED

MVP 不引入 Celery/RabbitMQ；未选异步任务架构。理由：当前没有必须后台执行的长任务，预约成功必须以数据库事务提交为准。代价：复杂通知/批处理未来需扩展。

评审状态：待团队评审；批准信息尚未填写。关联业务补充见 [规则审查](../rule-review.md)；实际验证见 [验证记录](../verification.md)。
