# 最小技术验证边界

目的：在页面开发前核实统一EquipmentSlot、[start,end)、btree_gist排斥约束、事务和锁顺序。实际执行看verification.md，测试存在不能代替通过。

最新实测：2026-11-10，PostgreSQL17.11/Python3.13.9数据库测试12项通过；20独立连接×20轮的服务层竞争每轮1成功/19业务冲突，20连接预约维护混合竞争同样通过。随后GitHub CI的Python3.12/3.13两组各31项测试通过。对应JUnit、逐轮属性与CI日志见verification.md。应用HTTP端点仍未实现，全部Story仍TODO。

实现：equipment/booking/audit模型和迁移、accounts ADMIN组策略；create_slot/cancel_slot/set_equipment_enabled；锁Equipment后检查状态和当前时间，取消再锁Slot；日志失败同事务回滚。只有/health/进程端点，无业务HTTP页面。

数据库：NOT NULL、正时长、kind/status与owner类型检查；GiST对全部ACTIVE预约和维护共同排斥。已结束ACTIVE保留历史，实际区间自然不影响未来；CANCELLED释放。迁移先建btree_gist，再建排斥约束。应用冲突预查在设备锁后执行，数据库约束独立兜底，明确的排斥错误在atomic外转业务冲突。

数据库测试包括：绕过应用约束、邻接与不同设备、预约/维护双向互斥、取消审计/幂等/不恢复、停用保留和拒绝、is_staff不能代替ADMIN、审计失败回滚、20独立连接×20轮、20连接混合竞争、直接数据库竞争、启停与创建的两种提交次序。连接PID去重证明独立连接。pytest事务模式允许跨连接可见提交。

无数据库测试覆盖时间、取消边界、越权、幂等和健康检查。两层分开报告，不能用SQLite或规则测试冒充PostgreSQL并发通过。没有性能、真人可用性、HTTP安全、重启恢复或完整Story验收结果。Python3.12目标与本机3.13实际运行需分别核对。没有安装BMAD。

官方机制说明：[Django 5.2 ExclusionConstraint](https://docs.djangoproject.com/en/5.2/ref/contrib/postgres/constraints/)、[PostgreSQL 17 range类型](https://www.postgresql.org/docs/17/rangetypes.html)、[Django select_for_update](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update)。这些依据说明机制与使用限制，不能替代本机数据库运行证据。

实测边界：绕过设备锁直接并发插入可能触发23P01排斥冲突或40P01死锁中止。该测试只证明最终无双重提交，不保证业务友好错误；生产业务必须经设备锁服务。应用服务测试仍严格要求19个SlotConflict，不能把死锁与之混算。首次失败与修正后的通过均保留，不删除失败证据。
