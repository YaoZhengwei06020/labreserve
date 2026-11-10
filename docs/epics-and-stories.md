> 文档状态：候选基线，待团队评审。业务规则与实施状态分别见 rule-review.md、project-state.md 和 verification.md。

# LabReserve — Epics & Stories

**版本：** v0.1\
**状态：** PROPOSED — 待团队评审\
**上游：** product-brief.md、prd.md、architecture.md

## 拆分原则
- 每条 Story 交付一个可独立验收的业务能力。
- 每条 Story 对应 FR/NFR。
- 验收标准可观察、可测试。
- 不得自行修改架构边界。
- 无测试证据不得标记 Done。

SP 为相对估算，不等于工时，需团队重估。

---

# Epic E-01：用户身份与权限管理

目标：让实验室成员与管理员安全登录并按角色访问功能。关联 FR-01/02/03、NFR-02。相关 ADR-001/005。

## US-01 用户登录和退出（P0，3 SP）
作为实验室成员，我希望通过有效账户登录并退出系统。

验收：
- AC1：有效凭据登录成功，建立会话并进入设备列表。
- AC2：错误密码登录失败，不建立有效会话。
- AC3：未登录访问受保护页面重定向登录；JSON接口不返回业务数据。
- AC4：退出后会话失效，再次访问需认证。

测试：test_login_success、test_login_invalid_credentials、test_anonymous_access、test_logout_invalidates_session。

## US-02 角色权限控制（P0，3 SP）
作为管理员，我希望系统区分 MEMBER 和 ADMIN，避免成员修改设备配置。

验收：
- AC1：MEMBER 可访问被允许的设备和预约功能。
- AC2：MEMBER 调用新增/编辑设备接口返回403且数据库不变。
- AC3：ADMIN 可访问授权管理功能。
- AC4：篡改前端参数不能绕过服务端授权。

测试：test_member_allowed_access、test_member_admin_forbidden、test_admin_allowed_access、test_role_parameter_tampering。

## US-03 当前用户信息（P1，1 SP）
作为登录成员，我希望查看当前账户名称和角色。

验收：
- AC1：返回当前会话对应用户名、显示名和角色。
- AC2：未登录不能获得账户信息。
- AC3：不得通过修改参数查询他人私有账户数据。

测试：test_current_user_profile、test_anonymous_profile_access、test_profile_data_isolation。

---

# Epic E-02：设备信息与状态管理

目标：集中管理设备信息和可预约状态。关联 FR-04/05/06。

## US-04 查看设备列表与详情（P0，3 SP）
作为成员，我希望浏览设备列表和详情。

验收：
- AC1：数据库有3台设备时，列表展示3台设备名称、位置、状态。
- AC2：查询 E001 返回正确编号、名称、描述、位置、状态。
- AC3：不存在设备返回404而非服务端异常。

测试：test_equipment_list、test_equipment_detail、test_equipment_not_found。

## US-05 管理员新增和编辑设备（P0，3 SP）
作为管理员，我希望添加设备和修改信息。

验收：
- AC1：提交合法设备信息后可查询新设备。
- AC2：重复设备编号创建失败，数据库无重复记录。
- AC3：修改名称或位置后查询反映更新。
- AC4：MEMBER 创建/编辑请求返回403。

测试：test_equipment_create、test_equipment_code_unique、test_equipment_edit、test_member_cannot_edit_equipment。

## US-06 启用与停用设备（P0，3 SP）
作为管理员，我希望停用故障设备并在恢复后启用。

验收：
- AC1：AVAILABLE 设备停用后为 DISABLED。
- AC2：DISABLED 设备不能创建新预约。
- AC3：重新启用后，在其他条件满足时可以预约。
- AC4：停用不自动删除或取消历史/未来预约及维护；提示仍保留的未来占用。
- AC5：停用同时拒绝新维护；仍可取消未来既有占用；重新启用不恢复取消记录。
- AC6：与预约创建竞争时锁同一设备，结果符合提交先后，无绕过停用状态的新占用。

测试：test_disable_equipment、test_disabled_equipment_rejects_booking、test_enable_equipment、test_disable_preserves_reservations。

