# LabReserve · 实验室共享设备预约管理系统

[GitHub仓库](https://github.com/YaoZhengwei06020/labreserve) · [自动检查](https://github.com/YaoZhengwei06020/labreserve/actions)

《软件工程管理》课程项目，面向实验室成员和设备管理员，提供设备查询、预约、取消及维护管理。采用模块化单体架构，技术候选为Django 5.2 LTS、Django Templates/Bootstrap 5、PostgreSQL 17、pytest及Docker Compose。

当前处于工程初始化与技术验证阶段。统一设备占用模型、事务服务、数据库迁移和测试已建立；登录、设备与预约页面尚待开发。架构决策保持PROPOSED，13条Story均待完成。

## 项目文档

- [产品简报](docs/product-brief.md)、[PRD](docs/prd.md)、[架构设计](docs/architecture.md)
- [4个Epic与13条Story](docs/epics-and-stories.md)、[需求追踪](docs/traceability.md)
- [7条候选ADR](docs/adr/README.md)、[12条项目规则](docs/project-context.md)
- [业务规则一致性审查](docs/rule-review.md)、[当前进度](docs/project-state.md)
- [技术验证报告](docs/verification.md)、[技术验证范围](docs/technical-spike.md)
- [课程要求](docs/course-requirements.md)、[实验A计划](docs/experiment-a/README.md)
- [决策日志](docs/decision-log.md)、[AI使用说明](docs/ai-usage.md)

## 工程结构

```text
apps/accounts/      角色授权策略
apps/equipment/     设备模型与迁移
apps/booking/       统一占用模型及创建、取消、启停事务服务
apps/audit/         业务操作日志
apps/core/          公共模块
config/             Django配置与进程健康检查
tests/              规则、数据库约束及并发测试
scripts/            项目基线检查与数据库验证入口
.github/workflows/  自动检查配置
docs/               项目规划、评审与验证材料
```

## 开发环境

建议Python 3.12、PostgreSQL 17；自动检查覆盖Python 3.12和3.13。Compose提供开发用应用和数据库服务。

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
Copy-Item .env.example .env
docker compose up -d db
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py check
.\.venv\Scripts\python -m pytest
.\.venv\Scripts\python scripts/check_baseline.py
```

Django宿主进程从环境变量读取数据库参数，Compose从.env读取配置；参数变更时需同步设置POSTGRES_DB/USER/PASSWORD/HOST/PORT。示例密码只用于隔离开发环境，真实凭据不得提交。

完整容器方式：`docker compose up -d --build`，再运行`docker compose exec app python manage.py migrate`与`docker compose exec app python -m pytest`。开发端口仅绑定127.0.0.1。`/health/`只表示进程响应，不能代替数据库健康检查。runserver用于开发。

已有PostgreSQL17时，设置连接环境变量后运行`python scripts/verify_postgres.py`，可执行版本预检、唯一命名临时库测试并生成报告；测试角色需具备建库和扩展权限。

## 验证与实施计划

规则测试19项、PostgreSQL17.11隔离测试12项已通过；GitHub自动检查的Python3.12/3.13两组各31项测试通过。验证覆盖20独立连接连续20轮、预约维护互斥及事务回滚，详见验证报告。

Sprint1：登录、权限、设备基础与预约闭环；Sprint2：日程、维护、个人预约、取消和管理员功能。30分钟/4小时/7天参数、时区及其他待定规则由团队评审后定稿。实验A独立开展并保留真实结果。
