# 第一轮集成验收摘要

## 结论

完整测试共 146 项，实际结果为 **146 passed、0 failed、0 skipped**，耗时 68.45 秒。真实控制台输出见 `pytest.txt`，实际 JUnit 见 `tests.xml`，环境与命令见 `environment.txt`。

本证据支持相关 Story 进入 `review`，不代替指定复核人的接受结论，也不表示 Story 已为 `done`。

## Story 与证据映射

| Story | 当前建议状态 | 主要测试与证据 | 尚未覆盖或待确认 |
|---|---|---|---|
| US-01 登录和退出 | review | `tests/test_auth_web.py`；真实配置登录页测试 `tests/test_integration_web.py`；完整 JUnit | 指定复核人姚政伟待确认 |
| US-02 角色权限控制 | review | `tests/test_equipment_web.py` 中 ADMIN/MEMBER、参数篡改和 `is_staff` 测试；`tests/test_policy.py` | 指定复核人姚政伟待确认 |
| US-04 设备列表与详情 | review | `tests/test_equipment_web.py`；真实配置设备详情与预约入口集成测试 | 指定复核人姚政伟待确认 |
| US-05 设备新增与编辑 | review | `tests/test_equipment_web.py` 中新增、编辑、唯一编号、权限和状态字段保护测试 | 指定复核人姚政伟待确认 |
| US-08 创建合法预约 | review | `tests/test_reservation_rules.py`、`tests/test_reservation_web.py`、`tests/test_integration_web.py` | 30 分钟、4 小时、7 天仍为 PROPOSED；指定复核人罗永煌待确认 |
| US-09 冲突与并发保护 | review | 完整 JUnit；`docs/evidence/us09/acceptance-matrix.md`；独立 35 项验证 | 指定复核人罗永煌待确认 |
| US-12 取消个人预约 | review | `tests/test_cancellation_web.py`、`tests/test_cancellation_acceptance.py`、`tests/test_integration_web.py` | 指定复核人罗永煌待确认 |

## 真实配置流程

`tests/test_integration_web.py` 不替换生产 `ROOT_URLCONF` 或模板 Loader，覆盖：

1. 生产模板和命名路由可用。
2. 首页重定向设备列表。
3. 登录成员从设备详情进入预约，创建 ACTIVE 预约并查看详情。
4. 取消后记录变为 CANCELLED，取消入口消失，随后原时段可重订。
5. 已开始预约不显示取消表单。

US-09 的六条 AC 及 20 轮逐请求数据另见 `docs/evidence/us09/acceptance-matrix.md` 和 `docs/evidence/us09/tests.xml`。
