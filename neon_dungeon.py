import os
import sys
import json
import random
import time
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

DATA_DIR = "neon_dungeon_data"
SAVE_FILE = os.path.join(DATA_DIR, "save.json")
BEST_RUNS_FILE = os.path.join(DATA_DIR, "best_runs.json")
CODEX_FILE = os.path.join(DATA_DIR, "codex.json")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def load_json(filepath, default):
    if not os.path.exists(filepath):
        return default
    try:
        with open(filepath, 'r') as f:
            return json.load(f)
    except Exception:
        return default

def save_json(filepath, data):
    ensure_data_dir()
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)


@dataclass
class Hero:
    name: str
    class_name: str
    hp: int
    max_hp: int
    attack: int
    defense: int
    dodge_chance: int
    level: int = 1
    xp: int = 0
    credits: int = 0
    floor: int = 1
    inventory: List[str] = field(default_factory=list)
    equipped_weapon: str = "Rusty Keyboard"
    equipped_armor: str = "Hoodie"
    skills: List[str] = field(default_factory=list)
    defeated_bosses: List[str] = field(default_factory=list)
    active_run: bool = True
    modifiers: List[str] = field(default_factory=list)

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

@dataclass
class Enemy:
    name: str
    hp: int
    max_hp: int
    attack: int
    defense: int
    dodge_chance: int
    is_boss: bool = False

    def to_dict(self):
        return self.__dict__

CLASSES = {
    "Hacker": {"max_hp": 30, "attack": 6, "defense": 3, "dodge_chance": 10, "skill": "Data Spike", "desc": "Balanced, starts with Data Spike skill (ignores some defense)"},
    "Runner": {"max_hp": 25, "attack": 5, "defense": 2, "dodge_chance": 25, "skill": "Phase Dash", "desc": "Faster, higher dodge chance"},
    "Tank": {"max_hp": 40, "attack": 4, "defense": 5, "dodge_chance": 5, "skill": "Shield Wall", "desc": "More HP and defense"},
    "Glitch Mage": {"max_hp": 20, "attack": 8, "defense": 1, "dodge_chance": 15, "skill": "Byte Storm", "desc": "Lower HP, stronger special skill"}
}

WEAPONS = {
    "Rusty Keyboard": {"attack": 2},
    "Neon Dagger": {"attack": 4},
    "Packet Blade": {"attack": 6},
    "Laser Katana": {"attack": 8},
    "Admin Hammer": {"attack": 10},
    "Ghost Spear": {"attack": 12}
}

ARMORS = {
    "Hoodie": {"defense": 1},
    "Chrome Vest": {"defense": 3},
    "Firewall Cloak": {"defense": 5},
    "Admin Plate": {"defense": 8},
    "Phantom Shell": {"defense": 10}
}

ITEMS = {
    "Health Patch": {"heal": 15, "price": 10, "desc": "Heals 15 HP"},
    "Mega Health Patch": {"heal": 40, "price": 25, "desc": "Heals 40 HP"},
    "Energy Drink": {"energy": 1, "price": 15, "desc": "Restores energy for skills (Not implemented yet)"},
    "Data Shard": {"xp": 20, "price": 20, "desc": "Grants 20 XP"},
    "Smoke Bomb": {"escape": True, "price": 15, "desc": "Allows escaping combat"},
    "Repair Kit": {"heal": 25, "price": 20, "desc": "Heals 25 HP"}
}

ENEMIES = [
    {"name": "Glitch Rat", "hp_base": 10, "atk_base": 3, "def_base": 0, "dodge": 5},
    {"name": "Static Slime", "hp_base": 15, "atk_base": 2, "def_base": 2, "dodge": 0},
    {"name": "Malware Knight", "hp_base": 25, "atk_base": 5, "def_base": 4, "dodge": 5},
    {"name": "Chrome Spider", "hp_base": 12, "atk_base": 6, "def_base": 1, "dodge": 20},
    {"name": "Data Wraith", "hp_base": 18, "atk_base": 7, "def_base": 0, "dodge": 15},
    {"name": "Packet Goblin", "hp_base": 14, "atk_base": 4, "def_base": 1, "dodge": 10},
    {"name": "Trojan Archer", "hp_base": 20, "atk_base": 6, "def_base": 2, "dodge": 10},
    {"name": "Cache Mimic", "hp_base": 30, "atk_base": 4, "def_base": 5, "dodge": 0},
    {"name": "Signal Leech", "hp_base": 22, "atk_base": 5, "def_base": 2, "dodge": 5},
    {"name": "Null Reaper", "hp_base": 40, "atk_base": 8, "def_base": 3, "dodge": 10}
]