---

# Epic E-03：设备预约与并发一致性

目标：查询日程、创建预约并保证预约与维护不重叠。关联 FR-07～10、FR-14、NFR-01/05。相关 ADR-002/003/004。

## US-07 查看设备预约日程（P0，3 SP）
作为成员，我希望查看设备占用时间。

验收：
- AC1：09:00–11:00 ACTIVE 预约在查询中展示。
- AC2：CANCELLED 记录不再作为占用。
- AC3：14:00–15:00 ACTIVE 维护时段显示为维护占用。
- AC4：日程不泄露其他成员不必要个人信息。

测试：test_schedule_active_slots、test_schedule_cancelled_slots、test_schedule_maintenance、test_schedule_privacy。

## US-08 创建合法预约（P0，5 SP）
作为成员，我希望选择设备和时间并提交预约。

验收：
- AC1：设备可用且时段无冲突时，创建当前用户的 ACTIVE 预约并返回标识。
- AC2：结束时间≤开始时间时拒绝。
- AC3：时长短于30分钟或长于4小时拒绝（数值待团队确认）。
- AC4：开始时间在过去或超出7天提前预约上限时拒绝（数值待团队确认）。
- AC5：成功后重新查询能看到预约。

测试：test_create_reservation、test_invalid_time_range、test_reservation_duration_limit、test_reservation_advance_limit、test_reservation_persisted。

## US-09 冲突检测与并发保护（P0，8 SP）
作为成员，我希望系统可靠阻止重叠预约。

验收：
- AC1：09:00–11:00已存在，09:00–11:00申请拒绝。
- AC2：09:00–11:00已存在，10:00–12:00申请拒绝。
- AC3：09:00–11:00已存在，11:00–12:00在其他条件合法时成功。
- AC4：20个独立请求竞争同一空闲时段，恰好1个成功、19个业务冲突，最终只有1条对应 ACTIVE 记录。
- AC5：连续20轮，每轮满足 AC4。
- AC6：绕过应用层查询的非法重叠写入仍被数据库约束阻止。

测试：test_exact_overlap、test_partial_overlap、test_adjacent_intervals、test_concurrent_booking、test_concurrency_repeated、test_database_exclusion_constraint。

## US-10 管理员设置维护时段（P0，5 SP）
作为管理员，我希望设置设备维护时间。

验收：
- AC1：合法空闲时段可创建 MAINTENANCE ACTIVE 占用。
- AC2：与已有预约重叠时拒绝，原预约不变。
- AC3：维护时段阻止新预约。
- AC4：MEMBER 创建维护返回403。
- AC5：预约和维护同时竞争同一设备同一时段，最多一个成功，数据库无重叠 ACTIVE 占用。
- AC6：管理员可在维护开始前以非空原因取消；保存操作者/时间/目标/原因；普通用户和已开始维护拒绝。
- AC7：维护取消仅释放该维护，重复取消保留首次审计，不恢复历史预约。
- AC8：不提供原地修改时段；取消后另建是独立操作，失败不得隐式恢复旧记录。

测试：test_create_maintenance、test_maintenance_conflicts_reservation、test_booking_conflicts_maintenance、test_member_cannot_create_maintenance、test_booking_maintenance_race。

---

# Epic E-04：预约记录与管理员操作

目标：成员管理个人预约，管理员查询全部预约并处理异常。关联 FR-11/12/13/15。

## US-11 查看个人预约（P0，3 SP）
作为成员，我希望查看自己的预约记录。

验收：
- AC1：成员 A 有2条记录时，个人页面返回2条。
- AC2：A 不会看到 B 的私有预约。
- AC3：CANCELLED 显示已取消。
- AC4：结束时间早于当前时间的 ACTIVE 记录显示已结束；不要求自动改变持久化状态。

测试：test_my_reservations、test_reservation_owner_isolation、test_cancelled_status_display、test_completed_status_display。

## US-12 取消个人预约（P0，3 SP）
作为成员，我希望取消本人尚未开始的预约。

