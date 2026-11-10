# BMAD工具配置

目标版本：课程参考的BMAD Method 6.12.1。模块范围：核心与BMad Method（bmm），暂不引入TEA或bmb扩展。

实际安装日期：2026-11-10。core和bmm均为6.12.1，Codex共29个技能入口；uv 0.13.7已配置。已执行官方resolve_customization、resolve_config、sprint_plan validate和sprint_plan status；冲刺文件校验结果valid=true，未发现未知键或非法状态。[机器可读证据](evidence/bmad-setup.json)记录版本、配置和校验结果。

现有规划文件沿用docs目录，安装过程不得覆盖PRD、ADR或Story。工作流结果应明确输入、工具版本、执行时间、输出及审核状态；保留PROPOSED和待评审状态，避免将工具输出直接计为团队决策。

项目元数据中的draft对应BMAD的backlog。独立卡存在不表示通过开发就绪评审；两套状态由项目校验脚本交叉核对。根目录保留课程要求的sprint-status.yaml，BMAD implementation_artifacts配置为项目根目录，Story位置为docs/stories。

## 可复现安装

前置条件：Node.js20.12+、npm/npx、uv与Python3.11+。在PowerShell中运行`./scripts/setup_bmad.ps1`，安装器锁定6.12.1；团队覆盖配置保存在`_bmad/custom/config.toml`。生成的工具运行文件及本机技能入口不纳入版本控制，项目规划、Story、冲刺状态与证据正常入库。

本次依赖下载采用pip下载官方声明的ruamel.yaml依赖，再由uv从本地wheel缓存离线执行原脚本，未修改官方校验器。[官方安装说明](https://docs.bmad-method.org/start/install-bmad/)中稳定版v6.12与v7预览版路径不同，本项目不切换到预览版。

安装和格式校验已完成；PRD评审、架构批准、bmad-build实施和实验A仍需按实际发生分别记录。当前开发就绪结论见[就绪检查](reviews/implementation-readiness.md)。
