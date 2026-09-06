# CUMCM Skills

给数学建模队伍的少量工具。沿用项目已有题意、快照、代码和论文；不另建任务平台，不保证奖项。

| 用途 | 入口 |
|---|---|
| 需要一次教练定向或复盘 | `$math-modeling-coach`，保留原有显式启动、单轮关闭方式 |
| 接队友任务、交出结果、接收模型变化或判断阶段下一步 | `$modeling-team`，支持自动按情境选用，也可直接点名 |

三个独立Codex通过项目文件和Git协作；无需连接账号，也不用固定谁永远只写代码或论文。某阶段由一人整合共享题意/论文，其余人交付能接用的成果。

## 三句就能开始

- **接活**：“用 modeling-team 接手这个项目。读取当前题意和快照，找到现在最值得我做的一项工作，明确依赖和编辑范围，然后实际推进。”
- **交接**：“把本次准备采纳的结果交给队友。核对权威文件和评价口径，生成必要的成果凭据，给复算方式及一句能写进论文的结论。不要把机器检查写成人工核验。”
- **接收**：“接收队友这次成果。先检查它是否仍适用于当前模型，完成最关键的独立核查，再更新现有快照和论文。”

Codex负责整理必要字段与执行命令，学生不必填写技术表格。人仍需实际理解、决定和核查，尤其是核心假设、目标与约束。另一个Codex检查通过不能代替人工核验。

## 安装与固定版本

在赛前取得本仓库的真实Git工作树。选择一个已检查的完整commit；三人用同一个commit。`tools/install_skills.py`无网络，只从本地Git对象安装，不把未提交改动混入版本。

将下面的 `项目目录` 换成你当前项目路径，由Codex运行。首次不带`--apply`会预览；确认已有授权后加`--apply`安装。

```powershell
$skillsRevision = git rev-parse HEAD
python tools/install_skills.py install --repo . --revision $skillsRevision --skill math-modeling-coach --skill modeling-team --dest '项目目录/.agents/skills'
```

安装后把`install`换成`verify`可检查文件与指定commit一致；更新使用`update`及新的完整commit，添加`--apply`才写入。已有人工修改或同名目录不会被静默覆盖，旧版本保留备份；同名不同位置技能不能视作自动合并。当前个人安装/junction也不会被这个命令改动。

每个Skill目录有`.skill-install.json`记录commit与文件hash。版本一致不代表方法正确；正式使用前至少在你自己的Codex里调用一次确认能发现。三个真实账号的可用性须由三位用户实际确认。

## 两个脚本各负责什么

- `tools/install_skills.py`：固定版本、完整引用资源、已有修改保护、安装后核验。
- `modeling-team/scripts/result_receipt.py`：检查已登记输入/代码/结果是否变动，读取实际指标，拒绝不同声明口径的自动排名。首次使用见[成果凭据](modeling-team/references/result-receipts.md)。它不证明数学正确、最优性、已运行或人工审查；不能漏掉主脚本调用的关键模块。

## 赛前和正式比赛

GitHub适合赛前部署与演练。2026官方规则对赛期GitHub等平台的赛题交流有限制，不自行假定私有仓库豁免。赛期保守使用本地Git和队内文件传递；方式和官方来源见[队内交接](modeling-team/references/team-transfer.md)。赛前冻结Skills，赛中不静默更新。

本仓库当前增量是经过小型演练的候选工具，不能据此推断获奖效果。[验证记录](VALIDATION.md)区分脚本检查、代理模拟、真实账号和真人理解。可运行的[离线协作练习](examples/README.md)用于检查接手是否成功。
