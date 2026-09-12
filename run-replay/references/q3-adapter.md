# CUMCM B Q3 日志入口

对单个版本目录使用：

```text
python <skill>/scripts/adapt_q3.py --run <含actions.jsonl的目录> --output <任务产物目录>/replay-data.json --title <算法名>
python <skill>/scripts/build_replay.py --input <任务产物目录>/replay-data.json --output <当前对话可视化目录>/run-replay.html
```

适配器只读取 actions.jsonl、可选 result.json/metadata.json 与祖先三层内的 case.json/cases.json。有多个案例时按运行目录的父目录名称匹配，或显式传 --case <单案例JSON>；不能从案例列表随便取第一例。没有真值文件也能用公开状态回放。

默认几何来自技能自带 scripts/q3_state/ 的 CoverageInformationState.update(action,response)，只依赖 Python 标准库。该模块取自团队 CUMCM 项目的公开反馈状态实现（geometry.py、state.py、coverage.py），仅把原来的项目路径和顶层导入改成包内相对导入；数学和终止规则未改。不加载/执行策略choose、不启动模拟器、不向外发送动作。

运行的几何协议有变化时，可以显式传 --repo <对应版本CUMCM项目根目录>，改用该项目 experiments/b_q3/probability_patrol/coverage_state.py；这不是默认安装依赖。适配器适用于从第1步开始的完整前缀；中途截断的后缀必须另提供正确初始状态，不能冒充原点出发。

默认按记录解释，无信号是该频道的真实测量反馈，不能用未执行的计划圆证明覆盖。参数来自这一项目已确认协议：区域1800米、保证接收1000米、最大接收1500米、清除20米、方向约束1.005度（含取整余量）；任务协议不同先调整适配器，不沿用这些常数。

常见reason映射是规则解释，不是重新证明每步决策，文字中注明“规则说明”。metadata中带 refinement_decisions 的记录附上真实选择及预测节省。其他决策记录需按实际结构补充适配，不能把F3理由套给POMDP或baseline。运行源码相较日志版本有变化时，应使用该运行对应的状态重建器或明确说明无法完全还原。

输入可以是未完成运行；终点展示“记录结束/未确认完成”。result.json.success=true 而公开状态不完整、时间不一致时适配报错，保留错误并查明来源。
