# 协作、分阶段提交与合并

执行安排日期：2026-11-11。适用于两轮Sprint；成员确认与排期待完成。本文是后续执行约定，不是已发生的团队评审记录。

## 分工与开发阶段

姚政伟负责需求统筹、过程文档、集成、交付与US-13；郑焰负责认证、权限与设备基础；刘昊文负责预约、并发一致性与取消；罗永煌负责日程、维护、测试与实验组织。成员在各自任务分支开展工作，通过PR进行交叉复核和集成。

每个开发阶段明确前置依赖、实现范围、验证步骤和验收条件。提交应能说明实际改动及其验证结果，未覆盖的验收条件在Story卡和PR中保留。

以下划分是工作边界，没有固定提交次数指标。一个阶段可以因真实复核而产生多次提交；不提交空改动，不倒填时间，也不把同一完整成果复制成多人的重复贡献。

| 成员 | 阶段 | 交付与检查边界 |
| --- | --- | --- |
| 郑焰 | ZY-01 / US-01 | 登录、退出及对应请求测试，先验证会话与安全跳转 |
| 郑焰 | ZY-02 / US-02 | 服务端角色权限、普通成员与ADMIN、is_staff区别及越权测试 |
| 郑焰 | ZY-03 / US-04 | 设备列表、详情、空状态与不存在设备处理 |
| 郑焰 | ZY-04 / US-05 | 设备新增编辑、字段校验与权限回归；不绕过启停服务修改设备状态 |
| 郑焰 | ZY-05 / US-03、06 | Sprint2当前用户信息和设备启停界面，接入已有事务服务 |
| 刘昊文 | LH-01 / US-08 | 预约表单和请求入口，接入统一服务；FR-10时间参数待批准，未批准不报完整验收 |
| 刘昊文 | LH-02 / US-09 | HTTP冲突反馈、真实PostgreSQL17并发回归与证据；保留设备锁、排斥约束和审计 |
| 刘昊文 | LH-03 / US-12 | 个人取消入口、归属/开始时间/幂等测试及错误反馈 |
| 罗永煌 | LY-01 / US-08、09复核 | 独立复现预约与并发测试，记录实际结果；发现问题时增加回归测试或提出具体复核意见 |
| 罗永煌 | LY-02 / US-07 | 设备日程、相邻时段及预约/维护展示测试 |
| 罗永煌 | LY-03 / US-10 | 维护创建与取消、权限和冲突回归；不自动取消预约或恢复历史记录 |
| 罗永煌 | LY-04 / US-11 | 个人预约列表、隔离权限与取消后状态展示 |
| 罗永煌 | LY-05 / 实验A | 冻结实验方案、真实执行、原始数据及分析；实验前单独核对对照任务和操作者 |

跨成员依赖：认证与设备基础先集成，预约入口再接入；日程和个人预约依赖预约入口。罗永煌可先审阅和复现已有技术spike，不能把复现写成自己实现了该spike。实验A在正式采样前核对任务可比性，避免把已看到完整实现的任务当作无规划对照。

## 提交与PR

1. 从最新main建立阶段分支，例如`feat/zy-us01-login`、`feat/lh-us08-reservation`、`test/ly-us09-concurrency-review`。已有分支继续工作前先确认依赖已合并。
2. 用自己的GitHub账号和与该账号关联的提交邮箱。提交只包含本阶段实际检查过的文件，不上传数据库目录、运行包、凭据或原始聊天导出。
3. 改动和相关测试形成有意义的一次提交，例如`feat(US-01): add login and logout`。真实测试记录、复核修正可另提交，不要求为了次数拆开必须同时生效的实现与测试。
4. 推送阶段分支并创建PR，注明Story、需求、依赖、实现范围、AI辅助、实际运行的检查、结果与未完成项。测试未运行时填写原因，保留“未运行”，不能使用预设通过结论。
5. 由`sprint-status.yaml`指定的另一位成员复核。PR评论记清实际检查项和结论；有问题就在同一分支修正，保留实际修订记录。
6. 集成者确认检查与复核后使用GitHub的`Create a merge commit`合并，保留阶段分支的各次提交。不要将这些过程提交Squash为一条；未配置允许merge commit时先调整合并设置，不用改写作者或历史解决。本文未更改仓库设置。

GitHub Desktop支持按相关文件或改动选择提交，具体界面见[官方提交教程](https://docs.github.com/en/desktop/making-changes-in-a-branch/committing-and-reviewing-changes-to-your-project-in-github-desktop)。普通合并保留分支提交、Squash将其合为一条，见[官方合并方式说明](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/about-merge-methods-on-github)。

## 冲刺状态随真实进展提交

`sprint-status.yaml`是跟踪主文件；Story卡和原生BMAD的`development_status`同步更新。状态变化与对应工作同次提交或在真实复核发生后另一次提交，不预先生成整轮冲刺的状态历史。

| 真实事件 | 状态与提交内容 |
| --- | --- |
| 就绪检查完成，未决规则已足够支持该Story开发 | `draft → ready-for-dev`；BMAD从`backlog → ready-for-dev`，记录就绪依据 |
| 负责人实际开始工作 | `ready-for-dev → in-progress`；记录当前范围和依赖 |
| 可复现实现及本阶段检查完成，提交独立复核 | `in-progress → review`；附证据，未覆盖AC明确保留 |
| 指定复核人确认全部AC，证据可追踪 | `review → done`；填写`acceptance_evidence`与真实复核结论 |
| 发现验收缺口 | 保留问题证据，按实际情况退回`in-progress`或继续`review`；不得直接补写通过 |

部分子阶段交付不等于整个Story完成；跨阶段工作未覆盖全部AC时不能标done。只有过程任务发生变化时，只更新`process_tasks`和时间，不抬高Story状态。当前13条Story仍为draft/backlog。

每次更新填实际日期与`last_updated`。负责人更新自己Story的状态与卡片，姚政伟负责冲突协调和集成状态，复核结论由实际复核人填写。所有人都修改同一个YAML时，后一个PR以最新main核对并保留前一个PR的变更，避免覆盖其他成员的状态更新。

## 集成与证据核对

合并前运行`python scripts/check_baseline.py`、`python scripts/check_project_process.py`及相关测试；涉及数据库时使用真实PostgreSQL17。核对GitHub Actions的具体运行，区分本地结果与CI结果。基线结构检查通过不代表Story或作业已完成。

保留PR的Commits、Files changed、复核意见、检查运行及`sprint-status.yaml`的文件历史。可用`git log --all --date=iso --format="%h %ad %an %s" -- sprint-status.yaml`核对状态文件历次提交。贡献分布结合实际产物和复核内容判断，不按行数、提交数或贡献图颜色代替质量评价。

仓库协作者账号尚未收集。账号与写权限就绪后按协作仓库方式提交；暂未获得写权限时可用个人fork发PR，不能借用其他人的账号。尚未邀请成员或更改仓库权限。
