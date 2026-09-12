# 回放数据约定

build_replay.py 接受一个 UTF-8 JSON 对象。已有本项目 view_data.json 可直接读取；字段名沿用其格式。渲染器只处理数据，不运行策略。

## 核心字段

- case: name、seed 可选；sources 为可选真值列表 `{channel:整数, position:[x,y], radius:接收半径(可选)}`。无真值用空列表。
- frames: 初始状态加每步更新后的状态。每帧 `{q:[x,y],time:累计秒数,complete:bool,seen:[历史发现的频道],channels:[频道状态]}`。
- 频道状态：`{j:整数,status:"unknown"|"found"|"cleared"|"absent"}`。found 状态可以提供 center:[x,y], radius:包围半径, polygon:[[x,y],...]。未提供几何时不显示几何；radius 表示包围圆尺度，不是概率可信度。
- actions: 与帧一一对应的 `{kind:"measure"|"clear"|"move",position:[x,y],channel:整数,result:反馈代码,bearing:角度或null}`。
- single: 每条动作的讲解，`{start:i,end:i,title,action,feedback,why,focus:频道或0}`，i从1开始。文字无HTML，渲染时用textContent。
- groups: 同样的讲解结构，start/end 包含分组的全部原始步骤。所有组必须不重不漏覆盖1…N；切换查看方式仍以真实步骤对应。

## 场景参数（scene，可选）

domain_radius、coverage_radius、clear_radius、bearing_length、angle_error_deg 是真实模型参数。unit 默认“米”，agent_label 默认“机器狗”。默认不画未知参数对应的圆或扇形。数据中的 x/y 和半径必须使用同一单位。time 固定以秒存储；界面显示分钟。

note 说明场景假设/数据缺失，initial_why 说明初始状态，title 提供默认标题。无给定 domain_radius 时按全部记录坐标自动确定视窗。适配器应总是显式写 scene，避免不同任务误用 Q3 参数。

旧版 Q3 view_data 缺 scene 时，可用渲染器 --q3-defaults 显式启用 Q3 半径与误差参数。不要对其他任务使用这个选项。

## 可选候选比较

options: `{name,q:[x,y],channels:测量频道数,mean:预计后续分钟,selected:bool}`；first_end 是这些候选真正可见的步骤。没有完整候选记录就用空列表，不能从结果倒推出候选。provenance 可以记录输入文件、哈希、重建器和理由来源，渲染不执行这些内容。

## 原始数据不足

只有位置/动作记录时，可以形成轨迹和动作回放，但需要适配器明确写出“未记录几何/理由”，不能编造多边形、未观测源或算法动机。缺少累计时间时，只有明确收费规则才可复算；否则先向用户指出这个具体缺口。
