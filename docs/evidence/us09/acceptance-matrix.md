# US-09 独立验收矩阵

## 结论与执行摘要

- **结论：通过，建议进入人工复核。** 本次指定的 35 项测试全部通过，无失败、错误或跳过。
- 被测提交：`a195203048cd2741038ab473ca3b312bc17b1379`（预期短 SHA：`a195203`，匹配）。
- 分支：`feat/integration-reservation-flow`；测试前工作区干净。
- 实际数据库：PostgreSQL 17.11，`localhost:55432`，Django 后端为 `django.db.backends.postgresql`。
- JUnit 时间戳：`2026-11-24T10:55:18.618115+08:00`。
- 收集 35 项：通过 35、失败 0、错误 0、跳过 0；控制台总耗时 19.83 秒，JUnit `time="19.784"`。
- 本报告只覆盖用户指定的三个测试文件，**不代表本次重新运行了完整 146 项测试**。

## 实际执行命令

工作目录：`E:\project\labreserve\.worktrees\integration`

```bash
set -o pipefail; POSTGRES_PORT=55432 ../../.venv/Scripts/python.exe -m pytest tests/test_us09_http_independent.py tests/test_us09_independent.py tests/test_integration_web.py --junitxml=docs/evidence/us09/tests.xml 2>&1 | tee docs/evidence/us09/pytest.txt
```

真实控制台结果：

```text
collected 35 items
tests\test_integration_web.py ....                                       [ 11%]
tests\test_us09_http_independent.py ............                         [ 45%]
tests\test_us09_independent.py ...................                       [100%]
============================= 35 passed in 19.83s =============================
```

分项数量：`test_integration_web.py` 4 项、`test_us09_http_independent.py` 12 项、`test_us09_independent.py` 19 项，合计 35 项。完整原始输出见 `pytest.txt`；本次实际生成的 JUnit 见 `tests.xml`；版本与端口见 `environment.txt`。

## 六条 AC 逐项结果

| AC | 结果 | 对应实际测试 | 代码行为与本次证据 |
|---|---|---|---|
| AC1：09:00–11:00 已存在，09:00–11:00 申请拒绝 | **通过** | `test_overlap_variants_rejected_without_partial_writes[exact]`；`test_http_overlap_returns_409_without_success_writes[exact]` | 服务层以相同起止时间创建竞争预约并断言 `SlotConflict`；HTTP 层断言 409。两层均断言占用记录仍只有 1 条、创建审计仍只有 1 条，无额外成功写入。对应 JUnit testcase 均无失败。 |
| AC2：09:00–11:00 已存在，10:00–12:00 申请拒绝 | **通过** | `test_overlap_variants_rejected_without_partial_writes[extends-right]`；`test_http_overlap_returns_409_without_success_writes[partial-right]` | 候选时段从既有时段中点后一小时开始并向右延伸，服务层断言业务冲突、HTTP 层断言 409，且没有部分写入。另有 `extends-left`、`covers-existing`、`inside-existing` 和 HTTP `partial-left` 覆盖其他重叠方向，均通过。 |
| AC3：09:00–11:00 已存在，11:00–12:00 在其他条件合法时成功 | **通过** | `test_half_open_adjacency_and_different_equipment_are_allowed`；`test_http_adjacent_reservation_returns_303_and_persists` | 服务层创建前、后相邻预约并断言共 4 条 ACTIVE（含不同设备场景）；HTTP 层对结束点等于开始点的相邻预约断言 303、ACTIVE 持久化且总数为 2。对应 JUnit testcase 通过。 |
| AC4：20 个独立请求竞争同一空闲时段，恰好 1 成功、19 业务冲突，最终只有 1 条对应 ACTIVE | **通过** | `test_nfr01_twenty_independent_connections_for_twenty_rounds` | 每轮提交 20 个 `RESERVATION` 请求；代码断言 20 个不同 `pg_backend_pid`、1 个 `success`、19 个 `business_conflict`。随后查询数据库，断言该设备只有 1 条 ACTIVE、自连接重叠计数为 0、总槽位数为 1、创建审计为 1。JUnit 的 20 组轮次属性均符合这些数值。 |
| AC5：连续 20 轮，每轮满足 AC4 | **通过** | `test_nfr01_twenty_independent_connections_for_twenty_rounds` | 测试代码使用 `for round_index in range(20)` 连续执行；每轮使用新设备并重复全部断言。`tests.xml` 中实际存在 `round_01` 至 `round_20` 共 20 组属性，20/20 轮均为 20 个不同后端 PID、1 成功、19 业务冲突、1 ACTIVE、1 创建审计。逐轮摘要见下表。 |
| AC6：绕过应用层查询的非法重叠写入仍被数据库约束阻止 | **通过** | `test_direct_illegal_overlap_is_stopped_by_database`；补充：`test_direct_database_race_distinguishes_constraint_errors_and_deadlocks` | 第一项直接调用 `EquipmentSlot.objects.create` 写入重叠 ACTIVE，不经过 `create_slot` 应用层冲突查询；断言 `IntegrityError`、约束名 `slot_no_active_overlap`、SQLSTATE `23P01`，并断言无额外记录或审计。补充直接数据库竞争用例也通过，并最终断言仅 1 条 ACTIVE 且无重叠。 |