验收：
- AC1：本人取消未开始 ACTIVE 预约后变为 CANCELLED，保留记录。
- AC2：取消后其他用户可在其他条件满足时预约该时段。
- AC3：不能取消其他用户预约，返回403且原记录不变。
- AC4：不能取消已经开始的预约。
- AC5：重复取消不产生额外有效占用或重复状态变更。

测试：test_cancel_own_reservation、test_rebook_after_cancel、test_cancel_other_user_forbidden、test_cancel_started_reservation、test_cancel_idempotent_state。

## US-13 管理员查询与处理异常预约（P1，5 SP）
作为管理员，我希望查询全部预约并取消异常预约，保留原因。

验收：
- AC1：管理员可查询不同成员的全部预约。
- AC2：可按设备、用户、状态筛选。
- AC3：MEMBER 访问管理接口返回403。
- AC4：管理员只能取消尚未开始的预约，必须填写非空原因（含自己的预约），状态改为 CANCELLED 并保存日志；开始后拒绝；重复取消保留首次审计。
- AC5：未填写原因时操作失败，预约不变。
- AC6：取消事务失败时，不留下与最终状态不一致的成功日志。

测试：test_admin_list_reservations、test_admin_filter_reservations、test_member_admin_reservation_forbidden、test_admin_cancel_with_reason、test_admin_cancel_requires_reason、test_admin_cancel_transaction_rollback。

---

## 故事总览

| Story | 内容 | 优先级 | SP |
|---|---|---|---:|
| US-01 | 用户登录和退出 | P0 | 3 |
| US-02 | 角色与权限控制 | P0 | 3 |
| US-03 | 当前用户信息 | P1 | 1 |
| US-04 | 设备列表与详情 | P0 | 3 |
| US-05 | 管理员新增和编辑设备 | P0 | 3 |
| US-06 | 启用与停用设备 | P0 | 3 |
| US-07 | 设备预约日程 | P0 | 3 |
| US-08 | 创建设备预约 | P0 | 5 |
| US-09 | 预约冲突与并发保护 | P0 | 8 |
| US-10 | 设备维护时段 | P0 | 5 |
| US-11 | 查看个人预约 | P0 | 3 |
| US-12 | 取消个人预约 | P0 | 3 |
| US-13 | 管理员预约管理 | P1 | 5 |
| **合计** | **13 Stories** | | **48** |

## Sprint 候选安排

### Sprint 1：基础系统与并发预约（25 SP）
US-01、US-02、US-04、US-05、US-08、US-09。\
目标：登录、权限、设备基础、预约闭环、PostgreSQL 并发技术验证。

### Sprint 2：完整预约管理与验收（23 SP）
US-03、US-06、US-07、US-10、US-11、US-12、US-13。\
目标：日程、维护、个人预约、取消、管理员功能、集成测试、实验 A、复盘和 GitHub 交付。

Sprint 分配和故事点为 AI 初估，须团队重估。

## 跨 Story 约束
- 所有预约创建共享 booking 服务。
- 预约和维护统一 EquipmentSlot。
- 时间测试使用可控制时钟。
- 并发测试使用真实 PostgreSQL。
- 权限由服务端检查。
- 状态变化必须保持事务一致性。
- Story Done 必须保留测试证据。

## 团队待批准规则（已给出统一候选口径）
- 管理员能否取消已开始预约。
- 维护时段是否允许取消，以及对应状态/操作。
- 设备停用后未来预约的处置与告知。
- 预约和设备停用并发时的锁顺序。
- 维护和预约并发时的锁顺序。
- 30分钟、4小时、7天规则是否接受。
- 时区是否为 Asia/Shanghai。
- 是否预置账户。
- 是否允许同时预约多台设备。
- 是否需要审批。

**当前状态：** 13条 Story 的候选基线形成，尚待团队评审和估算。

## 统一补充与验收边界

PRD v0.2与rule-review.md统一生命周期规则。13条Story均TODO，故事点为AI辅助初估，25+23=48；US-10增加维护取消验收条件后需团队重新估算。附列测试名称为验收计划，实际执行范围见verification.md。
