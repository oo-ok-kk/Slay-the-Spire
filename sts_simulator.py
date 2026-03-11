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


# ==================== Task 3: 战斗模拟器 ====================

import csv
import random
from collections import Counter


class BattleSim:
    """
    战斗模拟器 - 测试力量流卡组稳定性
    
    实验设定:
    - 卡组: 5张《打击》, 5张《防御》, 2张《燃烧》(增加2力量)
    - 敌人: 100HP, 每回合固定造成8点伤害
    - 模拟: 5000场战斗
    - 策略: 贪婪算法（优先打力量牌，其次打伤害牌）
    """
    
    def __init__(self, card_data: dict):
        self.card_data = card_data
        self.card_library = {}
        
        # 加载卡牌到库
        for card_info in card_data['cards']:
            self.card_library[card_info['name']] = Card(
                name=card_info['name'],
                rarity=card_info['rarity'],
                card_type=card_info['type'],
                cost=card_info['cost'],
                damage=card_info['damage'],
                damage_upgraded=card_info['damage_upgraded'],
                block=card_info.get('block', 0),
                block_upgraded=card_info.get('block_upgraded', 0),
                effect=card_info.get('effect', ''),
                description=card_info.get('description', '')
            )
    
    def create_deck(self) -> List[Card]:
        """
        创建卡组:
        - 5张 Strike (打击)
        - 5张 Defend (防御)
        - 2张 Inflame (燃烧, +2力量)
        """
        deck = []
        
        # 5张打击
        for _ in range(5):
            deck.append(self.card_library['Strike'])
        
        # 5张防御
        for _ in range(5):
            deck.append(self.card_library['Defend'])
        
        # 2张燃烧
        for _ in range(2):
            deck.append(self.card_library['Inflame'])
        
        return deck
    
    def greedy_play(self, hand: List[Card], player: Entity, enemy: Entity) -> List[Card]:
        """
        贪婪算法打牌:
        1. 优先打力量牌 (Power)
        2. 其次打伤害最高的牌
        """
        # 按优先级排序
        # 优先级: Power(力量) > Attack(攻击) > Skill(防御)
        sorted_hand = sorted(hand, key=lambda c: (
            0 if c.card_type == 'Power' else  1 if c.card_type == 'Attack' else 2,
            -(c.base_damage + c.base_block)  # 伤害/格挡高的优先
        ))
        
        return sorted_hand
    
    def simulate_battle(self, player_hp: int = 80, enemy_hp: int = 100, enemy_damage: int = 8) -> dict:
        """
        单场战斗模拟
        
        Returns:
            dict: {
                'win': bool,           # 是否胜利
                'turns': int,          # 回合数
                'damage_taken': int,   # 受到的伤害
                'final_hp': int        # 剩余HP
            }
        """
        # 初始化
        player = Entity(name="Ironclad", hp=player_hp, max_hp=player_hp)
        enemy = Entity(name="Enemy", hp=enemy_hp, max_hp=enemy_hp)
        
        # 创建卡组并洗牌
        deck = self.create_deck()
        draw_pile = deck.copy()
        random.shuffle(draw_pile)
        discard_pile = []
        hand = []
        
        turn = 0
        total_damage_taken = 0
        
        while player.is_alive() and enemy.is_alive():
            turn += 1
            
            # 回合开始
            player.start_turn()
            enemy.start_turn()
            
            # 抽牌 (每回合抽5张)
            for _ in range(5):
                if not draw_pile:
                    if discard_pile:
                        draw_pile = discard_pile.copy()
                        random.shuffle(draw_pile)
                        discard_pile = []
                    else:
                        break
                hand.append(draw_pile.pop())
            
            # 贪婪打牌
            cards_to_play = self.greedy_play(hand.copy(), player, enemy)
            
            for card in cards_to_play:
                if not player.is_alive() or not enemy.is_alive():
                    break
                
                apply_card(card, player, enemy)
                hand.remove(card)
                discard_pile.append(card)
                
                # 敌人死亡，跳出
                if not enemy.is_alive():
                    break
            
            # 敌人攻击
            if enemy.is_alive():
                damage_taken = enemy.take_damage(enemy_damage)
                total_damage_taken += damage_taken
            
            # 弃掉剩余手牌
            discard_pile.extend(hand)
            hand = []
        
        return {
            'win': enemy.hp <= 0,
            'turns': turn,
            'damage_taken': total_damage_taken,
            'final_hp': player.hp
        }
    
    def run_simulation(self, num_battles: int = 5000, output_file: str = "sim_results.csv") -> dict:
        """
        运行多场战斗模拟
        
        Args:
            num_battles: 战斗场数
            output_file: 输出CSV文件名
        
        Returns:
            dict: 统计结果
        """
        print(f"{'='*60}")
        print(f"战斗模拟开始")
        print(f"{'='*60}")
        print(f"卡组: 5 Strike + 5 Defend + 2 Inflame")
        print(f"敌人: 100HP, 每回合伤害 8")
        print(f"模拟场次: {num_battles}")
        print(f"{'='*60}\n")
        
        results = []
        wins = 0
        total_damage = 0
        total_turns = 0
        
        for i in range(num_battles):
            result = self.simulate_battle()
            results.append({
                'battle_id': i + 1,
                'win': result['win'],
                'turns': result['turns'],
                'damage_taken': result['damage_taken'],
                'final_hp': result['final_hp']
            })
            
            if result['win']:
                wins += 1
            total_damage += result['damage_taken']
            total_turns += result['turns']
            
            # 进度显示
            if (i + 1) % 1000 == 0:
                print(f"进度: {i+1}/{num_battles} ({100*(i+1)//num_battles}%)")
        
        # 保存CSV
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['battle_id', 'win', 'turns', 'damage_taken', 'final_hp'])
            writer.writeheader()
            writer.writerows(results)
        
        # 统计结果
        stats = {
            'total_battles': num_battles,
            'wins': wins,
            'win_rate': wins / num_battles * 100,
            'avg_damage_taken': total_damage / num_battles,
            'avg_turns': total_turns / num_battles,
            'output_file': output_file
        }
        
        return stats


