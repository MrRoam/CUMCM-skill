# 队内交接：GitHub赛前与离线赛期

仅在跨队员传递代码/成果时读取。本文件不创造参赛规则；正式参赛仍须核对当届官方通知。

2026参赛规则第5条明确列出GitHub等交流平台，未看到私有队内库豁免。赛前可在GitHub协作和安装技能；正式赛期采用本地Git、U盘或队内文件传递是这里的保守方案，不是组委会专门认证。原文：https://www.mcm.edu.cn/html_cn/node/9d8e511fe7a1447b35f53a82c908e2e0.html

2026 AI规定允许辅助使用智能体，但核心建模分析由团队主导、采纳内容须人工核验。AI使用详情PDF从真实项目记录整理，不能让机器代填“已人工核验”。原文：https://www.mcm.edu.cn/html_cn/node/fef94648f2836ab6cc81586f4c38512b.html

## 小项目的离线传递

由Codex执行下列Git操作；学生只需知道给谁、交什么、是否接收。不要求学生记命令。先查看`git status`、当前分支和双方共同提交；有无关改动时保留它们，不自动stash、reset或覆盖。

发送者在自己的任务分支提交本次相关文件。完整分支bundle包含该分支可达历史，不限最新文件；若有敏感内容、巨大数据或身份信息，不盲目打包。只传代码、必要数据和可复算小结果，官方原件按队内约定保持只读。

首次分享示例（名字按实际替换，输出应位于仓库外的受管交换目录）：

```sh
git bundle create /path/to/exchange/solver.bundle task/solver
git bundle verify /path/to/exchange/solver.bundle
```

接收方先核对来源及bundle内容，取到单独的远程引用后看差异，不直接覆盖当前分支：

```sh
git bundle verify /path/to/exchange/solver.bundle
git fetch /path/to/exchange/solver.bundle task/solver:refs/remotes/team/solver
git log --oneline HEAD..refs/remotes/team/solver
git diff HEAD...refs/remotes/team/solver
```

在集成分支复核依赖与成果凭据，再运行有关检查，满足当前目标才合并。冲突要理解双方意图，不一律选ours/theirs。多人同时改变指标单位、模型假设或论文源稿时，先统一语义，再解决文本冲突。

双方已有共同提交且历史很大时，可创建增量bundle；先验证接收者确有所有前置提交，否则提供完整必要历史。比赛开始前演练一次首次传递和一次依赖变更后的接收即可，不需要自行搭建服务器。

版本一致性优先于“更新到最新”：技能在赛前固定到明确commit，比赛中不后台静默更新。更新时显示差异、保留本地修改，重新做受影响的最小演练。
