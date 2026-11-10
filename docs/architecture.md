> 文档状态：候选基线，待团队评审。业务规则与实施状态分别见 rule-review.md、project-state.md 和 verification.md。

# LabReserve — 系统架构设计文档

**版本：** v0.1\
**状态：** PROPOSED（待团队评审）\
**上游：** product-brief.md、prd.md

## 1. 架构目标与原则

目标：满足设备预约、维护、并发一致性、安全、可部署和团队协作。

质量属性：NFR-01一致性、NFR-02安全、NFR-03性能、NFR-04部署、NFR-05可靠性、NFR-06可用性。

原则：
- 优先业务正确性。
- 成熟技术优先。
- 核心规则服务端验证。
- 数据库承担最终一致性约束。
- 避免不必要的分布式组件。
- 决策可追溯、行为可测试。

## 2. 候选技术栈

- Python 3.12
- Django 5.2 LTS
- Django Templates + Bootstrap 5 + 少量 JavaScript
- PostgreSQL 17
- pytest + pytest-django
- Docker Compose
- Git + GitHub

以上均为候选方案，尚待团队评审。当前实现与验证状态见verification.md。

## 3. 总体架构

采用模块化单体（Modular Monolith）。

表现层：Django Templates、Bootstrap、原生 JavaScript。\
业务层：accounts、equipment、booking、audit、core。\
数据访问层：Django ORM、事务 API、必要 SQL。\
持久化层：PostgreSQL。

模块职责：
- accounts：认证、用户、角色。
- equipment：设备信息和状态。
- booking：预约、维护、并发控制。
- audit：业务操作日志。
- core：配置、公共异常、基础页面。

依赖规则：
1. accounts 不依赖预约业务。
2. equipment 不直接修改预约记录。
3. booking 使用用户和设备领域数据。
4. audit 不参与业务可否预约的判定；要求记录的写操作与日志在同一事务，日志写入失败则整体回滚。
5. 占用写操作必须经过 booking 服务层。
6. 前端不得决定预约是否冲突。
7. 数据库约束不得被绕过。

## 4. 数据模型候选

### User
使用 Django 用户模型与角色授权机制。字段包括 id、username、password、first_name、is_active、is_staff；业务 ADMIN 角色应通过明确组/权限定义，不直接等同 is_staff。

### Equipment
id、code、name、description、location、status、created_at、updated_at。code 唯一；status 为 AVAILABLE/DISABLED。

### EquipmentSlot
统一表示设备时间占用：
- id
- equipment_id
- kind（RESERVATION / MAINTENANCE）
- user_id（维护时可为空）
- start_time
- end_time
- status（ACTIVE / CANCELLED）
- reason
- created_by
- created_at
- cancelled_at

### OperationLog
id、actor_id、action、target_type、target_id、reason、created_at。

### 为什么统一 EquipmentSlot
预约和维护都占用同一设备的时间资源。分开两张表难以通过单表约束防止跨表冲突。统一表可以对所有 ACTIVE 时间占用建立一个排除约束。代价是必须进行类型字段和业务校验。

## 5. 并发一致性

### 风险
仅“先查询冲突、再插入”会发生竞态：两个事务可能同时查询到空闲，然后都插入。

### 候选双重保护
1. 业务层：`transaction.atomic()` + 设备行级锁 `select_for_update()`；锁设备后重新检查状态、维护和占用，再写入。
2. 数据库层：PostgreSQL GiST exclusion constraint，防止同一设备的 ACTIVE 占用时间重叠。

示例 SQL（待在实际 schema 上验证）：

```sql
CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE equipment_slot
ADD CONSTRAINT valid_slot_time
CHECK (start_time < end_time);

ALTER TABLE equipment_slot
ADD CONSTRAINT no_overlap_active_slots
EXCLUDE USING gist (
    equipment_id WITH =,
    tstzrange(start_time, end_time, '[)') WITH &&
)
WHERE (status = 'ACTIVE');
```

需要字段 NOT NULL 和其他类型约束，避免空值绕过规则。

时间采用半开区间 `[start_time,end_time)`。相邻预约允许：09:00–10:00 与10:00–11:00。

伪代码：

```python
def create_reservation(user, equipment_id, start, end):
    validate_request(user, start, end)
    try:
        with transaction.atomic():
            equipment = (
                Equipment.objects
                .select_for_update()
                .get(id=equipment_id)
            )
            validate_equipment_status(equipment)
            validate_time_against_current_time(start, end)
            validate_no_overlap(equipment, start, end)
            return EquipmentSlot.objects.create(
                equipment=equipment,
                kind="RESERVATION",
                user=user,
                start_time=start,
                end_time=end,
                status="ACTIVE",
                created_by=user,
            )
    except IntegrityError as exc:
        if is_overlap_constraint_violation(exc):
            raise ReservationConflict() from exc
        raise
```

这是伪代码，不可直接视为完整实现。`IntegrityError` 应在 atomic 块外捕获，只把明确的排除约束冲突转换为业务冲突，其他异常继续抛出。维护、设备停用也应使用一致锁顺序。

### 并发测试
- 真实 PostgreSQL。
- 20个独立连接并发请求。
- 同步屏障尽可能同时发起。
- 连续20轮。
- 每轮恰好1成功、19冲突。
- 最终数据库只有1条对应 ACTIVE 占用。
- 额外测试预约与维护混合竞争。

## 6. 认证与安全

候选采用 Django Session Authentication：
- MVP 使用管理员预置账户，是否开放注册待确认。
- MEMBER、ADMIN 两种业务角色。
- 服务端执行权限检查。
- 使用 Django 密码哈希。
- 启用 CSRF。
- 不提交密钥、真实账户和密码。
- 公开部署使用 HTTPS、安全 Cookie、关闭 DEBUG。