BOSSES = {
    5: {"name": "Firewall Brute", "hp_base": 50, "atk_base": 8, "def_base": 5, "dodge": 5},
    10: {"name": "Chrome Hydra", "hp_base": 100, "atk_base": 12, "def_base": 8, "dodge": 10},
    15: {"name": "Black Ice Queen", "hp_base": 150, "atk_base": 16, "def_base": 10, "dodge": 15},
    20: {"name": "Rootkit Dragon", "hp_base": 220, "atk_base": 20, "def_base": 15, "dodge": 10},
    25: {"name": "The Core Ghost", "hp_base": 350, "atk_base": 25, "def_base": 20, "dodge": 20}
}

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print("=" * 50)
    print("           N E O N   D U N G E O N   C L I")
    print("=" * 50)

def input_prompt(prompt="> "):
    try:
        return input(prompt).strip()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)

def get_hero_stats(hero: Hero):
    wep_atk = WEAPONS.get(hero.equipped_weapon, {}).get("attack", 0)
    arm_def = ARMORS.get(hero.equipped_armor, {}).get("defense", 0)
    return hero.attack + wep_atk, hero.defense + arm_def

def save_game(hero: Hero):
    save_json(SAVE_FILE, hero.to_dict())

def update_codex(category: str, item: str):
    codex = load_json(CODEX_FILE, {})
    if category not in codex:
        codex[category] = []
    if item not in codex[category]:
        codex[category].append(item)
    save_json(CODEX_FILE, codex)