def run_battle_sim():
    """运行战斗模拟测试"""
    # 加载数据
    card_data = load_card_data()
    
    # 创建模拟器
    sim = BattleSim(card_data)
    
    # 运行5000场战斗
    stats = sim.run_simulation(num_battles=5000, output_file='sim_results.csv')
    
    # 输出结果
    print(f"\n{'='*60}")
    print(f"模拟结果统计")
    print(f"{'='*60}")
    print(f"总战斗场数: {stats['total_battles']}")
    print(f"胜利场数: {stats['wins']}")
    print(f"胜率: {stats['win_rate']:.2f}%")
    print(f"平均损血量: {stats['avg_damage_taken']:.2f}")
    print(f"平均回合数: {stats['avg_turns']:.2f}")
    print(f"结果已保存至: {stats['output_file']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    # 可以选择运行哪个测试
    # run_tests()           # 单元测试
    run_battle_sim()       # 战斗模拟


# ==================== Task 5: Lagavulin 敌人模拟 ====================

@dataclass
class Lagavulin(Entity):
    """
    乐嘉维林 (Lagavulin) - 洞穴第三层Boss前小怪
    
    属性:
    - 110 HP (进阶0级基准)
    - 沉睡状态 (Asleep): 前3回合不行动，除非受到伤害
    
    攻击循环:
    - 回合1-2: 造成18点伤害
    - 回合3: 灵魂虹吸 (Siphon Soul) - 玩家力量-1，敏捷-1
    - 循环
    """
    
    def __init__(self):
        super().__init__(
            name="Lagavulin",
            hp=110,
            max_hp=110
        )
        self.metallicize: int = 8  # 金属化：每回合结束获得8格挡
        self.is_asleep: bool = True  # 初始沉睡
        self.turn_counter: int = 0   # 回合计数器
        self.total_damage_dealt: int = 0  # 累计伤害
        self.siphon_count: int = 0  # 灵魂虹吸次数
    
    def start_turn(self) -> 'Lagavulin':
        """回合开始"""
        self.turn_counter += 1
        self.block = 0  # 重置格挡
        
        # 沉睡逻辑：如果受到伤害则唤醒
        if self.is_asleep:
            print(f"  [Lagavulin 沉睡中...]")
        
        return self
    
    def take_damage(self, damage: int) -> int:
        """受到伤害时唤醒"""
        actual = super().take_damage(damage)
        if self.is_asleep and damage > 0:
            self.is_asleep = False
            print(f"  [Lagavulin 被惊醒！]")
        return actual
    
    def take_turn(self, player: Entity) -> dict:
        """
        执行敌人回合
        返回: {'action': str, 'damage': int, 'effects': list}
        """
        result = {
            'action': 'none',
            'damage': 0,
            'effects': []
        }
        
        # 沉睡中不行动
        if self.is_asleep:
            result['action'] = 'asleep'
            print(f"  Lagavulin 回合 {self.turn_counter}: 沉睡中，不行动")
            # 沉睡时仍获得金属化
            self.add_block(self.metallicize)
            print(f"    金属化: +{self.metallicize} 格挡")
            return result
        
        # 攻击循环模式
        # 回合1, 2: 18伤害
        # 回合3: 灵魂虹吸 (Siphon Soul)
        cycle_turn = ((self.turn_counter - 1) % 3) + 1  # 1, 2, 3循环
        
        if cycle_turn in [1, 2]:
            # 普通攻击
            damage = 18
            actual_damage = player.take_damage(damage)
            self.total_damage_dealt += actual_damage
            result['action'] = 'attack'
            result['damage'] = actual_damage
            print(f"  Lagavulin 回合 {self.turn_counter}: 攻击造成 {actual_damage} 伤害")
        
        elif cycle_turn == 3:
            # 灵魂虹吸
            player.strength -= 1
            # 注意：杀戮尖塔中敏捷(Dexterity)会减少格挡
            # 但这里简化为只有力量
            self.siphon_count += 1
            result['action'] = 'siphon'
            result['effects'] = ['player_strength_-1']
            print(f"  Lagavulin 回合 {self.turn_counter}: 灵魂虹吸！玩家力量-1")
        
        # 回合结束时获得金属化
        self.add_block(self.metallicize)
        print(f"    金属化: +{self.metallicize} 格挡 (总格挡: {self.block})")
        
        return result
    
    def get_status(self) -> str:
        """获取状态描述"""
        status = f"Lagavulin HP:{self.hp}/{self.max_hp}"
        if self.is_asleep:
            status += " [沉睡]"
        status += f" | 累计伤害:{self.total_damage_dealt} | 虹吸次数:{self.siphon_count}"
        return status


def simulate_lagavulin_battle():
    """模拟乐嘉维林战斗 - 验证第10回合的累计压力"""
    print("=" * 70)
    print("Task 5: 乐嘉维林 (Lagavulin) 战斗模拟")
    print("=" * 70)
    print("敌人: Lagavulin")
    print("  - 110 HP")
    print("  - 初始沉睡，前3回合不行动（除非受到伤害）")
    print("  - 回合1-2: 18伤害")
    print("  - 回合3: 灵魂虹吸 (力量-1)")
    print("  - 回合结束: 金属化 +8 格挡")
    print("=" * 70)
    
    # 加载卡牌数据
    card_data = load_card_data()
    card_library = {}
    for card_info in card_data['cards']:
        card_library[card_info['name']] = Card(
            name=card_info['name'],
            rarity=card_info['rarity'],
            card_type=card_info['type'],
            cost=card_info['cost'],
            damage=card_info['damage'],
            damage_upgraded=card_info['damage_upgraded'],
            block=card_info.get('block', 0),
            block_upgraded=card_info.get('block_upgraded', 0),
            effect=card_info.get('effect', ''),
            description=card_info.get('description', '')
        )
    
    # 创建玩家和敌人
    player = Entity(name="Ironclad", hp=80, max_hp=80, strength=0)
    lagavulin = Lagavulin()
    
    # 玩家卡组（简单攻击卡牌用于唤醒）
    strike_card = card_library['Strike']
    
    print(f"\n【初始状态】")
    print(f"  玩家: {player}")
    print(f"  敌人: {lagavulin.get_status()}")
    
    # 模拟10回合
    print(f"\n{'='*70}")
    print("战斗过程")
    print("=" * 70)
    
    for turn in range(1, 11):
        print(f"\n--- 回合 {turn} ---")
        
        # 玩家回合
        player.start_turn()
        
        # 玩家攻击以唤醒沉睡敌人
        if lagavulin.is_asleep:
            print(f"  玩家攻击以唤醒 Lagavulin...")
            apply_card(strike_card, player, lagavulin)
            print(f"    造成 {strike_card.base_damage} 伤害")
        
        # 敌人回合
        lagavulin.start_turn()
        lagavulin.take_turn(player)
        
        print(f"  玩家状态: {player}")
        print(f"  敌人状态: {lagavulin.get_status()}")
    
    # 第10回合总结
    print(f"\n{'='*70}")
    print(f"【第10回合总结】")
    print(f"{'='*70}")
    print(f"  玩家剩余HP: {player.hp}/{player.max_hp}")
    print(f"  玩家损失HP: {player.max_hp - player.hp}")
    print(f"  玩家剩余力量: {player.strength}")
    print(f"  Lagavulin 剩余HP: {lagavulin.hp}/{lagavulin.max_hp}")
    print(f"  累计造成伤害: {lagavulin.total_damage_dealt}")
    print(f"  灵魂虹吸次数: {lagavulin.siphon_count}")
    print(f"\n【数值压力分析】")
    print(f"  前10回合平均伤害/回合: {lagavulin.total_damage_dealt / 10:.1f}")
    
    # 计算实际战斗回合（唤醒后的回合）
    active_turns = max(0, turn - 3)  # 假设在第3回合被唤醒
    print(f"  沉睡回合数: 3")
    print(f"  实际行动回合数: {active_turns}")
    if active_turns > 0:
        print(f"  行动回合平均伤害: {lagavulin.total_damage_dealt / active_turns:.1f}")
    print(f"{'='*70}")


if __name__ == "__main__":
    # 运行 Lagavulin 模拟
    simulate_lagavulin_battle()