## 7. 页面结构

普通成员：
- P-01 登录
- P-02 设备列表
- P-03 设备详情与预约
- P-04 个人预约

管理员：
- P-05 设备管理
- P-06 维护管理
- P-07 预约管理

## 8. 候选接口

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | /equipment/ | 设备列表 |
| GET | /equipment/{id}/ | 设备详情 |
| GET | /equipment/{id}/schedule/ | 日程 |
| POST | /reservations/ | 创建预约 |
| GET | /reservations/mine/ | 个人预约 |
| POST | /reservations/{id}/cancel/ | 取消 |
| GET | /manage/reservations/ | 管理员查询 |
| POST | /manage/maintenance/ | 创建维护 |

状态码：400参数错误、401未认证 JSON、403无权限、404不存在、409业务冲突、201创建成功。浏览器页面可对未登录访问重定向登录页。写操作不得用 GET，必须满足 CSRF。

## 9. 目录结构候选

```text
labreserve/
├── README.md
├── .gitignore
├── .env.example
├── pyproject.toml
├── compose.yaml
├── Dockerfile
├── manage.py
├── config/
├── apps/
│   ├── accounts/
│   ├── equipment/
│   ├── booking/
│   ├── audit/
│   └── core/
├── templates/
├── static/
├── tests/
└── docs/
    ├── product-brief.md
    ├── prd.md
    ├── architecture.md
    ├── project-context.md
    ├── decision-log.md
    ├── adr/
    ├── epics/
    ├── stories/
    ├── experiment-a/
    └── retrospective.md
```

## 10. 候选 ADR（全部 PROPOSED）

### ADR-001 模块化单体
选择 Django 模块化单体；未选 React + FastAPI 前后端分离。理由：表单型业务、团队规模小、独立前后端复杂度收益不明显。代价：未来复杂客户端可能需要扩展。

### ADR-002 PostgreSQL
选择 PostgreSQL；未选 SQLite。理由：依赖 GiST 排除约束、事务和行级锁；SQLite 无法提供相同机制。代价：需管理数据库服务。

### ADR-003 统一 EquipmentSlot
选择统一预约/维护占用模型；未选 Reservation 与 Maintenance 分表。理由：统一资源时间冲突可在数据库层约束。代价：需要 kind/status 约束和业务校验。

### ADR-004 行级锁 + 数据库排除约束
选择设备行级锁、事务和 GiST 排除约束；未选仅应用层先查再插入，也暂不引入 Redis 分布式锁。理由：避免竞态，数据库兜底。代价：同设备写操作串行化，需真实并发测试。

### ADR-005 Session Authentication
选择 Django Session；未选自行实现 JWT。理由：同源 Web 应用，无需 Token 刷新和撤销体系。代价：未来独立客户端需重新评估。

### ADR-006 Docker Compose
选择 Docker Compose；未选 Kubernetes。理由：应用和数据库两个服务，Kubernetes 过度复杂。代价：不具备复杂集群调度能力。

### ADR-007 不引入异步队列
MVP 不引入 Celery/RabbitMQ；未选异步任务架构。理由：当前没有必须后台执行的长任务，预约成功必须以数据库事务提交为准。代价：复杂通知/批处理未来需扩展。

以上 ADR 不能代替真实团队评审或人机决策日志。

## 11. 追溯矩阵

- FR-01～03 → ADR-001/005 → accounts。
- FR-04～06 → ADR-001/004 → equipment。
- FR-07～10 → ADR-002/003/004 → booking、EquipmentSlot。
- FR-11～12 → ADR-003/005 → 预约状态和用户归属。
- FR-13/15 → ADR-001/005 → 管理员授权、审计。
- FR-14 → ADR-002/003/004 → 统一时间占用。
- NFR-01 → ADR-002/003/004。
- NFR-02 → ADR-005。
- NFR-03 → ADR-001/002。
- NFR-04 → ADR-001/006/007。
- NFR-05 → ADR-002/004/007。
- NFR-06 → ADR-001。

## 12. 测试架构

单元：时间区间、冲突、时长、状态转换、权限。\
集成：认证、事务、设备停用、取消后重订、维护、日志。\
并发：相同/部分重叠、20并发、预约与维护竞争、设备停用竞争、回滚。\
质量门槛：Must Have 测试通过；NFR-01/02 必须通过；无已知一致性缺陷；保留真实测试证据。

## 13. 部署

Docker Compose 管理应用和 PostgreSQL。README 写明环境、变量、数据库初始化、迁移、演示账户、启动、测试和常见问题。测试与演示数据隔离；不提交真实账户密码。

## 14. 实施顺序

1. 验证 PostgreSQL 排除约束。
2. 初始化 Django、数据库、认证。
3. 建立 Equipment 和 EquipmentSlot。
4. 实现预约业务服务。
5. 开发用户和管理员界面。
6. 完成权限、异常、并发测试。
7. 部署和验收。

**结论：** 候选方案为 Django 模块化单体 + PostgreSQL，使用事务、设备行级锁和排除约束保证时间占用一致性。团队评审与技术验证完成前，保持 PROPOSED 状态。

## 15. 生命周期规则与工程边界（PROPOSED）

取消、设备停用、维护取消统一遵循 PRD BR-07/09/10/11 与 rule-review.md；维护取消纳入原 FR-14/US-10。业务 ADMIN 使用明确 Django Group ADMIN，不等同 is_staff。工程按 accounts/equipment/booking/audit/core 划分；业务服务集中 booking。Python 3.12 保留为候选目标，本机 Python 3.13.9 的运行结果须注明版本差异。所有 Story 仍 TODO。
