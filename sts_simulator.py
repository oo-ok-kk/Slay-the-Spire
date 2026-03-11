"""
Slay the Spire Simulator - 杀戮尖塔模拟器
基于 ironclad_master_data.json
"""

import json
from dataclasses import dataclass, field
from typing import Optional, List


# ==================== 数据加载 ====================

def load_card_data() -> dict:
    """加载卡牌数据"""
    try:
        with open('ironclad_master_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # 如果本地文件不存在，从GitHub获取
        import urllib.request
        url = "https://raw.githubusercontent.com/oo-ok-kk/Slay-the-Spire/main/ironclad_master_data.json"
        with urllib.request.urlopen(url) as response:
            return json.loads(response.read().decode())


# ==================== 类定义 ====================

@dataclass
class Entity:
    """实体基类（玩家或敌人）"""
    name: str
    hp: int
    max_hp: int
    block: int = 0
    strength: int = 0
    vulnerable: int = 0  # 易伤回合数
    weak: int = 0       # 虚弱回合数
    
    def take_damage(self, damage: int) -> int:
        """受到伤害，返回实际受到的伤害（扣除格挡后）"""
        actual_damage = max(0, damage - self.block)
        remaining_block = max(0, self.block - damage)
        self.block = remaining_block
        self.hp = max(0, self.hp - actual_damage)
        return actual_damage
    
    def add_block(self, amount: int) -> 'Entity':
        """增加格挡值"""
        self.block += amount
        return self
    
    def add_strength(self, amount: int) -> 'Entity':
        """增加力量"""
        self.strength += amount
        return self
    
    def apply_vulnerable(self, turns: int) -> 'Entity':
        """施加易伤"""
        self.vulnerable = turns
        return self
    
    def apply_weak(self, turns: int) -> 'Entity':
        """施加虚弱"""
        self.weak = turns
        return self
    
    def start_turn(self) -> 'Entity':
        """回合开始时重置格挡值（核心逻辑3）"""
        self.block = 0
        # 状态回合数递减
        if self.vulnerable > 0:
            self.vulnerable -= 1
        if self.weak > 0:
            self.weak -= 1
        return self
    
    def is_alive(self) -> bool:
        """是否存活"""
        return self.hp > 0
    
    def __repr__(self):
        return f"{self.name}(HP:{self.hp}/{self.max_hp}, Block:{self.block}, Strength:{self.strength}, Vulnerable:{self.vulnerable})"


@dataclass
class Card:
    """卡牌类"""
    name: str
    rarity: str
    card_type: str  # Attack, Skill, Power
    cost: int
    damage: int = 0
    damage_upgraded: int = 0
    block: int = 0
    block_upgraded: int = 0
    effect: str = ""
    description: str = ""
    upgraded: bool = False
    
    @property
    def base_damage(self) -> int:
        """基础伤害（根据是否升级）"""
        return self.damage_upgraded if self.upgraded else self.damage
    
    @property
    def base_block(self) -> int:
        """基础格挡（根据是否升级）"""
        return self.block_upgraded if self.upgraded else self.block
    
    def is_attack(self) -> bool:
        """是否是攻击牌"""
        return self.card_type == "Attack"
    
    def is_skill(self) -> bool:
        """是否是技能牌"""
        return self.card_type == "Skill"
    
    def is_power(self) -> bool:
        """是否是能力牌"""
        return self.card_type == "Power"


# ==================== 核心逻辑 ====================

def apply_card(card: Card, source: Entity, target: Entity) -> dict:
    """
    应用卡牌效果（核心逻辑2）
    
    公式: FinalDamage = BaseDamage + Strength
    
    Args:
        card: 使用的卡牌
        source: 释放者（玩家）
        target: 目标（敌人）
    
    Returns:
        dict: 包含伤害、格挡等信息的字典
    """
    result = {
        "card": card.name,
        "type": card.card_type,
        "damage_dealt": 0,
        "block_gained": 0,
        "strength_gained": 0,
        "effects": []
    }
    
    if card.card_type == "Attack":
        # ========== 攻击牌 ==========
        base_damage = card.base_damage
        
        # 核心公式：FinalDamage = BaseDamage + Strength（核心逻辑2）
        # 虚弱状态会使力量增益减半
        if source.weak > 0:
            effective_strength = int(source.strength * 0.5)
        else:
            effective_strength = source.strength
        
        final_damage = base_damage + effective_strength
        
        # 易伤状态：受到伤害增加50%
        if target.vulnerable > 0:
            final_damage = int(final_damage * 1.5)
        
        # 造成伤害
        actual_damage = target.take_damage(final_damage)
        result["damage_dealt"] = actual_damage
        result["effects"].append(f"基础伤害 {base_damage} + 力量 {effective_strength} = {base_damage + effective_strength}")
        
        if target.vulnerable > 0:
            result["effects"].append(f"易伤倍率 x1.5 → 最终伤害 {actual_damage}")
        
    elif card.card_type == "Skill":
        # ========== 技能牌 ==========
        # 处理格挡
        if card.base_block > 0:
            source.add_block(card.base_block)
            result["block_gained"] = card.base_block
        
        # 处理消耗/特殊效果
        if "Exhaust" in card.effect:
            result["effects"].append("Exhaust: 消耗")
        
        if "Draw" in card.description:
            result["effects"].append("抽牌效果")
            
    elif card.card_type == "Power":
        # ========== 能力牌 ==========
        # 处理力量获取
        if "Strength" in card.effect:
            # 从效果描述中提取力量数值
            import re
            match = re.search(r'Gain (\d+)\((\d+)\)?', card.effect)
            if match:
                strength_amount = int(match.group(2)) if source.strength > 0 else int(match.group(1))
                source.add_strength(strength_amount)
                result["strength_gained"] = strength_amount
                result["effects"].append(f"获得 {strength_amount} 力量")
    
    return result


# ==================== 单元测试（核心逻辑4） ====================

def run_tests():
    """单元测试：验证核心功能"""
    print("=" * 60)
    print("单元测试：铁甲战士使用《打击》攻击怪物")
    print("=" * 60)
    
    # 1. 创建实体
    ironclad = Entity(name="Ironclad", hp=80, max_hp=80, strength=3)
    monster = Entity(name="Monster", hp=50, max_hp=50)
    
    print(f"\n【初始状态】")
    print(f"  玩家: {ironclad}")
    print(f"  怪物: {monster}")
    
    # 2. 加载卡牌数据
    card_data = load_card_data()
    
    # 3. 找到《打击》(Strike)卡牌
    strike_card = None
    for card_info in card_data['cards']:
        if card_info['name'] == 'Strike':
            strike_card = Card(
                name=card_info['name'],
                rarity=card_info['rarity'],
                card_type=card_info['type'],
                cost=card_info['cost'],
                damage=card_info['damage'],
                damage_upgraded=card_info['damage_upgraded'],
                effect=card_info['effect'],
                description=card_info['description']
            )
            break
    
    print(f"\n【使用卡牌】")
    print(f"  卡牌: {strike_card.name}")
    print(f"  类型: {strike_card.card_type}")
    print(f"  伤害: {strike_card.base_damage}")
    print(f"  费用: {strike_card.cost}")
    
    # 4. 应用卡牌（核心验证）
    print(f"\n【计算过程】")
    print(f"  公式: FinalDamage = BaseDamage + Strength")
    print(f"  = {strike_card.base_damage} + {ironclad.strength}")
    print(f"  = {strike_card.base_damage + ironclad.strength}")
    
    result = apply_card(strike_card, ironclad, monster)
    
    print(f"\n【结果】")
    print(f"  造成伤害: {result['damage_dealt']}")
    print(f"  怪物剩余HP: {monster.hp}")
    print(f"  效果描述: {result['effects']}")
    
    # 5. 验证
    expected_damage = 6 + 3  # 基础伤害 + 力量
    assert result['damage_dealt'] == expected_damage, f"伤害计算错误！期望 {expected_damage}，实际 {result['damage_dealt']}"
    assert monster.hp == 50 - expected_damage, f"怪物HP计算错误！"
    
    print(f"\n{'=' * 60}")
    print("✅ 测试通过！")
    print(f"{'=' * 60}")
    
    # 6. 测试回合开始时格挡清零（核心逻辑3）
    print(f"\n【回合机制测试】")
    ironclad.add_block(10)
    print(f"  回合开始前格挡: {ironclad.block}")
    ironclad.start_turn()
    print(f"  回合开始后格挡: {ironclad.block}")
    assert ironclad.block == 0, "格挡应该清零！"
    print(f"  ✅ 格挡清零测试通过！")


# ==================== 主程序 ====================

if __name__ == "__main__":
    run_tests()
