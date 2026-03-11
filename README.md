# Slay the Spire - Ironclad Battle Simulator

基于 Python 的杀戮尖塔战斗模拟器，用于逆向分析游戏数值平衡。

## 项目概述

本项目通过代码化复现的方式，将游戏机制转化为精确的 Python 逻辑，实现以下目标：

1. **机制逻辑的代码化复现** - 将模糊游戏规则转化为精确的状态机模型
2. **数值平衡的边际推演** - 分析单点能量转化率，发现设计意图
3. **AI 行为树的意图重构** - 逆向编写怪物行为算法
4. **压力测试下的设计盲区探测** - 万次模拟剥离随机性

## 核心功能

### 战斗模拟器 (`sts_simulator.py`)
- Entity / Card 类定义
- 力量 (Strength) 伤害计算: `FinalDamage = BaseDamage + Strength`
- 易伤 (Vulnerable) 结算优先级
- 回合制格挡重置机制
- Lagavulin 敌人行为树实现

### 卡牌数据 (`ironclad_master_data.json`)
- 铁甲战士 57 张卡牌 (Common + Uncommon)
- 完整字段：名称、能耗、伤害、格挡、效果

### 实验结果

| 实验 | 结果 |
|------|------|
| 力量流卡组 (5000场) | 胜率 100%，平均回合 3.9 |
| Lagavulin 对抗 (困难模式) | B组力量组 100% 胜率 |
| DPE 衰减分析 | 软狂暴阈值: 第3次虹吸前 |

## 关键发现

### 伤害公式
```
FinalDamage = ⌊(BaseDamage + Strength) × VulnerableMultiplier⌋
```

### 乐嘉维林 (Lagavulin) 设计分析
- **软狂暴**: 必须在第3次灵魂虹吸前结束战斗
- **双向削弱**: 同时降低力量和敏捷，限制单一 build
- **金刚杵价值**: +1 力量可减少 5-8% 损血

## 文件结构

```
.
├── ironclad_master_data.json    # 卡牌数据
├── sts_simulator.py            # 战斗模拟器
├── sim_results.csv             # 5000场战斗结果
├── deck_comparison.csv         # 卡组对比实验
├── dpe_decay.png              # DPE衰减曲线图
└── lagavulin_analysis_report.md # 数值平衡分析报告
```

## 使用方法

```python
from sts_simulator import Entity, Card, apply_card, BattleSim

# 创建角色
player = Entity(name="Ironclad", hp=80, strength=3)
enemy = Entity(name="Monster", hp=50)

# 使用卡牌
result = apply_card(strike_card, player, enemy)
print(result)
```

## 技术栈

- Python 3.9+
- JSON (卡牌数据)
- Matplotlib / Seaborn (可视化)
- Scipy (数值分析)

---

*逆向工程学习项目，仅供研究参考*
