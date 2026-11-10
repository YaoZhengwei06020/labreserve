# 技术验证报告

日期：2026-11-10。范围：统一EquipmentSlot、PostgreSQL排斥约束、设备锁、事务与业务审计。

## 环境与结果

| 验证 | 环境 | 结果 |
| --- | --- | --- |
| 规则与健康检查 | Python3.13.9、Django5.2.19 | 19项通过 |
| 数据库技术验证 | Windows x64、PostgreSQL17.11、Python3.13.9 | 12项通过，13.56秒 |
| 自动检查 | Ubuntu、PostgreSQL17、Python3.12 | 31项通过，4.29秒 |
| 自动检查 | Ubuntu、PostgreSQL17、Python3.13 | 31项通过，6.44秒 |
| 编号、追踪、故事点与链接检查 | scripts/check_baseline.py | 通过 |

自动检查执行依赖安装、Django检查、迁移一致性、数据库迁移和pytest。当前运行见[GitHub Actions](https://github.com/YaoZhengwei06020/labreserve/actions)。环境与测试运行包信息见[运行包来源](evidence/postgres-runtime-source.json)。

## 数据库验证范围

- btree_gist与GiST排斥约束迁移成功；相同设备有效预约和维护共同互斥。
- 零长区间拒绝，相邻时段与不同设备允许。
- 20个独立连接连续竞争20轮：每轮1个成功、19个业务冲突，最终1条ACTIVE；后端PID去重确认连接独立，JUnit记录20条轮次属性。
- 20连接预约/维护混合竞争通过。
- 设备停用与预约创建的两种次序通过，既有占用保留，停用后新增占用被拒。
- 管理员原因、归属权限、维护取消不恢复预约、取消幂等及审计失败回滚通过。

最终数据库运行：[摘要](evidence/postgres-e2af34c359ba/summary.json)、[JUnit报告](evidence/postgres-e2af34c359ba/tests.xml)、[测试输出](evidence/postgres-e2af34c359ba/pytest.txt)。规则测试报告见[JUnit](evidence/policy-tests.xml)。隔离测试库在测试结束后清理，实例关闭记录见[生命周期证据](evidence/postgres-lifecycle.json)。

## 发现与修正

首次数据库测试9项通过、1项失败。绕过设备锁直接并发插入时，PostgreSQL以40P01死锁中止竞争事务，而初版底层测试只接受23P01排斥冲突。[首次运行摘要](evidence/postgres-52c7254ecf6e/summary.json)和[失败输出](evidence/postgres-52c7254ecf6e/pytest.txt)保留。

底层竞争测试现区分排斥冲突与死锁中止，仍要求恰好一条提交；业务服务测试保持1成功、19个SlotConflict，不将死锁计为业务冲突或成功。官方机制说明见[PostgreSQL事务失败处理](https://www.postgresql.org/docs/17/mvcc-serialization-failure-handling.html)。

## 适用边界

结果证明服务层技术方案在所列环境可运行，不代表HTTP页面、性能、重启恢复或真人可用性验收。Compose应用完整部署、实验A及Story端到端验收仍待完成。公开报告仅移除主机名元数据，测试名称、状态、时间、轮次属性与失败正文保持不变。
