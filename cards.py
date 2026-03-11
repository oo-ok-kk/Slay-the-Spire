"""
Slay the Spire - Ironclad Card Library
铁甲战士卡牌库 - 支持力量与易伤机制计算
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Callable
from enum import Enum
import json


class Rarity(Enum):
    STARTER = "Starter"
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"


class CardType(Enum):
    ATTACK = "Attack"
    SKILL = "Skill"
    POWER = "Power"


class StatusEffect:
    """状态效果基类"""
    def __init__(self, name: str, duration: int = 1):
        self.name = name
        self.duration = duration
    
    def __repr__(self):
        return f"{self.name}({self.duration})"


class Vulnerable(StatusEffect):
    """易伤状态 - 受到伤害增加50%"""
    def __init__(self, duration: int = 3):
        super().__init__("Vulnerable", duration)
    
    @property
    def damage_multiplier(self) -> float:
        """易伤时伤害倍率 = 1.5"""
        return 1.5


class Weak(StatusEffect):
    """虚弱状态 - 力量给的伤害增益减少50%"""
    def __init__(self, duration: int = 3):
        super().__init__("Weak", duration)
    
    @property
    def strength_multiplier(self) -> float:
        """虚弱时力量增益倍率 = 0.5"""
        return 0.5


class Strength(StatusEffect):
    """力量状态 - 永久增加攻击伤害"""
    def __init__(self, amount: int):
        super().__init__("Strength", -1)  # -1 表示永久
        self.amount = amount
    
    def __repr__(self):
        return f"Strength({self.amount})"


@dataclass
class Card:
    """卡牌"""
    name: str
    rarity: str
    energy: int
    base_damage: int
    upgraded_damage: int
    effect: str
    description: str
    card_type: str = "Attack"
    upgraded: bool = False
    
    @property
    def damage(self) -> int:
        """根据是否升级返回伤害"""
        return self.upgraded_damage if self.upgraded else self.base_damage
    
    def play(self, source: 'Character', target: 'Enemy') -> 'DamageResult':
        """打出卡牌 - 链式调用的入口"""
        return DamageBuilder(source, target).calculate(self)


@dataclass
class Character:
    """角色（玩家）"""
    hp: int = 80
    max_hp: int = 80
    energy: int = 3
    max_energy: int = 3
    block: int = 0
    strength: int = 0
    status_effects: List[StatusEffect] = field(default_factory=list)
    
    def add_strength(self, amount: int) -> 'Character':
        """增加力量 - 链式调用"""
        self.strength += amount
        self.status_effects.append(Strength(amount))
        return self
    
    def add_block(self, amount: int) -> 'Character':
        """增加护甲 - 链式调用"""
        self.block += amount
        return self
    
    def add_status(self, effect: StatusEffect) -> 'Character':
        """添加状态 - 链式调用"""
        self.status_effects.append(effect)
        return self
    
    def has_status(self, status_name: str) -> bool:
        """检查是否有某状态"""
        return any(e.name == status_name for e in self.status_effects)
    
    def get_status(self, status_name: str) -> Optional[StatusEffect]:
        """获取状态"""
        for e in self.status_effects:
            if e.name == status_name:
                return e
        return None
    
    def remove_status(self, status_name: str) -> 'Character':
        """移除状态 - 链式调用"""
        self.status_effects = [e for e in self.status_effects if e.name != status_name]
        return self
    
    def end_turn(self) -> 'Character':
        """回合结束 - 护甲清零，状态回合-1"""
        self.block = 0
        new_effects = []
        for effect in self.status_effects:
            if effect.duration > 0:  # 永久效果不减少
                effect.duration -= 1
            if effect.duration != 0:
                new_effects.append(effect)
        self.status_effects = new_effects
        return self
    
    def __repr__(self):
        return f"Character(HP:{self.hp}/{self.max_hp}, Energy:{self.energy}, Block:{self.block}, Strength:{self.strength})"


@dataclass
class Enemy:
    """敌人"""
    hp: int
    max_hp: int
    vulnerable: int = 0  # 易伤回合数
    weak: int = 0       # 虚弱回合数
    block: int = 0
    
    def take_damage(self, damage: int) -> int:
        """受到伤害 - 返回实际受到的伤害（扣除护甲后）"""
        actual_damage = max(0, damage - self.block)
        remaining_block = max(0, self.block - damage)
        self.block = remaining_block
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage
    
    def apply_vulnerable(self, turns: int) -> 'Enemy':
        """施加易伤 - 链式调用"""
        self.vulnerable = turns
        return self
    
    def apply_weak(self, turns: int) -> 'Enemy':
        """施加虚弱 - 链式调用"""
        self.weak = turns
        return self
    
    def end_turn(self) -> 'Enemy':
        """回合结束"""
        self.block = 0
        if self.vulnerable > 0:
            self.vulnerable -= 1
        if self.weak > 0:
            self.weak -= 1
        return self
    
    def __repr__(self):
        return f"Enemy(HP:{self.hp}/{self.max_hp}, Vulnerable:{self.vulnerable}, Weak:{self.weak}, Block:{self.block})"


class DamageBuilder:
    """伤害计算构建器 - 支持链式调用"""
    
    def __init__(self, source: Character, target: Enemy):
        self.source = source
        self.target = target
        self.base_damage: int = 0
        self.multipliers: List[float] = []
        self.additions: List[int] = []
        self.effects: List[Callable] = []
        self._is_chain_attack = False
        self._chain_count = 0
    
    def with_card(self, card: Card) -> 'DamageBuilder':
        """使用卡牌"""
        self.base_damage = card.damage
        return self
    
    def with_strength(self) -> 'DamageBuilder':
        """应用力量加成"""
        # 获取虚弱状态对力量的削弱
        weak_multiplier = 0.5 if self.target.weak > 0 else 1.0
        effective_strength = self.source.strength * weak_multiplier
        if effective_strength != 0:
            self.additions.append(effective_strength)
        return self
    
    def with_vulnerable(self) -> 'DamageBuilder':
        """应用易伤加成"""
        # 注意：易伤和虚弱是分开的，易伤不影响力量
        # 易伤只影响最终伤害
        return self
    
    def with_heavy_blade(self, times: int = 3) -> 'DamageBuilder':
        """重刀特效 - 力量影响多次"""
        weak_multiplier = 0.5 if self.target.weak > 0 else 1.0
        effective_strength = self.source.strength * weak_multiplier * times
        if effective_strength != 0:
            self.additions.append(effective_strength)
        return self
    
    def chain_attack(self, times: int = 2) -> 'DamageBuilder':
        """链式攻击（多次攻击）"""
        self._is_chain_attack = True
        self._chain_count = times
        return self
    
    def with_effect(self, effect: Callable) -> 'DamageBuilder':
        """添加额外效果"""
        self.effects.append(effect)
        return self
    
    def calculate(self, card: Optional[Card] = None) -> 'DamageResult':
        """计算最终伤害"""
        if card:
            self.with_card(card)
        
        # 应用力量
        if "Strength" in card.effect if card else True:
            self.with_strength()
        
        # 应用易伤（只在最终计算时应用）
        if self.target.vulnerable > 0:
            self.multipliers.append(1.5)
        
        # 计算基础伤害 + 加成
        damage = self.base_damage + sum(self.additions)
        
        # 应用倍率
        for multiplier in self.multipliers:
            damage = int(damage * multiplier)
        
        # 链式攻击
        if self._is_chain_attack:
            damage *= self._chain_count
        
        # 造成伤害
        actual_damage = self.target.take_damage(damage)
        
        # 执行额外效果
        for effect in self.effects:
            effect(self.source, self.target)
        
        return DamageResult(
            base_damage=self.base_damage,
            added_damage=sum(self.additions),
            multipliers=self.multipliers.copy(),
            final_damage=actual_damage,
            blocked=damage - actual_damage,
            target_hp=self.target.hp
        )


@dataclass
class DamageResult:
    """伤害结果"""
    base_damage: int
    added_damage: int
    multipliers: List[float]
    final_damage: int
    blocked: int
    target_hp: int
    
    def __str__(self):
        mult_str = f" x {self.multipliers}" if self.multipliers else ""
        return f"伤害: {self.base_damage} + {self.added_damage}{mult_str} = {self.final_damage} (护甲抵消: {self.blocked}, 敌人剩余HP: {self.target_hp})"


# ==================== 使用示例 ====================

def demo():
    """演示链式调用"""
    
    # 创建角色和敌人
    ironclad = Character(hp=80, energy=3, strength=3)
    enemy = Enemy(hp=100, max_hp=100)
    
    print("=" * 50)
    print("初始状态:")
    print(f"  {ironclad}")
    print(f"  {enemy}")
    print("=" * 50)
    
    # 案例1: 普通攻击
    print("\n【案例1】普通攻击 (Strike)")
    result = (DamageBuilder(ironclad, enemy)
              .with_card(Card(
                  name="Strike", rarity="Starter", energy=1,
                  base_damage=6, upgraded_damage=9,
                  effect="", description="Deal 6 damage"
              ))
              .with_strength()
              .calculate())
    print(f"  {result}")
    
    # 案例2: 攻击易伤敌人
    print("\n【案例2】攻击易伤敌人 (Strike)")
    enemy.vulnerable = 2  # 敌人易伤
    result = (DamageBuilder(ironclad, enemy)
              .with_card(Card(
                  name="Strike", rarity="Starter", energy=1,
                  base_damage=6, upgraded_damage=9,
                  effect="", description="Deal 6 damage"
              ))
              .with_strength()
              .with_vulnerable()
              .calculate())
    print(f"  {result}")
    
    # 案例3: 重刀 (Heavy Blade) - 力量影响3次
    print("\n【案例3】重刀 (Heavy Blade) - 力量 x3")
    enemy.vulnerable = 0  # 重置易伤
    result = (DamageBuilder(ironclad, enemy)
              .with_card(Card(
                  name="Heavy Blade", rarity="Common", energy=2,
                  base_damage=14, upgraded_damage=14,
                  effect="Strength 3 times", description="Deal 14 damage"
              ))
              .with_heavy_blade(3)  # 力量影响3次
              .calculate())
    print(f"  {result}")
    
    # 案例4: 双重攻击 (Twin Strike)
    print("\n【案例4】双重攻击 (Twin Strike)")
    result = (DamageBuilder(ironclad, enemy)
              .with_card(Card(
                  name="Twin Strike", rarity="Common", energy=1,
                  base_damage=5, upgraded_damage=7,
                  effect="Twice", description="Deal 5 damage twice"
              ))
              .with_strength()
              .chain_attack(2)  # 攻击2次
              .calculate())
    print(f"  {result}")
    
    # 案例5: 完整链式调用演示
    print("\n【案例5】完整链式调用 - Bash")
    ironclad.add_strength(5).add_block(10)  # 链式增加力量和护甲
    enemy.apply_vulnerable(2)  # 链式施加易伤
    result = (DamageBuilder(ironclad, enemy)
              .with_card(Card(
                  name="Bash", rarity="Starter", energy=2,
                  base_damage=8, upgraded_damage=10,
                  effect="Apply 2 Vulnerable", description="Deal 8 damage"
              ))
              .with_strength()
              .with_vulnerable()
              .calculate())
    print(f"  {result}")
    print(f"  角色: {ironclad}")
    print(f"  敌人: {enemy}")
    
    print("\n" + "=" * 50)
    print("链式调用演示完成!")


if __name__ == "__main__":
    demo()
