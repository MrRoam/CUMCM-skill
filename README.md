# CUMCM Skills

数学建模竞赛的独立技能。两个 Skill 位于仓库根目录同一级，可以分别安装和调用，使用 modeling-team 不需要先开启 coach。

| 需要做什么 | Skill |
| --- | --- |
| 开启一轮教练定向或复盘 | [math-modeling-coach](math-modeling-coach/SKILL.md) |
| 识别本轮目的并安排分工、帮助队友接手、简明反馈成果 | [modeling-team](modeling-team/SKILL.md) |

## 从 GitHub 安装

本页对应 `main` 分支。把下面这句话发给队友的 Codex，即可通过内置 skill-installer 安装分工技能：

```text
请使用 $skill-installer 安装 https://github.com/MrRoam/CUMCM-skill/tree/main/modeling-team
```

需要同时安装教练时：

```text
请使用 $skill-installer 从 MrRoam/CUMCM-skill 的 main 分支安装 modeling-team 和 math-modeling-coach 两个 Skill。
```

默认安装到个人技能目录（通常为 `~/.codex/skills/`），下一轮对话即可使用。若已有同名技能，先让 Codex 核对来源和本地修改再更新，不直接覆盖个人修改。团队需要固定同一版本时，明确指定同一个完整 commit SHA 作为安装的 ref。

也可以取得本仓库后，将所需技能的**整个目录**复制到项目的 `.agents/skills/` 下，保留 `SKILL.md`、`references/` 和已有的 `agents/`。不要只复制一个 `SKILL.md`。

## 使用 modeling-team

- **分工**：“用 $modeling-team 看当前项目。我们这一轮想探索几种不同路线，请结合已有材料安排能各自独立推进的任务，并解释为什么这样分；目的不清楚的地方先集中问我们。”
- **接手**：“用 $modeling-team 读取仓库里的这份分工说明。我负责其中的 B 任务，先让我和 Codex 都理解共同目的、整体分工、我的起点和交付。”
- **反馈**：“我这条路线已经研究完了，用 $modeling-team 根据仓库成果整理一段给队友的简明反馈：所得、对共同问题的作用、详细记录位置，以及确实需要的配合。”

探索、排查和精修可以采用不同分法，不固定三人的身份。分工确定后，在项目已有 Markdown 中写清背景、安排及理由、个人任务和交付；详细成果留在项目仓库，反馈避免重复搬运大量材料。模型和数据的专业判断由团队或相应专业技能承担。

此仓库存放技能，具体赛题、实验和论文留在团队自己的项目中。安装完整性不代表已验证多人协作效果。