## 20 轮并发结果摘要

以下来自本次 `tests.xml` 的 `round_01` 至 `round_20` 属性；“实际唯一 PID”由每个 `requests` 数组中的 `pid` 重新计算，而非只读取汇总字段。

| 轮次 | 请求数 | 记录的不同后端 PID | 实际唯一 PID | 成功 | 业务冲突 | ACTIVE | 创建审计 | 结果 |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| 01 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 02 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 03 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 04 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 05 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 06 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 07 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 08 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 09 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 10 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 11 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 12 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 13 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 14 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 15 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 16 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 17 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 18 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 19 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |
| 20 | 20 | 20 | 20 | 1 | 19 | 1 | 1 | 通过 |

独立连接与数据库状态的代码核验位置：

- `tests/test_us09_independent.py:39-40`：断言数据库 vendor 为 `postgresql`，版本为 PostgreSQL 17。
- `tests/test_us09_independent.py:247-306`：每个 worker 使用线程本地 Django 连接，执行 `SELECT pg_backend_pid()`，通过 `Barrier` 同步竞争，并断言 20 个后端 PID 全部不同。
- `tests/test_us09_independent.py:309-331`：数据库查询断言单条 ACTIVE 和 ACTIVE 间重叠数为 0。
- `tests/test_us09_independent.py:334-368`：连续 20 轮、每轮 20 个预约请求及 1/19/1/1 断言，并将每个请求结果写入 JUnit 属性。

## 真实配置集成流程结果

| 范围 | 对应实际测试 | 结果 | 验证内容 |
|---|---|---|---|
| 真实配置、模板与命名路由 | `test_real_configuration_loads_templates_and_named_routes` | **通过** | pytest 明确加载 `config.settings`；测试实际加载 `base.html`、设备列表、预约表单和预约详情模板，访问登录页返回 200，并断言 `/reservations/new/`、`/reservations/`、`/reservations/1/cancel/` 命名路由。 |
| 预约→取消→重订完整流程 | `test_complete_reservation_cancel_and_rebook_flow` | **通过** | 登录成员后访问设备详情和预约表单均为 200；提交预约返回 303 并持久化 ACTIVE；详情页包含取消入口；取消返回 303，记录变为 CANCELLED 且取消审计为 1；取消后的详情不再显示取消表单；使用相同时段重订返回 303，最终总记录 2 条，其中 ACTIVE 1 条、CANCELLED 1 条。 |
| HTTP 取消、重复取消与重订回归 | `test_http_cancel_rebooking_and_repeat_cancel_regressions` | **通过** | 额外验证重复取消不覆盖首次取消时间、操作者、原因和审计，随后相同时段可重订且仅有 1 条 ACTIVE。 |

## 证据文件

- `environment.txt`：实际日期、提交、分支、测试前工作区状态、OS、Python、Django、PostgreSQL 和端口。
- `pytest.txt`：本次真实完整控制台输出。
- `tests.xml`：本次 pytest 实际生成的 JUnit，含 35 个 testcase 和 20 轮逐请求并发属性。
- `acceptance-matrix.md`：本逐项验收矩阵。
