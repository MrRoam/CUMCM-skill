# 结果凭据：给队友一份可检查的结果来源

凭据保存结果来自哪些文件和JSON字段。它不运行计算，也不证明数学正确、最优、可行或已经人工审核。`check`通过，只表示已登记的内容与封存时一致。

## 先看实际计算用了什么

由Codex从代码和真实运行配置生成spec，学生不用抄大表。必须登记：

- `inputs`：实际使用的原始数据及相关处理数据。
- `evaluators`：评价入口，以及它调用的本地物理、预处理等模块；影响评价的配置和实际依赖版本（如锁文件）也要覆盖。
- `evaluation`：影响可比性的字段，如目标定义、约束、单位口径、平均规则、验证划分、物理假设和数值精度。用JSON Pointer引用实际值。
- `candidate`：待评价的具体方案、布局、预测结果等；`run`：种子、搜索算法、日志等运行记录。

不要只登记`model.py`而漏掉它导入的`physics.py`。工具不自动扫描依赖；未检查登记覆盖时，最多声称“已登记文件一致”，不能声称“模型相同”。依赖版本从实际环境取得，不能填想当然的版本。

候选和种子不同通常不阻止比较，但修改评价器精度、数据划分或假设必须反映到比较口径。一个配置文件混有这两类字段时，用`evaluation`选出影响评价的字段，整个文件仍可放在`run`中追溯。

## 小例子

假定项目内已有`data.csv`、`model.py`、它调用的`physics.py`、实际依赖锁`requirements-lock.txt`、`candidate.json`和`result.json`。结果文件中`evaluation`保存完整评价口径，`score`是数值，`unit`是单位。将下面保存为`spec.json`：

```json
{
  "inputs": {"data": "data.csv"},
  "evaluators": {
    "entry": "model.py", "physics": "physics.py",
    "dependencies": "requirements-lock.txt"
  },
  "candidate": {"plan": "candidate.json"},
  "run": {},
  "evaluation": {
    "contract": {"path": "result.json", "pointer": "/evaluation"}
  },
  "metrics": {
    "score": {
      "path": "result.json", "pointer": "/score",
      "unit": {"path": "result.json", "pointer": "/unit"},
      "direction": "max"
    }
  }
}
```

`direction`可以是`max`或`min`；单位也可直接写字符串，但那只是声明，工具不会推断它是否正确。指向整个JSON对象时`pointer`填空字符串。所有路径相对项目根目录，不允许越界。

下面以工具已位于当前目录为例；实际安装位置不同时替换脚本路径：

```text
python result_receipt.py seal spec.json --root PROJECT --out receipt.json
python result_receipt.py check receipt.json --root PROJECT
python result_receipt.py compare receipt.json --root PROJECT --other receipt_b.json
```

第二份凭据在另一克隆时，另加`--other-root OTHER_PROJECT`。封存不覆盖已有文件；失败退出码为2。

## 比较失败时怎么办

评价参数或指标单位确实不同：先解释区别，统一评价口径后复算，再比较。

登记文件哈希不同：只说明字节变了，注释和格式调整也会触发。工具无法自动确认数学含义是否等价；查看diff，或将候选放到同一评价器/数据版本复算。不要把这种拒绝说成已经证明两个模型不同，也没有`force`绕过选项。

文件变更后，旧凭据校验失败是正常的。**不能只给旧结果重新盖上新代码哈希，冒充用新代码复算。**先实际重跑相关计算和检查，生成对应结果后再封存。凭据只能检查声明，无法证明一条未发生的运行。

若只改变候选或随机种子，保留各自凭据，确认共同评价文件和`evaluation`字段一致后比较。数值有高低仍不自动代表统计显著、方案可行或全局最优。