def save_best_run(hero: Hero, result: str):
    runs = load_json(BEST_RUNS_FILE, [])
    run_data = {
        "name": hero.name,
        "class": hero.class_name,
        "deepest_floor": hero.floor,
        "level": hero.level,
        "credits": hero.credits,
        "bosses_defeated": hero.defeated_bosses,
        "result": result,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    runs.append(run_data)
    runs.sort(key=lambda x: x["deepest_floor"], reverse=True)
    save_json(BEST_RUNS_FILE, runs[:10]) # Keep top 10

def generate_enemy(floor: int) -> Enemy:
    if floor in BOSSES:
        boss_data = BOSSES[floor]
        hp = boss_data["hp_base"] + (floor * 2)
        atk = boss_data["atk_base"] + (floor // 2)
        defense = boss_data["def_base"] + (floor // 3)
        return Enemy(boss_data["name"], hp, hp, atk, defense, boss_data["dodge"], is_boss=True)

    enemy_data = random.choice(ENEMIES)
    hp = enemy_data["hp_base"] + (floor * 2) + random.randint(0, floor)
    atk = enemy_data["atk_base"] + (floor // 2)
    defense = enemy_data["def_base"] + (floor // 3)

    name = enemy_data["name"]
    # Variants
    variant = random.random()
    if variant < 0.1:
        name = f"Elite {name}"
        hp = int(hp * 1.5)
        atk = int(atk * 1.2)
    elif variant < 0.2:
        name = f"Corrupted {name}"
        atk = int(atk * 1.5)
        hp = int(hp * 0.8)
    elif variant < 0.3:
        name = f"Mini {name}"
        hp = int(hp * 0.5)
        dodge = min(50, enemy_data["dodge"] + 20)

    return Enemy(name, hp, hp, atk, defense, enemy_data["dodge"])


def level_up_check(hero: Hero):
    while hero.xp >= hero.level * 100:
        hero.xp -= hero.level * 100
        hero.level += 1
        hero.max_hp += 5
        hero.hp = min(hero.max_hp, hero.hp + 10)
        hero.attack += 1
        hero.defense += 1
        print(f"\n*** LEVEL UP! You are now level {hero.level} ***")
        print(f"Max HP increased to {hero.max_hp}!")
        print(f"Attack increased to {hero.attack}!")
        print(f"Defense increased to {hero.defense}!")
        input("Press Enter to continue...")

def create_hero() -> Optional[Hero]:
    clear_screen()
    print_banner()
    name = ""
    while not name:
        name = input_prompt("Enter your hero's name: ")
        if not name:
            print("Name cannot be empty.")

    print("\nSelect your class:")
    class_list = list(CLASSES.keys())
    for i, cls in enumerate(class_list):
        info = CLASSES[cls]
        print(f"{i+1}. {cls} ({info['desc']})")

    cls_idx = -1
    while cls_idx < 0 or cls_idx >= len(class_list):
        choice = input_prompt("> ")
        if choice.isdigit() and 1 <= int(choice) <= len(class_list):
            cls_idx = int(choice) - 1
        else:
            print("Invalid choice.")

    cls_name = class_list[cls_idx]
    stats = CLASSES[cls_name]

    hero = Hero(
        name=name,
        class_name=cls_name,
        hp=stats["max_hp"],
        max_hp=stats["max_hp"],
        attack=stats["attack"],
        defense=stats["defense"],
        dodge_chance=stats["dodge_chance"],
        skills=[stats["skill"]]
    )

    update_codex("classes", cls_name)
    print(f"\nHero created: {hero.name} the {hero.class_name}!")
    time.sleep(1.5)
    return hero

def continue_run() -> Optional[Hero]:
    data = load_json(SAVE_FILE, None)
    if data and data.get("active_run"):
        return Hero.from_dict(data)
    else:
        print("No active run found.")
        time.sleep(1.5)
        return None

def view_hero(hero: Hero):
    clear_screen()
    print_banner()
    print(f"Name: {hero.name} | Class: {hero.class_name} | Level: {hero.level}")
    print(f"HP: {hero.hp}/{hero.max_hp} | XP: {hero.xp}/{hero.level*100} | Credits: {hero.credits}")
    total_atk, total_def = get_hero_stats(hero)
    print(f"Attack: {total_atk} (Base {hero.attack}) | Defense: {total_def} (Base {hero.defense})")
    print(f"Dodge: {hero.dodge_chance}% | Floor: {hero.floor}")
    print(f"\nEquipped Weapon: {hero.equipped_weapon}")
    print(f"Equipped Armor: {hero.equipped_armor}")
    print("\nSkills:")
    for skill in hero.skills:
        print(f"- {skill}")
    print("\nInventory:")
    if not hero.inventory:
        print("- Empty")
    else:
        for item in hero.inventory:
            print(f"- {item}")
    print(f"\nModifiers: {', '.join(hero.modifiers) if hero.modifiers else 'None'}")
    input_prompt("\nPress Enter to return...")

def view_best_runs():
    clear_screen()
    print_banner()
    runs = load_json(BEST_RUNS_FILE, [])
    if not runs:
        print("No past runs found.")
    else:
        for i, run in enumerate(runs):
            print(f"{i+1}. {run['name']} the {run['class']} - Floor {run['deepest_floor']} (Level {run['level']})")
            print(f"   Result: {run['result']} | Credits: {run['credits']} | Time: {run['timestamp']}")
    input_prompt("\nPress Enter to return...")

def view_codex():
    clear_screen()
    print_banner()
    codex = load_json(CODEX_FILE, {})
    if not codex:
        print("Codex is empty. Start playing to discover items, enemies, and classes!")
    else:
        for cat, items in codex.items():
            print(f"\n--- {cat.upper()} ---")
            for item in sorted(items):
                print(f"- {item}")
    input_prompt("\nPress Enter to return...")

def display_help():
    clear_screen()
    print_banner()
    print("Welcome to Neon Dungeon CLI!")
    print("This is a free, open-source, offline terminal roguelite.")
    print("\nHow to Play:")
    print("- Explore the dungeon floor by floor.")
    print("- Fight enemies, collect loot, and manage your stats.")
    print("- Reach floor 25 to win!")
    print("\nCombat:")
    print("- Attack: Uses your equipped weapon and attack stat to deal damage.")
    print("- Defend: Reduces incoming damage for the turn.")
    print("- Skill: Uses your class's unique ability.")
    print("- Item: Consume an item from your inventory.")
    print("- Flee: Try to run away (does not work on bosses).")
    print("\nPrivacy & Safety:")
    print("This game uses no tracking, no ads, and requires no internet.")
    print("All save files are stored locally in the 'neon_dungeon_data' folder.")
    input_prompt("\nPress Enter to return...")


def show_ending(hero: Hero, victory: bool):
    clear_screen()
    print_banner()
    if victory:
        print("V I C T O R Y !")
        print("You have successfully breached The Core Ghost and survived the Neon Dungeon!")
        result = "Victory"
    else:
        print("G A M E   O V E R")
        print("Your signal has been lost...")
        result = "Defeat"

    hero.active_run = False
    save_best_run(hero, result)
    save_game(hero) # Save inactive state to prevent reload exploit

    print(f"\nFinal Stats:")
    print(f"Name: {hero.name} the {hero.class_name}")
    print(f"Level: {hero.level} | Floor: {hero.floor}")
    print(f"Credits: {hero.credits}")
    print(f"Bosses Defeated: {len(hero.defeated_bosses)}")
    input_prompt("\nPress Enter to return to Main Menu...")

def main_menu():
    while True:
        clear_screen()
        print_banner()
        print("1. New Run")
        print("2. Continue Run")
        print("3. View Hero (if active run exists)")
        print("4. Best Runs")
        print("5. Codex")
        print("6. Help")
        print("7. Quit")

        choice = input_prompt("> ")
        if choice == '1':
            hero = create_hero()
            if hero:
                save_game(hero)
                dungeon_loop(hero)
        elif choice == '2':
            hero = continue_run()
            if hero:
                dungeon_loop(hero)
        elif choice == '3':
            hero = continue_run()
            if hero:
                view_hero(hero)
            else:
                print("No active run found.")
                time.sleep(1.5)
        elif choice == '4':
            view_best_runs()
        elif choice == '5':
            view_codex()
        elif choice == '6':
            display_help()
        elif choice == '7':
            print("Shutting down terminal...")
            break
        else:
            print("Invalid command.")
            time.sleep(1)


def dungeon_loop(hero: Hero):
    weathers = ["Calm", "Calm", "Calm", "Byte Storm", "Low Signal", "Overclocked"]
    while hero.hp > 0 and hero.active_run:
        clear_screen()

        # Apply weather modifier
        if random.random() < 0.3:
            current_weather = random.choice(weathers)
        else:
            current_weather = "Calm"

        # Clean up old weather if it exists
        if "weather" in hero.modifiers:
            idx = hero.modifiers.index("weather")
            hero.modifiers.pop(idx)
            if idx < len(hero.modifiers):
                hero.modifiers.pop(idx) # Remove the value too

        if current_weather != "Calm":
            hero.modifiers.extend(["weather", current_weather])
            print(f"--- FLOOR {hero.floor} [{current_weather}] ---")
        else:
            print(f"--- FLOOR {hero.floor} ---")

        xp_needed = hero.level * 100
        xp_bars = int((hero.xp / xp_needed) * 10)
        xp_str = "[" + "=" * xp_bars + " " * (10 - xp_bars) + "]"

        print(f"[HP: {hero.hp}/{hero.max_hp}] [Credits: {hero.credits}] [XP: {xp_str} {hero.xp}/{xp_needed}]")

        if hero.floor == 26 and "endless" not in hero.modifiers:
            show_ending(hero, victory=True)
            print("Would you like to continue in Endless Mode? (y/n)")
            ans = input_prompt("> ").lower()
            if ans == 'y':
                hero.modifiers.append("endless")
                hero.active_run = True
            else:
                break

        encounter_types = ["combat"] * 5 + ["loot"] * 2 + ["heal"] * 1 + ["shop"] * 1 + ["event"] * 2

        if hero.floor % 5 == 0:
            encounter = "boss"
        else:
            encounter = random.choice(encounter_types)

        if encounter == "combat":
            enemy = generate_enemy(hero.floor)
            combat_loop(hero, enemy)
        elif encounter == "boss":
            enemy = generate_enemy(hero.floor)
            print(f"WARNING: BOSS ENCOUNTER DETECTED!")
            combat_loop(hero, enemy)
        elif encounter == "loot":
            handle_loot(hero)
        elif encounter == "heal":
            handle_heal(hero)
        elif encounter == "shop":
            shop_loop(hero)
        elif encounter == "event":
            event_loop(hero)

        if hero.hp <= 0:
            show_ending(hero, victory=False)
            break

        hero.floor += 1
        level_up_check(hero)
        save_game(hero)

        while hero.active_run:
            print("\nArea clear. Options:")
            print("1. Continue Deeper")
            print("2. Inspect Hero")
            print("3. Use Item")
            print("4. Save and Quit")
            choice = input_prompt("> ")
            if choice == '1':
                break
            elif choice == '2':
                view_hero(hero)
                clear_screen()
                print(f"--- FLOOR {hero.floor-1} ---")
            elif choice == '3':
                use_item(hero)
            elif choice == '4':
                save_game(hero)
                return


def handle_loot(hero: Hero):
    print("You found a loot cache!")
    roll = random.random()
    if roll < 0.4:
        creds = random.randint(10, 30) + hero.floor * 2
        print(f"Inside, you find {creds} Credits.")
        hero.credits += creds
    elif roll < 0.7:
        item = random.choice(list(ITEMS.keys()))
        print(f"Inside, you find a {item}.")
        hero.inventory.append(item)
        update_codex("items", item)
    elif roll < 0.85:
        wep = random.choice(list(WEAPONS.keys()))
        print(f"Inside, you find a {wep} (Attack: {WEAPONS[wep]['attack']}).")
        update_codex("weapons", wep)
        print("Equip it? (y/n)")
        if input_prompt("> ").lower() == 'y':
            hero.equipped_weapon = wep
    else:
        arm = random.choice(list(ARMORS.keys()))
        print(f"Inside, you find {arm} (Defense: {ARMORS[arm]['defense']}).")
        update_codex("armors", arm)
        print("Equip it? (y/n)")
        if input_prompt("> ").lower() == 'y':
            hero.equipped_armor = arm
    input_prompt("Press Enter to continue...")

def handle_heal(hero: Hero):
    print("You found a healing station.")
    heal_amount = int(hero.max_hp * 0.3)
    hero.hp = min(hero.max_hp, hero.hp + heal_amount)
    print(f"You restored {heal_amount} HP.")
    input_prompt("Press Enter to continue...")

def use_item(hero: Hero):
    # Returns (escaped: bool, item_used: bool)
    if not hero.inventory:
        print("Your inventory is empty.")
        time.sleep(1)
        return False, False

    print("\nInventory:")
    for i, item in enumerate(hero.inventory):
        desc = ITEMS.get(item, {}).get("desc", "")
        print(f"{i+1}. {item} - {desc}")
    print("0. Cancel")

    choice = input_prompt("> ")
    if choice.isdigit():
        idx = int(choice) - 1
        if 0 <= idx < len(hero.inventory):
            item_name = hero.inventory.pop(idx)
            item_data = ITEMS.get(item_name, {})
            if "heal" in item_data:
                hero.hp = min(hero.max_hp, hero.hp + item_data["heal"])
                print(f"Used {item_name}. Restored {item_data['heal']} HP.")
            elif "xp" in item_data:
                hero.xp += item_data["xp"]
                print(f"Used {item_name}. Gained {item_data['xp']} XP.")
                level_up_check(hero)
            elif "escape" in item_data:
                print(f"Used {item_name}. You are surrounded by smoke!")
                return True, True # Escape flag
            else:
                print(f"Used {item_name}, but it had no immediate effect.")
            time.sleep(1.5)
            return False, True
    return False, False


def combat_loop(hero: Hero, enemy: Enemy):
    print(f"\nYou encounter a {enemy.name}!")
    update_codex("enemies", enemy.name)
    if enemy.is_boss:
        update_codex("bosses", enemy.name)

    defending = False
    skill_active = None

    while hero.hp > 0 and enemy.hp > 0:
        print(f"\n[{hero.name} - HP: {hero.hp}/{hero.max_hp}]")
        print(f"[{enemy.name} - HP: {enemy.hp}/{enemy.max_hp}]")

        print("1. Attack")
        print("2. Defend")
        print(f"3. Use Skill ({hero.skills[0] if hero.skills else 'None'})")
        print("4. Use Item")
        print("5. Inspect")
        print("6. Flee")

        action = input_prompt("> ")
        hero_atk, hero_def = get_hero_stats(hero)

        weather = ""
        if "weather" in hero.modifiers:
            weather = hero.modifiers[hero.modifiers.index("weather") + 1]

        if weather == "Overclocked":
            hero_atk = int(hero_atk * 1.2)
        elif weather == "Low Signal":
            hero_atk = max(1, int(hero_atk * 0.8))

        if defending:
            defending = False # Reset defense from last turn

        if action == '1':
            if random.randint(1, 100) <= enemy.dodge_chance:
                print(f"You attack, but {enemy.name} dodged!")
            else:
                dmg = max(1, hero_atk - enemy.defense)
                if random.random() < 0.1: # 10% crit
                    dmg = int(dmg * 1.5)
                    print("CRITICAL HIT!")
                enemy.hp -= dmg
                print(f"You deal {dmg} damage to {enemy.name}.")

        elif action == '2':
            defending = True
            print("You take a defensive stance, reducing incoming damage.")

        elif action == '3':
            if not hero.skills:
                print("You have no skills!")
                continue
            skill = hero.skills[0]
            if skill == "Data Spike":
                dmg = max(1, int(hero_atk * 1.2) - (enemy.defense // 2))
                enemy.hp -= dmg
                print(f"You use Data Spike! Dealt {dmg} damage, ignoring some defense.")
            elif skill == "Phase Dash":
                skill_active = "Phase Dash"
                print("You use Phase Dash! Dodge chance massively increased this turn.")
            elif skill == "Shield Wall":
                skill_active = "Shield Wall"
                print("You use Shield Wall! Incoming damage heavily reduced this turn.")
            elif skill == "Byte Storm":
                cost = int(hero.max_hp * 0.1)
                hero.hp -= cost
                dmg = max(1, int(hero_atk * 2.0) - enemy.defense)
                enemy.hp -= dmg
                print(f"You sacrifice {cost} HP to cast Byte Storm! Dealt {dmg} damage to {enemy.name}.")
                if hero.hp <= 0:
                    print("The Byte Storm consumed you...")
                    return

        elif action == '4':
            escaped, item_used = use_item(hero)
            if escaped:
                if enemy.is_boss:
                    print("You cannot escape a boss fight!")
                    continue
                else:
                    print("You escaped the battle using an item!")
                    return
            if not item_used:
                continue # Item wasn't used, don't consume turn

        elif action == '5':
            print(f"\n--- INSPECT ---")
            print(f"{enemy.name}")
            print(f"HP: {enemy.hp}/{enemy.max_hp}")
            print(f"Attack: {enemy.attack}")
            print(f"Defense: {enemy.defense}")
            print(f"Dodge Chance: {enemy.dodge_chance}%")
            print("---------------")
            time.sleep(1)
            continue # Inspecting doesn't consume a turn

        elif action == '6':
            if enemy.is_boss:
                print("You cannot flee from a boss!")
                continue
            if random.random() < 0.5:
                print("You successfully fled the battle!")
                return
            else:
                print("You failed to flee!")
        else:
            print("Invalid action.")
            continue

        if enemy.hp <= 0:
            break

        # Enemy turn
        dodge_ch = hero.dodge_chance
        if skill_active == "Phase Dash":
            dodge_ch += 50

        if random.randint(1, 100) <= dodge_ch:
            print(f"{enemy.name} attacks, but you dodged!")
        else:
            eff_def = hero_def
            if defending:
                eff_def = int(eff_def * 1.5) + 2
            if skill_active == "Shield Wall":
                eff_def += 10

            e_atk = enemy.attack
            if weather == "Overclocked":
                e_atk = int(e_atk * 1.2)
            elif weather == "Low Signal":
                e_atk = max(1, int(e_atk * 0.8))

            e_dmg = max(1, e_atk - eff_def)
            hero.hp -= e_dmg
            print(f"{enemy.name} attacks! You take {e_dmg} damage.")

        if weather == "Byte Storm" and hero.hp > 0:
            bs_dmg = random.randint(1, 3)
            hero.hp -= bs_dmg
            enemy.hp -= bs_dmg
            print(f"The Byte Storm zaps everyone for {bs_dmg} damage!")

        skill_active = None # Reset skill buffs

    if hero.hp > 0:
        xp_gain = 20 + (hero.floor * 5)
        if enemy.is_boss:
            xp_gain *= 3
            hero.defeated_bosses.append(enemy.name)
            print(f"*** {enemy.name} DEFEATED! ***")
        else:
            print(f"{enemy.name} defeated!")

        hero.xp += xp_gain
        cred_gain = random.randint(5, 15) + hero.floor
        hero.credits += cred_gain
        print(f"Gained {xp_gain} XP and {cred_gain} Credits.")
        input_prompt("Press Enter to continue...")


def shop_loop(hero: Hero):
    print("\nYou found a Shop Terminal.")
    stock = random.sample(list(ITEMS.keys()), min(3, len(ITEMS)))

    # Add optional random weapon/armor or mystery box
    if random.random() < 0.5:
        wep = random.choice(list(WEAPONS.keys()))
        stock.append(wep)
    if random.random() < 0.5:
        arm = random.choice(list(ARMORS.keys()))
        stock.append(arm)
    stock.append("Mystery Box")

    while True:
        print(f"\n[Credits: {hero.credits}]")
        print("Items for sale:")
        for i, item in enumerate(stock):
            if item in ITEMS:
                price = ITEMS[item]["price"]
            elif item in WEAPONS:
                price = WEAPONS[item]["attack"] * 10
            elif item in ARMORS:
                price = ARMORS[item]["defense"] * 10
            elif item == "Mystery Box":
                price = 30
            else:
                price = 50
            print(f"{i+1}. {item} - {price} Credits")
        print("0. Leave")

        choice = input_prompt("> ")
        if choice == '0':
            print("Leaving shop.")
            time.sleep(1)
            break
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(stock):
                item = stock[idx]

                if item in ITEMS:
                    price = ITEMS[item]["price"]
                elif item in WEAPONS:
                    price = WEAPONS[item]["attack"] * 10
                elif item in ARMORS:
                    price = ARMORS[item]["defense"] * 10
                elif item == "Mystery Box":
                    price = 30
                else:
                    price = 50

                if hero.credits >= price:
                    hero.credits -= price
                    stock.pop(idx) # Remove from stock

                    if item in ITEMS:
                        hero.inventory.append(item)
                        update_codex("items", item)
                        print(f"Bought {item} for {price} Credits.")
                    elif item in WEAPONS:
                        update_codex("weapons", item)
                        print(f"Bought {item} for {price} Credits.")
                        print("Equip it? (y/n)")
                        if input_prompt("> ").lower() == 'y':
                            hero.equipped_weapon = item
                    elif item in ARMORS:
                        update_codex("armors", item)
                        print(f"Bought {item} for {price} Credits.")
                        print("Equip it? (y/n)")
                        if input_prompt("> ").lower() == 'y':
                            hero.equipped_armor = item
                    elif item == "Mystery Box":
                        print("You open the Mystery Box...")
                        roll = random.random()
                        if roll < 0.3:
                            creds = random.randint(10, 50)
                            print(f"You found {creds} Credits inside!")
                            hero.credits += creds
                        elif roll < 0.6:
                            found_item = random.choice(list(ITEMS.keys()))
                            print(f"You found a {found_item} inside!")
                            hero.inventory.append(found_item)
                            update_codex("items", found_item)
                        elif roll < 0.8:
                            print("It's a trap! You take 5 damage.")
                            hero.hp -= 5
                        else:
                            print("It's empty...")
                else:
                    print("Not enough Credits.")
                time.sleep(1)

def event_loop(hero: Hero):
    events = [
        "broken vending machine",
        "suspicious data shrine",
        "lost robot merchant",
        "corrupted terminal",
        "neon fountain",
        "abandoned server rack",
        "glitch portal",
        "encrypted chest"
    ]
    event = random.choice(events)
    print(f"\nMystery Event: You encountered a {event}.")
    print("1. Investigate")
    print("2. Ignore")

    choice = input_prompt("> ")
    if choice == '1':
        outcome = random.random()
        if outcome < 0.4:
            creds = random.randint(20, 50)
            print(f"Success! You found {creds} hidden credits.")
            hero.credits += creds
        elif outcome < 0.7:
            heal = int(hero.max_hp * 0.2)
            print(f"A soothing energy restores {heal} HP.")
            hero.hp = min(hero.max_hp, hero.hp + heal)
        elif outcome < 0.85:
            print("It was a trap! You take 5 damage.")
            hero.hp -= 5
        else:
            item = random.choice(list(ITEMS.keys()))
            print(f"Jackpot! You obtained a {item}.")
            hero.inventory.append(item)
            update_codex("items", item)
    else:
        print("You safely walked past it.")

    input_prompt("Press Enter to continue...")

if __name__ == "__main__":
    try:
        main_menu()
    except Exception as e:
        print(f"\nA fatal error occurred: {e}")
        sys.exit(1)
