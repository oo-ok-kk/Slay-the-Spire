# Slay the Spire - Ironclad Battle Simulator

基于 Python 的杀戮尖塔战斗模拟器，用于逆向分析游戏数值平衡。

## 项目概述

本项目通过代码化复现的方式，将游戏机制转化为精确的 Python 逻辑，实现以下目标：

1. **规则的数字化重构** - 将非公开的战斗逻辑转化为精确代码
2. **规模化模拟实验** - 蒙特卡洛模拟上万场战斗，排除运气干扰
3. **数值平衡性审计** - 揭示设计师的"数值陷阱"与"生存门槛"
4. **可运行产出** - 提供模拟脚本 + 可视化报告

## 核心功能

### 1. 规则的数字化重构
- 从 JSON 文件提取卡牌和怪物原始属性
- 复刻核心数值计算引擎
- 力量伤害公式: $FinalDamage = BaseDamage + Strength$
- 格挡衰减、状态逻辑等完整实现

### 2. 规模化模拟实验
- 蒙特卡洛模拟 (5,000+ 场战斗)
- 多构筑对比 (力量流/爆发流/防御流)
- CSV 实时记录: 回合数、血量、能量效率

### 3. 数值平衡性审计
- 软狂暴计时器分析
- 资源价值重估 (燃烧之血)
- DPE 衰减曲线可视化

## 关键发现

### 伤害公式
$$FinalDamage = \lfloor (BaseDamage + Strength) \times VulnerableMultiplier \rfloor$$

### 乐嘉维林 (Lagavulin) 分析
| 指标 | 数值 |
|------|------|
| 软狂暴阈值 | 第3次灵魂虹吸前 |
| 力量组胜率 | 100% |
| 数值冗余度 | ~15% |

### 核心结论
- **HP as a Resource**: 燃烧之血6HP允许"零防御、全爆发"策略
- **力量增长函数**: $Damage \propto Strength \times Cards\_Played$
- **防御方差**: BPE < 4.0 时进入"数值死锁"

## 文件结构

```
.
├── README.md                       # 项目总览
├── ironclad_master_data.json      # 57张卡牌数据
├── sts_simulator.py                # 战斗模拟器
├── sim_results.csv                 # 5000场战斗结果
├── deck_comparison.csv            # 卡组对比实验
├── dpe_decay.png                  # DPE衰减曲线图
└── lagavulin_analysis_report.md    # 数值平衡审计报告
```

## 使用方法

```python
from sts_simulator import Entity, Card, apply_card, BattleSim

# 创建角色
player = Entity(name="Ironclad", hp=80, strength=3)
enemy = Entity(name="Monster", hp=50)

# 使用卡牌
result = apply_card(strike_card, player, enemy)
print(result)  # {'damage_dealt': 9, ...}
```

## 技术栈

- Python 3.9+
- JSON (卡牌数据)
- Matplotlib / Seaborn (可视化)
- Scipy (数值分析)

---

*逆向工程学习项目，仅供研究参考*
