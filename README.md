# CUMCM 团队论文写作与可视化 Skill

本仓库共享 `cumcm-formatting`，用于辅助全国大学生数学建模竞赛（CUMCM）论文的起草、审阅、排版、可视化和提交前检查。

Skill 只组织和检查团队已经形成的论证、数据、模型与结果。它不会替团队编造模型、实验、数值结果或参考文献，也不会把优秀论文中的常见做法误写成官方硬性要求。

## 团队成员如何使用

1. 克隆或更新本仓库。
2. 在 Codex 中打开本仓库根目录或任意子目录。
3. 在任务中显式调用：

   ```text
   $cumcm-formatting 根据我们的论证大纲和已确认结果起草摘要，并列出仍缺少的证据。
   ```

   ```text
   $cumcm-formatting 审阅当前论文的假设、符号、敏感性分析、图表和排版。
   ```

   ```text
   $cumcm-formatting 检查最终 PDF 与提交材料，区分硬性违规、改进建议和人工判断。
   ```

Codex 会从仓库根目录的 `.agents/skills/` 自动发现本 Skill。当前配置允许根据任务描述自动调用，但团队首次使用或需要保证调用时，建议显式写 `$cumcm-formatting`。如果更新后没有出现，重启 Codex 再试。

## 适用任务

- 根据团队批准的大纲和证据起草或修改论文；
- 检查摘要、章节结构、段落关系、假设、符号、参数和引用；
- 设计或检查流程图、结果图、敏感性图、对比图和表格；
- 区分官方格式要求、样本规律和经验性建议；
- 对 Markdown、DOCX、PDF 论文及提交文件包执行可复现的初步审计；
- 在最终提交前记录规则版本、已执行检查和未解决事项。

它不适合独立求解与论文写作无关的数学建模问题，也不授权 Codex 擅自改变团队已经确认的数学结论。

## 建议的团队交接材料

建模成员向论文负责人交接时，尽量提供：

- 问题拆解与论证大纲；
- 数据来源、清洗规则与最终数据；
- 模型、变量、符号和参数定义；
- 已运行代码、实验设置和结果文件；
- 假设及其理由；
- 敏感性、误差、稳健性或局限性结论；
- 每个图表要证明的观点；
- 可核查的参考文献与官方规则。

缺失材料不会被静默补造，而会被列为“人工判断”或“缺少证据”。

## 文件结构

```text
.agents/skills/cumcm-formatting/
├─ SKILL.md                         # 入口、触发范围、工作模式和完成标准
├─ agents/openai.yaml               # Codex 中的名称、简介和调用策略
├─ references/
│  ├─ official-format.md            # 官方排版、匿名性与提交要求
│  ├─ writing-and-review.md         # 结构、摘要、段落、引用与审阅
│  ├─ assumptions-and-validation.md # 假设、符号、参数、敏感性和误差
│  ├─ visuals.md                    # 图表、流程图、配色与可复现视觉设计
│  ├─ evidence-boundaries.md        # 硬性规则、样本规律、建议的证据边界
│  └─ workflow-and-routing.md       # 多阶段写作和交接流程
├─ scripts/
│  ├─ audit_manuscript.py           # 论文文本与内容诊断
│  └─ audit_submission.py           # 提交文件包诊断
├─ assets/visual-style-tokens.json  # 可复用视觉样式参数
└─ evals/evals.json                 # 触发及行为评测样例
```

## 运行本地审计

以下脚本仅提供诊断，不替代人工阅读和最终 PDF 视觉检查：

```powershell
python .agents/skills/cumcm-formatting/scripts/audit_manuscript.py 论文路径
python .agents/skills/cumcm-formatting/scripts/audit_submission.py 提交文件夹路径
```

检查 Skill 包自身：

```powershell
python tools/validate_package.py
```

GitHub Actions 会在提交和拉取请求时运行同一检查。

## 更新约定

- 当年官方竞赛文件优先于仓库中的历史总结；涉及最终提交时必须重新核对最新规则。
- 修改 `SKILL.md` 的触发范围、硬性限制或审批边界，应由至少一名其他队员复核。
- 新增经验性规律时写明来源和适用范围，不把样本统计直接提升为规范。
- 不提交未获授权的优秀论文全文、截图、个人信息、账号凭据或比赛受限材料。
- 不在多个文件中重复维护同一条规则；详细内容放在对应 reference，入口文件只负责路由。

详细贡献要求见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 分发说明

本 Skill 当前以仓库级方式共享，适合三人团队在同一项目中使用。若以后需要跨多个仓库或向更多人分发，可再封装为 Codex 插件；目前没有必要增加该复杂度。

关于 Codex 发现、显式调用和仓库级 Skill 目录的说明，参见 [OpenAI 官方文档](https://developers.openai.com/codex/build-skills)。

## 许可状态

当前仓库未声明开源许可证。团队在决定公开复用或接受外部贡献前，应先选择合适的许可证并确认其中引用材料的权利边界。
