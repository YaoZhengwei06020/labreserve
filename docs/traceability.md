# 需求追踪矩阵

本表覆盖15条FR与6条NFR的Story、架构和验证映射。执行结果见verification.md，规划中的测试不等同已完成验收。

| FR | Story | ADR | 验证入口或待实现项 |
| --- | --- | --- | --- |
| FR-01 | US-01 | ADR-001、ADR-005 | 登录退出HTTP待实现 |
| FR-02 | US-02 | ADR-005 | test_policy；test_staff_flag_is_not_business_admin；HTTP待实现 |
| FR-03 | US-03 | ADR-005 | 当前用户信息待实现 |
| FR-04 | US-04 | ADR-001 | 列表详情待实现 |
| FR-05 | US-05 | ADR-001 | 设备模型已有；管理表单待实现 |
| FR-06 | US-06 | ADR-004 | test_disable_preserves_slots_and_rejects_all_new_slots；test_disable_create_serialization |
| FR-07 | US-07 | ADR-003 | 日程与隐私待实现 |
| FR-08 | US-08 | ADR-003、ADR-004 | create_slot；页面待实现 |
| FR-09 | US-09 | ADR-002、ADR-004 | test_nfr01_20_connections_20_rounds；test_direct_database_race |
| FR-10 | US-08 | ADR-004 | test_invalid_interval；时长/提前量未实现 |
| FR-11 | US-11 | ADR-003 | 个人列表待实现 |
| FR-12 | US-12 | ADR-003、ADR-005 | test_cancellation_restrictions；test_cancellation_audit_and_maintenance_no_restore |
| FR-13 | US-13 | ADR-005 | 全体查询筛选待实现 |
| FR-14 | US-10 | ADR-003、ADR-004 | test_maintenance_conflict_both_directions；test_booking_maintenance_race；维护取消服务 |
| FR-15 | US-13 | ADR-005 | test_audit_failure_rolls_back_create_and_cancel；原因与审计 |

| NFR | ADR | 验证入口/原目标 |
| --- | --- | --- |
| NFR-01 | ADR-002/003/004 | PostgreSQL17.11服务层独立20连接×20轮已通过；HTTP验收仍待实现，见verification.md |
| NFR-02 | ADR-005 | 策略授权；HTTP/CSRF/身份隔离待实现 |
| NFR-03 | ADR-001/002 | 50用户/30设备/1000预约，列表p95≤500ms、日程≤800ms；未测 |
| NFR-04 | ADR-001/006/007 | GitHub全新Ubuntu/Python3.12和3.13环境迁移/测试已通过；Compose应用部署与完整Web启动待验收 |
| NFR-05 | ADR-002/004/007 | 审计回滚测试；重启持久性待验收 |
| NFR-06 | ADR-001 | 至少3名测试者/60秒内预约；未开展 |

规则修复见rule-review.md；全部Story均TODO。
