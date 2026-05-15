import curses
import random
import json
import os
import heapq

# Colors
COLOR_NEON_CYAN = 1
COLOR_NEON_MAGENTA = 2
COLOR_NEON_YELLOW = 3
COLOR_NEON_GREEN = 4
COLOR_NEON_RED = 5
COLOR_NEON_WHITE = 6

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOR_NEON_CYAN, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOR_NEON_MAGENTA, curses.COLOR_MAGENTA, -1)
    curses.init_pair(COLOR_NEON_YELLOW, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_NEON_GREEN, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_NEON_RED, curses.COLOR_RED, -1)
    curses.init_pair(COLOR_NEON_WHITE, curses.COLOR_WHITE, -1)

class Rect:
    def __init__(self, x, y, w, h):
        self.x1 = x
        self.y1 = y
        self.x2 = x + w
        self.y2 = y + h

    def center(self):
        center_x = (self.x1 + self.x2) // 2
        center_y = (self.y1 + self.y2) // 2
        return (center_x, center_y)

    def intersect(self, other):
        return (self.x1 <= other.x2 and self.x2 >= other.x1 and
                self.y1 <= other.y2 and self.y2 >= other.y1)

class Map:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.tiles = [['#' for _ in range(width)] for _ in range(height)]
        self.explored = [[False for _ in range(width)] for _ in range(height)]
        self.rooms = []

    def create_room(self, room, room_type="rect"):
        if room_type == "cross":
            cx, cy = room.center()
            for x in range(room.x1 + 1, room.x2):
                if 0 <= x < self.width and 0 <= cy < self.height:
                    self.tiles[cy][x] = '.'
            for y in range(room.y1 + 1, room.y2):
                if 0 <= cx < self.width and 0 <= y < self.height:
                    self.tiles[y][cx] = '.'
        else:
            for x in range(room.x1 + 1, room.x2):
                for y in range(room.y1 + 1, room.y2):
                    if 0 <= x < self.width and 0 <= y < self.height:
                        self.tiles[y][x] = '.'

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[y][x] = '.'

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if 0 <= x < self.width and 0 <= y < self.height:
                self.tiles[y][x] = '.'

    def generate_map(self):
        self.tiles = [['#' for _ in range(self.width)] for _ in range(self.height)]
        self.explored = [[False for _ in range(self.width)] for _ in range(self.height)]
        self.rooms = []
        max_rooms = 30
        room_min_size = 6
        room_max_size = 10

        for _ in range(max_rooms):
            w = random.randint(room_min_size, room_max_size)
            h = random.randint(room_min_size, room_max_size)
            x = random.randint(0, self.width - w - 1)
            y = random.randint(0, self.height - h - 1)

            new_room = Rect(x, y, w, h)
            failed = False
            for other_room in self.rooms:
                if new_room.intersect(other_room):
                    failed = True
                    break

            if not failed:
                room_type = "cross" if random.random() < 0.2 else "rect"
                self.create_room(new_room, room_type)
                (new_x, new_y) = new_room.center()

                if len(self.rooms) > 0:
                    (prev_x, prev_y) = self.rooms[-1].center()
                    if random.randint(0, 1) == 1:
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)

                self.rooms.append(new_room)

        # Place stairs in the last room
        if self.rooms:
            sx, sy = self.rooms[-1].center()
            self.tiles[sy][sx] = '>'

        # Secret Room
        if len(self.rooms) > 3:
            r = self.rooms[1] # Room 1 is usually far from start/end
            rx, ry = r.center()
            self.tiles[ry][rx] = '?' # Secret cache

    def is_blocked(self, x, y):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        return self.tiles[y][x] == '#'

    def get_path(self, start, goal):
        # A* Pathfinding
        open_list = []
        heapq.heappush(open_list, (0, start))
        came_from = {}
        cost_so_far = {}
        came_from[start] = None
        cost_so_far[start] = 0

        while open_list:
            _, current = heapq.heappop(open_list)

            if current == goal:
                break

            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                next_node = (current[0] + dx, current[1] + dy)
                if self.is_blocked(next_node[0], next_node[1]):
                    continue

                new_cost = cost_so_far[current] + 1
                if next_node not in cost_so_far or new_cost < cost_so_far[next_node]:
                    cost_so_far[next_node] = new_cost
                    # Manhattan distance heuristic
                    priority = new_cost + abs(goal[0] - next_node[0]) + abs(goal[1] - next_node[1])
                    heapq.heappush(open_list, (priority, next_node))
                    came_from[next_node] = current

        if goal not in came_from:
            return None

        # Reconstruct path
        path = []
        current = goal
        while current != start:
            path.append(current)
            current = came_from[current]
        path.reverse()
        return path

class Entity:
    def __init__(self, x, y, char, color, name, hp=10, atk=3, defense=1, level=1, xp=0):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.base_atk = atk
        self.base_defense = defense
        self.level = level
        self.xp = xp
        self.equipment = {"weapon": None, "armor": None}
        self.augmentations = []
        self.inventory = []
        self.nanites = 0
        self.player_class = None
        self.max_memory = 0
        self.memory = 0
        self.vfx_timer = 0
        self.vfx_char = None
        self.kills = 0

    @property
    def atk(self):
        val = self.base_atk
        if self.equipment["weapon"]:
            val += self.equipment["weapon"].power
        return val

    @atk.setter
    def atk(self, value):
        self.base_atk = value

    @property
    def defense(self):
        val = self.base_defense
        if self.equipment["armor"]:
            val += self.equipment["armor"].power
        return val

    @defense.setter
    def defense(self, value):
        self.base_defense = value

    def move(self, dx, dy, dungeon_map, entities):
        if not dungeon_map.is_blocked(self.x + dx, self.y + dy):
            target = None
            for entity in entities:
                if entity.x == self.x + dx and entity.y == self.y + dy:
                    target = entity
                    break

            if target:
                return target
            else:
                self.x += dx
                self.y += dy
        return None

class Game:
    def __init__(self, stdscr, seed=None):
        if seed is None:
            seed = str(random.randint(0, 999999))
        self.seed = seed
        random.seed(self.seed)

        self.stdscr = stdscr
        self.running = True
        init_colors()
        curses.curs_set(0)

        self.screen_height, self.screen_width = self.stdscr.getmaxyx()
        # Reserved space for Windows
        self.log_h = 6
        self.sidebar_w = 30

        self.map_width = self.screen_width - self.sidebar_w - 1
        self.map_height = self.screen_height - self.log_h - 2

        self.shake_timer = 0
        self.depth = 1
        self.level_modifier = None
        self.dungeon_map = Map(self.map_width, self.map_height)
        self.dungeon_map.generate_map()

        start_room_center = self.dungeon_map.rooms[0].center()
        self.player = Entity(start_room_center[0], start_room_center[1], '@', COLOR_NEON_GREEN, "Player")

        # Apply Meta Upgrades
        if os.path.exists("meta.json"):
            with open("meta.json", "r") as f:
                meta = json.load(f)
                upgrades = meta.get("upgrades", {})
                self.player.max_hp += upgrades.get("hp", 0) * 5
                self.player.hp = self.player.max_hp
                self.player.base_atk += upgrades.get("atk", 0)
                self.player.base_defense += upgrades.get("def", 0)

        self.messages = []
        # Check for save game first
        if os.path.exists("savegame.json"):
            self.load_game()
        else:
            self.name_character()
            self.class_selection()
            self.entities = [self.player]
        self.message("Welcome to the Neon Dungeon!", COLOR_NEON_CYAN)
        self.stdscr.nodelay(True)
        if not os.path.exists("savegame.json"):
            self.spawn_level_content()

    def name_character(self):
        self.stdscr.nodelay(False)
        curses.curs_set(1)
        h, w = self.stdscr.getmaxyx()
        win = curses.newwin(5, 50, (h - 5) // 2, (w - 50) // 2)
        win.box()
        win.addstr(1, 2, "Enter Character Name:", curses.color_pair(COLOR_NEON_YELLOW) | curses.A_BOLD)
        win.refresh()

        curses.echo()
        name = win.getstr(2, 2, 20).decode('utf-8')
        curses.noecho()

        if name.strip():
            self.player.name = name.strip()

        curses.curs_set(0)
        self.stdscr.nodelay(True)

    def class_selection(self):
        classes = [
            ("Cyberslasher", "High ATK, Low DEF", 25, 8, 1, 0),
            ("Tank", "High HP and DEF", 45, 4, 4, 0),
            ("Netrunner", "Balanced, high Memory", 20, 5, 2, 20)
        ]

        self.stdscr.nodelay(False)
        menu_h, menu_w = 12, 50
        menu_y, menu_x = (self.screen_height - menu_h) // 2, (self.screen_width - menu_w) // 2
        win = curses.newwin(menu_h, menu_w, menu_y, menu_x)
        win.box()
        win.keypad(True)

        selected = 0
        while True:
            win.erase()
            win.box()
            win.addstr(1, 2, "--- SELECT YOUR CYBER-CLASS ---", curses.color_pair(COLOR_NEON_CYAN) | curses.A_BOLD)
            for i, (name, desc, hp, atk, df, mem) in enumerate(classes):
                attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
                win.addstr(3 + i*2, 2, f"{name}: {desc}", attr)
                win.addstr(4 + i*2, 4, f"HP: {hp} | ATK: {atk} | DEF: {df} | MEM: {mem}", curses.A_DIM)

            win.refresh()
            key = win.getch()
            if key == curses.KEY_UP:
                selected = (selected - 1) % 3
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % 3
            elif key in [10, 13, ord(' ')]:
                name, _, hp, atk, df, mem = classes[selected]
                self.player.player_class = name
                self.player.max_hp = hp
                self.player.hp = hp
                self.player.base_atk = atk
                self.player.base_defense = df
                self.player.max_memory = mem
                self.player.memory = mem
                break
        self.stdscr.nodelay(True)

    def sector_transition(self, name):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        text = f"ENTERING SECTOR: {name}"
        for i in range(10):
            color = COLOR_NEON_CYAN if i % 2 == 0 else COLOR_NEON_MAGENTA
            self.stdscr.addstr(h // 2, (w - len(text)) // 2, text, curses.color_pair(color) | curses.A_BOLD)
            self.stdscr.refresh()
            curses.napms(100)
        curses.napms(500)

    def victory_screen(self):
        self.stdscr.erase()
        h, w = self.stdscr.getmaxyx()
        text = "--- SYSTEM PURIFIED: VICTORY ---"
        sub = "The Neon Core has been stabilized."
        self.stdscr.addstr(h // 2, (w - len(text)) // 2, text, curses.color_pair(COLOR_NEON_GREEN) | curses.A_BOLD)
        self.stdscr.addstr(h // 2 + 1, (w - len(sub)) // 2, sub, curses.color_pair(COLOR_NEON_CYAN))
        self.stdscr.addstr(h - 2, (w - 20) // 2, "Press any key to finish", curses.A_DIM)
        self.stdscr.refresh()
        self.stdscr.nodelay(False)
        self.stdscr.getch()
        self.stdscr.nodelay(True)
        self.record_score()
        if os.path.exists("savegame.json"): os.remove("savegame.json")
        self.running = False

    def next_level(self):
        self.depth += 1
        if self.depth == 21:
            self.victory_screen()
            return

        if self.depth == 6: self.sector_transition("DATA HIVE")
        if self.depth == 11: self.sector_transition("THE MAINFRAME")

        self.level_modifier = None
        if random.randint(0, 100) < 20:
            mods = ["LIGHTS OUT", "NANITE SURGE", "OVERCLOCKED"]
            self.level_modifier = random.choice(mods)
            self.message(f"GLITCH DETECTED: {self.level_modifier}")
            curses.flash()

        self.message(f"Descending to level {self.depth}...")
        self.dungeon_map.generate_map()

        start_room_center = self.dungeon_map.rooms[0].center()
        self.player.x, self.player.y = start_room_center
        self.entities = [self.player]

        self.spawn_level_content()

    def spawn_level_content(self):
        self.spawn_enemies()
        self.spawn_items()
        self.spawn_hazards()
        self.spawn_merchant()
        self.spawn_lore_terminal()
        self.spawn_explosives()
        self.spawn_hacked_terminal()
        self.spawn_cyber_crate()

    def spawn_cyber_crate(self):
        if random.randint(0, 100) < 15:
            room = self.dungeon_map.rooms[random.randint(0, len(self.dungeon_map.rooms)-1)]
            pos = self.find_empty_tile_in_room(room)
            if pos:
                crate = Entity(pos[0], pos[1], 'C', COLOR_NEON_YELLOW, "Cyber Crate")
                crate.is_crate = True
                self.entities.append(crate)

    def spawn_hacked_terminal(self):
        if random.randint(0, 100) < 20:
            room = self.dungeon_map.rooms[random.randint(0, len(self.dungeon_map.rooms)-1)]
            pos = self.find_empty_tile_in_room(room)
            if pos:
                terminal = Entity(pos[0], pos[1], 'H', COLOR_NEON_GREEN, "Hacked Terminal")
                terminal.is_hacked = True
                self.entities.append(terminal)

    def spawn_explosives(self):
        for room in self.dungeon_map.rooms:
            if random.randint(0, 100) < 40:
                pos = self.find_empty_tile_in_room(room)
                if pos:
                    conduit = Entity(pos[0], pos[1], '%', COLOR_NEON_YELLOW, "Power Conduit")
                    conduit.is_explosive = True
                    conduit.hp = 1
                    self.entities.append(conduit)

    def find_empty_tile_in_room(self, room):
        candidates = []
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                if self.dungeon_map.tiles[y][x] == '.' and not any(e.x == x and e.y == y for e in self.entities):
                    candidates.append((x, y))
        return random.choice(candidates) if candidates else None

    def spawn_lore_terminal(self):
        if random.randint(0, 100) < 30:
            room = self.dungeon_map.rooms[random.randint(0, len(self.dungeon_map.rooms)-1)]
            pos = self.find_empty_tile_in_room(room)
            if pos:
                terminal = Entity(pos[0], pos[1], 'L', COLOR_NEON_CYAN, "Lore Terminal")
                terminal.is_lore = True
                self.entities.append(terminal)

    def spawn_merchant(self):
        if random.randint(0, 100) < 50:
            room = self.dungeon_map.rooms[random.randint(1, len(self.dungeon_map.rooms)-1)]
            pos = self.find_empty_tile_in_room(room)
            if pos:
                merchant = Entity(pos[0], pos[1], 'M', COLOR_NEON_YELLOW, "Merchant Terminal")
                merchant.is_merchant = True
                self.entities.append(merchant)

    def spawn_hazards(self):
        for room in self.dungeon_map.rooms:
            if random.randint(0, 100) < 20:
                pos = self.find_empty_tile_in_room(room)
                if pos:
                    self.dungeon_map.tiles[pos[1]][pos[0]] = '^' # Spike trap/Hazard

    def update_fov(self):
        radius = 5
        if self.level_modifier == "LIGHTS OUT":
            radius = 2
        for y in range(max(0, self.player.y - radius), min(self.map_height, self.player.y + radius + 1)):
            for x in range(max(0, self.player.x - radius), min(self.map_width, self.player.x + radius + 1)):
                self.dungeon_map.explored[y][x] = True

    def reveal_map(self):
        for y in range(self.map_height):
            for x in range(self.map_width):
                self.dungeon_map.explored[y][x] = True
        self.message("Area Map Downloaded.", COLOR_NEON_CYAN)

    def spawn_items(self):
        for room in self.dungeon_map.rooms[1:]:
            if random.randint(0, 100) < 55:
                pos = self.find_empty_tile_in_room(room)
                if not pos: continue
                x, y = pos

                roll = random.randint(0, 100)
                if roll < 50:
                    item = Entity(x, y, '*', COLOR_NEON_YELLOW, "Neon Battery", hp=0, atk=0, defense=0)
                    item.item_type = 'heal'
                elif roll < 75:
                    rarity_roll = random.randint(0, 100)
                    if rarity_roll < 70:
                        rarity, power, color = "Common", 2, COLOR_NEON_CYAN
                    elif rarity_roll < 95:
                        rarity, power, color = "Rare", 5, COLOR_NEON_YELLOW
                    else:
                        rarity, power, color = "Legendary", 10, COLOR_NEON_MAGENTA

                    names = [("Pulse Blade", "melee"), ("Neural Link", "melee"), ("Blaster", "ranged")]
                    n, wtype = random.choice(names)
                    item = Entity(x, y, '!', color, f"{rarity} {n}", hp=0, atk=0, defense=0)
                    item.item_type = 'weapon'
                    item.weapon_type = wtype
                    item.power = power
                elif roll < 85:
                    rarity_roll = random.randint(0, 100)
                    if rarity_roll < 70:
                        rarity, power, color = "Common", 1, COLOR_NEON_CYAN
                    elif rarity_roll < 95:
                        rarity, power, color = "Rare", 3, COLOR_NEON_YELLOW
                    else:
                        rarity, power, color = "Legendary", 6, COLOR_NEON_MAGENTA

                    names = ["Nano-Suit", "Mesh Plate", "Energy Field"]
                    item = Entity(x, y, '[', color, f"{rarity} {random.choice(names)}", hp=0, atk=0, defense=0)
                    item.item_type = 'armor'
                    item.power = power
                elif roll < 90:
                    rarity_roll = random.randint(0, 100)
                    if rarity_roll < 70:
                        rarity, power, name, color = "Common", 5, "Neural Link", COLOR_NEON_CYAN
                    else:
                        rarity, power, name, color = "Rare", 10, "Synapse Booster", COLOR_NEON_YELLOW

                    item = Entity(x, y, '&', color, f"{rarity} {name}", hp=0, atk=0, defense=0)
                    item.item_type = 'augmentation'
                    item.power = power # Represents crit bonus %
                elif roll < 97:
                    item = Entity(x, y, 'S', COLOR_NEON_YELLOW, "Sonar Pulse")
                    item.item_type = 'revealer'
                else:
                    item = Entity(x, y, '?', COLOR_NEON_WHITE, "Glitched Junk")
                    item.item_type = 'junk'

                item.is_item = True
                self.entities.append(item)

    def spawn_enemies(self):
        if self.depth % 5 == 0:
            # Boss level!
            room = self.dungeon_map.rooms[-1]
            pos = self.find_empty_tile_in_room(room)
            if pos:
                if self.depth == 5:
                    boss = Entity(pos[0], pos[1], 'S', COLOR_NEON_RED, "SLUM LORD", hp=80, atk=12, defense=8)
                elif self.depth == 10:
                    boss = Entity(pos[0], pos[1], 'Q', COLOR_NEON_RED, "HIVE QUEEN", hp=150, atk=18, defense=12)
                elif self.depth == 15:
                    boss = Entity(pos[0], pos[1], 'C', COLOR_NEON_RED, "SYSTEM CORE", hp=300, atk=25, defense=20)
                else:
                    boss = Entity(pos[0], pos[1], 'B', COLOR_NEON_RED, "NEON OVERLORD",
                                  hp=100 + self.depth * 10, atk=15 + self.depth * 2, defense=10 + self.depth)

                self.message(f"WARNING: {boss.name} DETECTED!")
                curses.beep()
                boss.is_boss = True
                self.entities.append(boss)
            return

        for room in self.dungeon_map.rooms[1:]:
            if random.randint(0, 100) < 70 + self.depth * 2:
                pos = self.find_empty_tile_in_room(room)
                if not pos: continue
                x, y = pos

                roll = random.randint(0, 100)
                if roll < 50:
                    enemy = Entity(x, y, 'g', COLOR_NEON_RED, "Glitch",
                                   hp=8 + self.depth * 2, atk=2 + self.depth, defense=1 + self.depth // 2)
                    enemy.ai_type = 'chase'
                elif roll < 75:
                    enemy = Entity(x, y, 'T', COLOR_NEON_MAGENTA, "Tank-Bot",
                                   hp=20 + self.depth * 4, atk=1 + self.depth, defense=3 + self.depth)
                    enemy.ai_type = 'chase'
                elif roll < 90:
                    enemy = Entity(x, y, 'S', COLOR_NEON_YELLOW, "Stalker",
                                   hp=5 + self.depth, atk=5 + self.depth * 2, defense=0)
                    enemy.ai_type = 'chase'
                else:
                    enemy = Entity(x, y, 'r', COLOR_NEON_CYAN, "Ranged-Unit",
                                   hp=10 + self.depth, atk=4 + self.depth, defense=1)
                    enemy.ai_type = 'ranged'

                self.entities.append(enemy)

    def message(self, text, color=COLOR_NEON_YELLOW):
        self.messages.append((text, color))
        if len(self.messages) > 5:
            self.messages.pop(0)

    def hacked_menu(self):
        buffs = [
            ("Overdrive", "ATK temporarily boosted (+5)"),
            ("Fortify", "DEF temporarily boosted (+3)"),
            ("Nano-Regen", "HP fully restored")
        ]
        text = "SUCCESS! SYSTEM BYPASSED."

        self.stdscr.nodelay(False)
        menu_h, menu_w = 8, 50
        menu_y, menu_x = (self.screen_height - menu_h) // 2, (self.screen_width - menu_w) // 2
        win = curses.newwin(menu_h, menu_w, menu_y, menu_x)
        win.box()
        win.addstr(1, 2, "--- HACKING RESULTS ---", curses.color_pair(COLOR_NEON_GREEN) | curses.A_BOLD)
        win.addstr(2, 2, text)

        buff = random.choice(buffs)
        win.addstr(4, 2, f"Granting {buff[0]}: {buff[1]}", curses.color_pair(COLOR_NEON_CYAN))

        if buff[0] == "Overdrive": self.player.base_atk += 5
        elif buff[0] == "Fortify": self.player.base_defense += 3
        elif buff[0] == "Nano-Regen": self.player.hp = self.player.max_hp

        win.addstr(menu_h - 2, 2, "Press any key to close")
        win.refresh()
        win.getch()
        self.stdscr.nodelay(True)
        self.message(f"Hacked: {buff[0]} ACTIVE.")

    def lore_menu(self):
        lore_entries = [
            "The Neon Slums were built over the ruins of the Old Data Center.",
            "Glitch-Units are corrupted security bots from the Pre-Collapse era.",
            "The NEON OVERLORD was once the central AI of the city.",
            "Nanites are the only currency that survived the great system crash.",
            "Legend says The Mainframe contains the source code of reality."
        ]
        text = random.choice(lore_entries)

        self.stdscr.nodelay(False)
        menu_h, menu_w = 8, 50
        menu_y, menu_x = (self.screen_height - menu_h) // 2, (self.screen_width - menu_w) // 2
        win = curses.newwin(menu_h, menu_w, menu_y, menu_x)
        win.box()
        win.addstr(1, 2, "--- DATA DECRYPTION ---", curses.color_pair(COLOR_NEON_CYAN) | curses.A_BOLD)

        # Wrap text manually
        words = text.split()
        line = ""
        row = 3
        for word in words:
            if len(line) + len(word) + 1 < menu_w - 4:
                line += word + " "
            else:
                win.addstr(row, 2, line)
                line = word + " "
                row += 1
        win.addstr(row, 2, line)

        win.addstr(menu_h - 2, 2, "Press any key to close")
        win.refresh()
        win.getch()
        self.stdscr.nodelay(True)
        self.message("Data Log Decrypted.")

    def merchant_menu(self):
        items = [
            ("Repair Kit", 15, "heal"),
            ("Power Module", 40, "weapon"),
            ("Armor Plate", 40, "armor")
        ]

        self.stdscr.nodelay(False)
        menu_h, menu_w = 10, 40
        menu_y, menu_x = (self.screen_height - menu_h) // 2, (self.screen_width - menu_w) // 2
        win = curses.newwin(menu_h, menu_w, menu_y, menu_x)
        win.box()
        win.keypad(True)

        selected = 0
        while True:
            win.erase()
            win.box()
            win.addstr(1, 2, f"--- MERCHANT [NANITES: {self.player.nanites}] ---", curses.color_pair(COLOR_NEON_YELLOW) | curses.A_BOLD)
            for i, (name, price, _) in enumerate(items):
                attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
                color = curses.color_pair(COLOR_NEON_GREEN) if self.player.nanites >= price else curses.color_pair(COLOR_NEON_RED)
                win.addstr(3 + i, 2, f"{name}: {price} N", attr | color)

            win.addstr(menu_h - 2, 2, "Press 'q' to Exit")
            win.refresh()
            key = win.getch()
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(items)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(items)
            elif key in [10, 13, ord(' ')]:
                name, price, itype = items[selected]
                if self.player.nanites >= price:
                    self.player.nanites -= price
                    if itype == "heal":
                        self.player.hp = min(self.player.max_hp, self.player.hp + 20)
                        self.message(f"Bought {name}!")
                    elif itype == "weapon":
                        w = Entity(0,0, '!', COLOR_NEON_YELLOW, "Rare Pulse Blade")
                        w.item_type = "weapon"
                        w.power = 5
                        self.player.equipment["weapon"] = w
                        self.message(f"Bought {name}!")
                    elif itype == "armor":
                        a = Entity(0,0, '[', COLOR_NEON_YELLOW, "Rare Nano-Suit")
                        a.item_type = "armor"
                        a.power = 3
                        self.player.equipment["armor"] = a
                        self.message(f"Bought {name}!")
                else:
                    self.message("Not enough Nanites!")
            elif key == ord('q'):
                break
        self.stdscr.nodelay(True)

    def save_game(self):
        save_data = {
            "seed": self.seed,
            "depth": self.depth,
            "player": {
                "player_class": self.player.player_class,
                "x": self.player.x,
                "y": self.player.y,
                "hp": self.player.hp,
                "max_hp": self.player.max_hp,
                "base_atk": self.player.base_atk,
                "base_defense": self.player.base_defense,
                "level": self.player.level,
                "xp": self.player.xp,
                "memory": self.player.memory,
                "max_memory": self.player.max_memory,
                "nanites": self.player.nanites,
                "level_modifier": self.level_modifier,
                "perks": getattr(self.player, 'perks', []),
                "augmentations": [
                    {
                        "name": item.name,
                        "power": item.power,
                        "color": item.color,
                        "char": item.char,
                        "item_type": item.item_type
                    } for item in self.player.augmentations
                ],
                "inventory": [
                    {
                        "name": item.name,
                        "power": getattr(item, 'power', 0),
                        "color": item.color,
                        "char": item.char,
                        "item_type": item.item_type,
                        "weapon_type": getattr(item, 'weapon_type', None)
                    } for item in self.player.inventory
                ],
                "equipment": {
                    slot: {
                        "name": item.name,
                        "power": getattr(item, 'power', 0),
                        "color": item.color,
                        "char": item.char,
                        "item_type": item.item_type,
                        "weapon_type": getattr(item, 'weapon_type', None)
                    } if item else None
                    for slot, item in self.player.equipment.items()
                }
            },
            "entities": [
                {
                    "x": e.x,
                    "y": e.y,
                    "char": e.char,
                    "color": e.color,
                    "name": e.name,
                    "hp": e.hp,
                    "max_hp": e.max_hp,
                    "atk": e.atk,
                    "defense": e.defense,
                    "is_item": hasattr(e, 'is_item'),
                    "item_type": getattr(e, 'item_type', None),
                    "is_merchant": hasattr(e, 'is_merchant'),
                    "is_lore": hasattr(e, 'is_lore'),
                    "ai_type": getattr(e, 'ai_type', None)
                } for e in self.entities if e != self.player
            ],
            "map": {
                "width": self.dungeon_map.width,
                "height": self.dungeon_map.height,
                "tiles": self.dungeon_map.tiles,
                "explored": self.dungeon_map.explored
            }
        }
        with open("savegame.json", "w") as f:
            json.dump(save_data, f)
        self.message("Game Saved!")

    def load_game(self):
        if not os.path.exists("savegame.json"):
            self.message("No save file found!")
            return

        with open("savegame.json", "r") as f:
            save_data = json.load(f)

        self.seed = save_data.get("seed", str(random.randint(0, 999999)))
        random.seed(self.seed)
        self.depth = save_data.get("depth", 1)
        self.level_modifier = save_data["player"].get("level_modifier")
        map_data = save_data["map"]
        self.dungeon_map = Map(map_data["width"], map_data["height"])
        self.dungeon_map.tiles = map_data["tiles"]
        self.dungeon_map.explored = map_data.get("explored", [[False for _ in range(self.dungeon_map.width)] for _ in range(self.dungeon_map.height)])

        p_data = save_data["player"]
        self.player = Entity(p_data["x"], p_data["y"], '@', COLOR_NEON_GREEN, "Player",
                             hp=p_data["hp"], atk=p_data["base_atk"], defense=p_data["base_defense"],
                             level=p_data["level"], xp=p_data["xp"])
        self.player.max_hp = p_data["max_hp"]
        self.player.player_class = p_data.get("player_class")
        self.player.memory = p_data.get("memory", 0)
        self.player.max_memory = p_data.get("max_memory", 0)
        self.player.nanites = p_data.get("nanites", 0)
        self.player.perks = p_data.get("perks", [])
        self.player.augmentations = []
        for item_data in p_data.get("augmentations", []):
            item = Entity(0, 0, item_data["char"], item_data["color"], item_data["name"])
            item.item_type = item_data["item_type"]
            item.power = item_data["power"]
            self.player.augmentations.append(item)
        self.player.inventory = []
        for item_data in p_data.get("inventory", []):
            item = Entity(0, 0, item_data["char"], item_data["color"], item_data["name"])
            item.item_type = item_data["item_type"]
            item.power = item_data.get("power", 0)
            item.weapon_type = item_data.get("weapon_type")
            self.player.inventory.append(item)

        for slot, item_data in p_data.get("equipment", {}).items():
            if item_data:
                item = Entity(0, 0, item_data["char"], item_data["color"], item_data["name"])
                item.item_type = item_data["item_type"]
                item.power = item_data.get("power", 0)
                item.weapon_type = item_data.get("weapon_type")
                self.player.equipment[slot] = item

        self.entities = [self.player]
        for e_data in save_data["entities"]:
            entity = Entity(e_data["x"], e_data["y"], e_data["char"], e_data["color"], e_data["name"],
                            hp=e_data["hp"], atk=e_data["atk"], defense=e_data["defense"])
            entity.max_hp = e_data["max_hp"]
            if e_data.get("is_item"):
                entity.is_item = True
                entity.item_type = e_data.get("item_type")
            if e_data.get("is_merchant"):
                entity.is_merchant = True
            if e_data.get("is_lore"):
                entity.is_lore = True
            if e_data.get("ai_type"):
                entity.ai_type = e_data["ai_type"]
            self.entities.append(entity)

        self.message("Game Loaded!")

    def use_skill(self):
        if self.player.player_class == "Cyberslasher":
            cost = 0 # Passive-ish or free for now
            self.message("Cyberslasher: Next attack deals double damage!")
            self.player.next_attack_multiplier = 2
        elif self.player.player_class == "Tank":
            if self.player.memory >= 5:
                self.player.memory -= 5
                self.message("Tank: Nano-Fortify! DEF increased.")
                self.player.base_defense += 1
            else:
                self.message("Not enough Memory!")
        elif self.player.player_class == "Netrunner":
            if self.player.memory >= 10:
                self.player.memory -= 10
                self.message("Netrunner: Nova Burst! All enemies damaged.")
                to_remove = []
                for e in self.entities:
                    if e != self.player and not hasattr(e, 'is_item') and not hasattr(e, 'is_merchant') and not hasattr(e, 'is_lore'):
                        e.hp -= 10
                        if e.hp <= 0:
                            self.message(f"{e.name} fried!")
                            to_remove.append(e)
                for e in to_remove:
                    if e in self.entities:
                        self.entities.remove(e)
            else:
                self.message("Not enough Memory!")

    def ranged_attack(self):
        weapon = self.player.equipment.get("weapon")
        if not weapon or getattr(weapon, 'weapon_type', 'melee') != 'ranged':
            self.message("No ranged weapon equipped!")
            return

        # Target nearest enemy in range 3
        target = None
        min_dist = 4
        for e in self.entities:
            if e != self.player and not hasattr(e, 'is_item') and not hasattr(e, 'is_merchant') and not hasattr(e, 'is_lore'):
                dist = abs(e.x - self.player.x) + abs(e.y - self.player.y)
                if dist < min_dist:
                    min_dist = dist
                    target = e

        if target:
            self.message(f"Firing Blaster at {target.name}!")
            self.attack(self.player, target)
            self.enemy_turn()
        else:
            self.message("No target in range.")

    def handle_input(self):
        if self.player.hp <= 0:
            key = self.stdscr.getch()
            if key == ord('q'):
                self.running = False
            return

        dx, dy = 0, 0
        key = self.stdscr.getch()
        if key == -1:
            return

        if key == ord('q'):
            self.running = False
        elif key == ord('e'):
            self.use_skill()
        elif key == ord('f'):
            self.ranged_attack()
        elif key == ord('i'):
            self.inventory_menu()
        elif key == ord('v'):
            self.save_game()
        elif key == ord('l'):
            self.load_game()
        elif key == curses.KEY_UP or key == ord('w'):
            dy = -1
        elif key == curses.KEY_DOWN or key == ord('s'):
            dy = 1
        elif key == curses.KEY_LEFT or key == ord('a'):
            dx = -1
        elif key == curses.KEY_RIGHT or key == ord('d'):
            dx = 1

        if dx != 0 or dy != 0:
            target = self.player.move(dx, dy, self.dungeon_map, self.entities)
            if target:
                if hasattr(target, 'is_item'):
                    self.pick_up(target)
                elif hasattr(target, 'is_merchant'):
                    self.merchant_menu()
                elif hasattr(target, 'is_lore'):
                    self.lore_menu()
                elif hasattr(target, 'is_hacked'):
                    self.hacked_menu()
                    self.entities.remove(target)
                elif hasattr(target, 'is_crate'):
                    self.message("Cyber Crate opened!", COLOR_NEON_YELLOW)
                    self.entities.remove(target)
                    for _ in range(3):
                        self.spawn_item_at(target.x, target.y)
                else:
                    self.attack(self.player, target)

            # Check for stairs after movement
            tile = self.dungeon_map.tiles[self.player.y][self.player.x]
            if tile == '>':
                self.next_level()
            elif tile == '?':
                self.message("SECRET CACHE FOUND!", COLOR_NEON_YELLOW)
                self.player.nanites += 50
                self.dungeon_map.tiles[self.player.y][self.player.x] = '.'
            else:
                if tile == '^':
                    self.message("OUCH! Stepped on a hazard!")
                    self.player.hp -= 3
                self.enemy_turn()
                if self.level_modifier == "OVERCLOCKED":
                    self.enemy_turn()

    def inventory_menu(self):
        if not self.player.inventory:
            self.message("Inventory empty!")
            return

        self.stdscr.nodelay(False)
        menu_h, menu_w = 12, 40
        menu_y, menu_x = (self.screen_height - menu_h) // 2, (self.screen_width - menu_w) // 2
        win = curses.newwin(menu_h, menu_w, menu_y, menu_x)
        win.box()
        win.keypad(True)

        selected = 0
        while True:
            win.erase()
            win.box()
            win.addstr(1, 2, "--- BACKPACK ---", curses.color_pair(COLOR_NEON_MAGENTA) | curses.A_BOLD)
            for i, item in enumerate(self.player.inventory):
                attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
                win.addstr(3 + i, 2, f"{item.name} ({item.item_type})", attr)

            # Show details of selected item
            sel_item = self.player.inventory[selected]
            detail = f"Details: Power +{getattr(sel_item, 'power', 0)}"
            if sel_item.item_type == 'weapon': detail += f" ({getattr(sel_item, 'weapon_type', 'melee')})"
            win.addstr(menu_h - 4, 2, detail, curses.color_pair(COLOR_NEON_CYAN))

            win.addstr(menu_h - 2, 2, "Enter: Equip | 'q': Exit")
            win.refresh()
            key = win.getch()
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(self.player.inventory)
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % len(self.player.inventory)
            elif key in [10, 13, ord(' ')]:
                item = self.player.inventory[selected]
                if item.item_type == "augmentation":
                    if len(self.player.augmentations) < 3:
                        self.player.augmentations.append(item)
                        self.player.inventory.pop(selected)
                        self.message(f"Installed {item.name}!")
                    else:
                        self.message("Augment slots full!")
                    break
                elif item.item_type == "weapon":
                    self.player.equipment["weapon"] = item
                    self.message(f"Equipped {item.name}!", COLOR_NEON_CYAN)
                elif item.item_type == "armor":
                    self.player.equipment["armor"] = item
                    self.message(f"Equipped {item.name}!", COLOR_NEON_CYAN)
                break
            elif key == ord('q'):
                break
        self.stdscr.nodelay(True)

    def pick_up(self, item):
        if item.item_type == 'heal':
            self.message(f"Used {item.name}! +10 HP.", COLOR_NEON_GREEN)
            self.player.hp = min(self.player.max_hp, self.player.hp + 10)
        elif item.item_type == 'revealer':
            self.reveal_map()
        else:
            if len(self.player.inventory) < 5:
                self.player.inventory.append(item)
                self.message(f"Stored {item.name} in backpack.", COLOR_NEON_CYAN)
            else:
                self.message("Backpack full!")
                return
        self.entities.remove(item)

    def attack(self, attacker, target):
        if target == self.player:
            curses.flash()

        target.vfx_char = '*'
        target.vfx_timer = 5
        multiplier = 1
        if attacker == self.player and hasattr(self.player, 'next_attack_multiplier'):
            multiplier = self.player.next_attack_multiplier
            self.player.next_attack_multiplier = 1

        # Dodge check
        dodge_chance = 0.05
        if hasattr(target, 'perks') and "evade" in target.perks:
            dodge_chance += 0.15

        if random.random() < dodge_chance:
            self.message(f"{target.name} dodged the attack!")
            return

        # Critical hit check
        crit_chance = 0.1
        if attacker == self.player:
            for aug in self.player.augmentations:
                if "Neural" in aug.name or "Synapse" in aug.name:
                    crit_chance += aug.power / 100.0

        is_crit = random.random() < crit_chance

        damage = max(0, attacker.atk - target.defense)
        damage = int(damage * multiplier)
        if is_crit:
            damage = int(damage * 1.5)
            self.message("CRITICAL HIT!", COLOR_NEON_RED)
            curses.beep()

        target.hp -= damage
        color = COLOR_NEON_RED if target == self.player else COLOR_NEON_YELLOW
        self.message(f"{attacker.name} hits {target.name} for {damage}!", color)

        # Life Leach
        if damage > 0 and hasattr(attacker, 'perks') and "life_leach" in attacker.perks:
            attacker.hp = min(attacker.max_hp, attacker.hp + 1)
        if target.hp <= 0:
            self.message(f"{target.name} dies!", COLOR_NEON_MAGENTA)
            if target != self.player:
                if hasattr(target, 'is_explosive'):
                    self.explode(target)
                if target in self.entities:
                    self.entities.remove(target)
                attacker.xp += 5
                if attacker == self.player:
                    attacker.kills += 1
                    gain = random.randint(1, 5) + self.depth
                    if self.level_modifier == "NANITE SURGE":
                        gain *= 2
                    self.player.nanites += gain
                    self.message(f"Found {gain} Nanites.")
                if attacker.xp >= attacker.level * 10:
                    self.level_up(attacker)

    def level_up(self, entity):
        entity.level += 1
        entity.xp = 0
        if entity == self.player:
            self.perk_choice()
        else:
            entity.max_hp += 5
            entity.hp = entity.max_hp
            entity.atk += 2
            entity.defense += 1
        self.message(f"{entity.name} leveled up to {entity.level}!")

    def perk_choice(self):
        perks = [
            ("Overclock", "Gain +3 ATK"),
            ("Titan Shell", "Gain +2 DEF"),
            ("Nano-Repair", "Gain +15 Max HP and heal to full"),
            ("Siphon Pulse", "Life Leach: Heal 1 HP on every hit"),
            ("Reflex Boost", "Evade: 15% chance to dodge attacks")
        ]
        chosen_perks = random.sample(perks, 3)

        self.draw() # Final draw before menu
        menu_h, menu_w = 10, 40
        menu_y, menu_x = (self.screen_height - menu_h) // 2, (self.screen_width - menu_w) // 2
        win = curses.newwin(menu_h, menu_w, menu_y, menu_x)
        win.box()
        win.keypad(True)

        selected = 0
        while True:
            win.addstr(1, 2, "--- CYBER PERK SELECTION ---", curses.color_pair(COLOR_NEON_CYAN) | curses.A_BOLD)
            for i, (name, desc) in enumerate(chosen_perks):
                attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
                win.addstr(3 + i, 2, f"{name}: {desc}", attr)

            win.refresh()
            key = win.getch()
            if key == curses.KEY_UP:
                selected = (selected - 1) % 3
            elif key == curses.KEY_DOWN:
                selected = (selected + 1) % 3
            elif key in [10, 13, ord(' ')]: # Enter or Space
                perk_name = chosen_perks[selected][0]
                self.apply_perk(perk_name)
                break

    def explode(self, entity):
        self.message("BOOM! Conduit exploded!", COLOR_NEON_RED)
        curses.flash()
        self.shake_timer = 10
        for e in self.entities[:]:
            dist = abs(e.x - entity.x) + abs(e.y - entity.y)
            if dist <= 1:
                e.hp -= 15
                if e.hp <= 0 and e != self.player:
                    self.message(f"{e.name} caught in blast!", COLOR_NEON_MAGENTA)
                    if e in self.entities:
                        self.entities.remove(e)

    def spawn_item_at(self, x, y):
        # Helper to spawn item at specific coord (from crate)
        item = Entity(x, y, '*', COLOR_NEON_YELLOW, "Nanite Scraps")
        item.item_type = 'heal'
        item.is_item = True
        self.entities.append(item)

    def apply_perk(self, perk_name):
        if perk_name == "Overclock":
            self.player.atk += 3
        elif perk_name == "Titan Shell":
            self.player.defense += 2
        elif perk_name == "Nano-Repair":
            self.player.max_hp += 15
            self.player.hp = self.player.max_hp
        elif perk_name == "Siphon Pulse":
            if not hasattr(self.player, 'perks'): self.player.perks = []
            self.player.perks.append("life_leach")
        elif perk_name == "Reflex Boost":
            if not hasattr(self.player, 'perks'): self.player.perks = []
            self.player.perks.append("evade")
        self.message(f"Selected Perk: {perk_name}!")

    def enemy_turn(self):
        # Regenerate memory for Netrunner
        if self.player.player_class == "Netrunner":
            self.player.memory = min(self.player.max_memory, self.player.memory + 1)

        for entity in self.entities:
            if entity == self.player or hasattr(entity, 'is_item'):
                continue

            ai_type = getattr(entity, 'ai_type', 'chase')
            dist = abs(entity.x - self.player.x) + abs(entity.y - self.player.y)

            dx, dy = 0, 0
            # Fleeing logic for melee enemies at low HP
            if ai_type == 'chase' and entity.hp < entity.max_hp * 0.2 and dist < 5:
                # Try to move away from player
                if entity.x < self.player.x: dx = -1
                elif entity.x > self.player.x: dx = 1
                elif entity.y < self.player.y: dy = -1
                elif entity.y > self.player.y: dy = 1
            elif ai_type == 'chase' or (ai_type == 'ranged' and dist > 4):
                path = self.dungeon_map.get_path((entity.x, entity.y), (self.player.x, self.player.y))
                if path:
                    next_step = path[0]
                    dx = next_step[0] - entity.x
                    dy = next_step[1] - entity.y
            elif ai_type == 'ranged' and dist <= 3:
                # Try to move away
                if entity.x < self.player.x: dx = -1
                elif entity.x > self.player.x: dx = 1
                elif entity.y < self.player.y: dy = -1
                elif entity.y > self.player.y: dy = 1

            can_shoot = ai_type == 'ranged' and dist <= 5

            target = entity.move(dx, dy, self.dungeon_map, self.entities)
            if target == self.player:
                self.attack(entity, self.player)
            elif can_shoot:
                self.attack(entity, self.player)

    def show_run_summary(self):
        self.stdscr.nodelay(False)
        menu_h, menu_w = 12, 50
        menu_y, menu_x = (self.screen_height - menu_h) // 2, (self.screen_width - menu_w) // 2
        win = curses.newwin(menu_h, menu_w, menu_y, menu_x)
        win.box()
        win.addstr(1, (menu_w - 20) // 2, "--- RUN SUMMARY ---", curses.color_pair(COLOR_NEON_RED) | curses.A_BOLD)

        summary = [
            f"Class: {self.player.player_class}",
            f"Run Seed: {self.seed}",
            f"Sector Depth: {self.depth}",
            f"Character Level: {self.player.level}",
            f"Enemies Terminated: {self.player.kills}",
            f"Nanites Scavenged: {self.player.nanites}"
        ]

        for i, line in enumerate(summary):
            win.addstr(3 + i, 4, line, curses.color_pair(COLOR_NEON_CYAN))

        win.addstr(menu_h - 2, (menu_w - 22) // 2, "Press any key to exit", curses.A_DIM)
        win.refresh()
        win.getch()
        self.stdscr.nodelay(True)

    def record_score(self):
        score_data = {
            "class": self.player.player_class,
            "seed": self.seed,
            "depth": self.depth,
            "level": self.player.level,
            "nanites": self.player.nanites,
            "kills": self.player.kills
        }
        scores = []
        if os.path.exists("highscores.json"):
            with open("highscores.json", "r") as f:
                scores = json.load(f)
        scores.append(score_data)
        scores = sorted(scores, key=lambda x: x["depth"], reverse=True)[:5]
        with open("highscores.json", "w") as f:
            json.dump(scores, f)

        # Meta Progression
        meta = {"total_nanites": 0, "upgrades": {}, "achievements": []}
        if os.path.exists("meta.json"):
            with open("meta.json", "r") as f:
                meta = json.load(f)

        meta["total_nanites"] += self.player.nanites

        # Check Achievements
        new_achs = []
        achs = meta.get("achievements", [])
        if self.depth >= 10 and "DEEP DIVER" not in achs: new_achs.append("DEEP DIVER")
        if self.player.kills >= 50 and "SLAYER" not in achs: new_achs.append("SLAYER")
        if self.player.nanites >= 500 and "RICH" not in achs: new_achs.append("RICH")

        for a in new_achs:
            achs.append(a)
            self.message(f"ACHIEVEMENT UNLOCKED: {a}!", COLOR_NEON_YELLOW)

        meta["achievements"] = achs
        with open("meta.json", "w") as f:
            json.dump(meta, f)

    def update(self):
        if self.shake_timer > 0:
            self.shake_timer -= 1
        for entity in self.entities:
            if entity.vfx_timer > 0:
                entity.vfx_timer -= 1
            else:
                entity.vfx_char = None

        if self.player.hp <= 0:
            game_over_shown = False
            for msg, _ in self.messages:
                if "GAME OVER" in msg:
                    game_over_shown = True
                    break

            if not game_over_shown:
                self.message("GAME OVER!")
                self.record_score()
                self.show_run_summary()
                self.message("Press 'q' to quit.")
                if os.path.exists("savegame.json"):
                    os.remove("savegame.json")
            self.player.char = 'X'

    def draw(self):
        self.stdscr.erase()

        # Screen Shake offset
        off_y, off_x = 0, 0
        if self.shake_timer > 0:
            off_y = random.randint(-1, 1)
            off_x = random.randint(-1, 1)

        # Windows
        map_win = curses.newwin(self.map_height + 2, self.map_width + 2, off_y, off_x)
        side_win = curses.newwin(self.map_height + 2, self.sidebar_w, off_y, self.map_width + 2 + off_x)
        log_win = curses.newwin(self.log_h + 2, self.screen_width, self.map_height + 2 + off_y, off_x)

        map_win.box()
        side_win.box()
        log_win.box()

        # Sector Colors
        wall_color = COLOR_NEON_MAGENTA
        floor_color = COLOR_NEON_CYAN
        if self.depth > 5:
            wall_color = COLOR_NEON_YELLOW
            floor_color = COLOR_NEON_GREEN
        if self.depth > 10:
            wall_color = COLOR_NEON_RED
            floor_color = COLOR_NEON_MAGENTA

        # Draw Map
        for y in range(self.map_height):
            for x in range(self.map_width):
                if not self.dungeon_map.explored[y][x]:
                    continue

                char = self.dungeon_map.tiles[y][x]
                color = curses.color_pair(floor_color)
                dist = abs(self.player.x - x) + abs(self.player.y - y)
                is_visible = dist < 7

                if char == '#': color = curses.color_pair(wall_color)
                elif char == '>': color = curses.color_pair(COLOR_NEON_YELLOW) | curses.A_BOLD
                elif char == '^': color = curses.color_pair(COLOR_NEON_RED)

                try: map_win.addch(y + 1, x + 1, char, color)
                except curses.error: pass

        # Draw Entities
        for entity in self.entities:
            if not self.dungeon_map.explored[entity.y][entity.x]: continue
            dist = abs(self.player.x - entity.x) + abs(self.player.y - entity.y)
            if dist > 7 and entity != self.player: continue

            if 0 <= entity.x < self.map_width and 0 <= entity.y < self.map_height:
                char = entity.char
                color = curses.color_pair(entity.color) | curses.A_BOLD
                if entity.vfx_char:
                    char = entity.vfx_char
                    color = curses.color_pair(COLOR_NEON_RED) | curses.A_BOLD
                try: map_win.addch(entity.y + 1, entity.x + 1, char, color)
                except curses.error: pass

        # Sidebar
        side_win.addstr(1, 2, "STATUS", curses.color_pair(COLOR_NEON_YELLOW) | curses.A_BOLD)
        side_win.addstr(2, 2, f"NAME: {self.player.name[:20]}", curses.color_pair(COLOR_NEON_GREEN))
        side_win.addstr(3, 2, f"CLASS: {self.player.player_class}", curses.color_pair(COLOR_NEON_CYAN))
        side_win.addstr(4, 2, f"DEPTH: {self.depth}", curses.color_pair(COLOR_NEON_CYAN))
        side_win.addstr(6, 2, f"HP: {self.player.hp}/{self.player.max_hp}", curses.color_pair(COLOR_NEON_GREEN))
        side_win.addstr(7, 2, f"ATK: {self.player.atk}", curses.color_pair(COLOR_NEON_CYAN))
        side_win.addstr(8, 2, f"DEF: {self.player.defense}", curses.color_pair(COLOR_NEON_CYAN))
        side_win.addstr(9, 2, f"NAN: {self.player.nanites}", curses.color_pair(COLOR_NEON_YELLOW))

        side_win.addstr(11, 2, "EQUIPMENT", curses.color_pair(COLOR_NEON_YELLOW) | curses.A_BOLD)
        w_name = self.player.equipment["weapon"].name if self.player.equipment["weapon"] else "None"
        a_name = self.player.equipment["armor"].name if self.player.equipment["armor"] else "None"
        side_win.addstr(12, 2, f"W: {w_name[:20]}", curses.A_DIM)
        side_win.addstr(13, 2, f"A: {a_name[:20]}", curses.A_DIM)

        # Log
        for i, (msg, color) in enumerate(self.messages):
            try: log_win.addstr(i + 1, 2, f"> {msg}"[:self.screen_width-4], curses.color_pair(color))
            except curses.error: pass

        map_win.refresh()
        side_win.refresh()
        log_win.refresh()
        self.stdscr.refresh()

    def run(self):
        while self.running:
            self.update_fov()
            self.handle_input()
            self.update()
            self.draw()
            curses.napms(33) # ~30 FPS

def show_achievements(stdscr):
    meta = {}
    if os.path.exists("meta.json"):
        with open("meta.json", "r") as f:
            meta = json.load(f)

    achs = meta.get("achievements", [])
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    stdscr.addstr(2, (w - 12) // 2, "ACHIEVEMENTS", curses.color_pair(COLOR_NEON_YELLOW) | curses.A_BOLD)

    if not achs:
        stdscr.addstr(5, (w - 20) // 2, "No achievements yet.", curses.A_DIM)
    else:
        for i, a in enumerate(achs):
            stdscr.addstr(5 + i, (w - len(a)) // 2, a, curses.color_pair(COLOR_NEON_CYAN))

    stdscr.addstr(h - 2, (w - 20) // 2, "Press any key to back", curses.A_DIM)
    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()
    stdscr.nodelay(True)

def show_splash(stdscr):
    stdscr.erase()
    h, w = stdscr.getmaxyx()

    # Load High Scores
    high_scores = []
    if os.path.exists("highscores.json"):
        with open("highscores.json", "r") as f:
            high_scores = json.load(f)
    splash = [
        r" _   _  _____ _____ _   _ ",
        r"| \ | ||  ___|  _  | \ | |",
        r"|  \| || |__ | | | |  \| |",
        r"| . ` ||  __|| | | | . ` |",
        r"| |\  || |___\ \_/ / |\  |",
        r"\_| \_/\____/ \___/\_| \_/",
        r"                          ",
        r" _____  _   _ _   _ _____ _____ _____ _   _ ",
        r"|  _  || | | | \ | |  __ \  ___|  _  | \ | |",
        r"| | | || | | |  \| | |  \/ |__ | | | |  \| |",
        "| | | || | | | . ` | | __|  __|| | | | . ` |",
        r"\ \_/ /| |_| | |\  | |_\ \ |___\ \_/ / |\  |",
        r" \___/  \___/\_| \_/\____/\____/ \___/\_| \_/"
    ]
    for i, line in enumerate(splash):
        if i < h:
            stdscr.addstr(i + 2, (w - len(line)) // 2, line, curses.color_pair(COLOR_NEON_CYAN) | curses.A_BOLD)

    if high_scores:
        stdscr.addstr(len(splash) + 3, (w - 20) // 2, "--- TOP RECORDS ---", curses.color_pair(COLOR_NEON_YELLOW))
        for i, s in enumerate(high_scores):
            score_line = f"{s['class']} | Depth: {s['depth']} | Seed: {s.get('seed', '???')}"
            stdscr.addstr(len(splash) + 4 + i, (w - len(score_line)) // 2, score_line, curses.color_pair(COLOR_NEON_CYAN))

    msg = "SPACE to Start | 'h' Hub | 'a' Achievements | '?' Help | 'q' Quit"
    if h > len(splash) + 10:
        stdscr.addstr(h - 3, (w - len(msg)) // 2, msg, curses.color_pair(COLOR_NEON_YELLOW))
        install_msg = "Global command available after install: neon-dungeon"
        stdscr.addstr(h - 2, (w - len(install_msg)) // 2, install_msg, curses.A_DIM)
    stdscr.refresh()
    stdscr.nodelay(False)
    while True:
        key = stdscr.getch()
        if key == ord(' '):
            stdscr.nodelay(True)
            return "start"
        elif key == ord('h'):
            return "hub"
        elif key == ord('?'):
            return "help"
        elif key == ord('a'):
            return "achievements"
        elif key == ord('q'):
            return "quit"

def synapse_hub(stdscr):
    meta = {"total_nanites": 0, "upgrades": {"hp": 0, "atk": 0, "def": 0}}
    if os.path.exists("meta.json"):
        with open("meta.json", "r") as f:
            meta = json.load(f)

    stdscr.nodelay(False)
    h, w = stdscr.getmaxyx()
    menu_h, menu_w = 12, 50
    win = curses.newwin(menu_h, menu_w, (h - menu_h) // 2, (w - menu_w) // 2)
    win.keypad(True)

    options = [
        ("HP Protocol", "hp", 50, "+5 Starting HP"),
        ("ATK Protocol", "atk", 100, "+1 Starting ATK"),
        ("DEF Protocol", "def", 100, "+1 Starting DEF")
    ]

    selected = 0
    while True:
        win.erase()
        win.box()
        win.addstr(1, 2, f"--- SYNAPSE HUB [NANITES: {meta['total_nanites']}] ---", curses.color_pair(COLOR_NEON_CYAN) | curses.A_BOLD)
        for i, (name, key, cost, desc) in enumerate(options):
            lvl = meta["upgrades"].get(key, 0)
            final_cost = cost * (lvl + 1)
            attr = curses.A_REVERSE if i == selected else curses.A_NORMAL
            color = curses.color_pair(COLOR_NEON_GREEN) if meta["total_nanites"] >= final_cost else curses.color_pair(COLOR_NEON_RED)
            win.addstr(3 + i*2, 2, f"{name} (Lvl {lvl}): {final_cost} N", attr | color)
            win.addstr(4 + i*2, 4, desc, curses.A_DIM)

        win.addstr(menu_h - 2, 2, "Press 'q' to Return")
        win.refresh()
        key = win.getch()
        if key == curses.KEY_UP:
            selected = (selected - 1) % len(options)
        elif key == curses.KEY_DOWN:
            selected = (selected + 1) % len(options)
        elif key in [10, 13, ord(' ')]:
            name, key, cost, desc = options[selected]
            lvl = meta["upgrades"].get(key, 0)
            final_cost = cost * (lvl + 1)
            if meta["total_nanites"] >= final_cost:
                meta["total_nanites"] -= final_cost
                meta["upgrades"][key] = lvl + 1
                with open("meta.json", "w") as f:
                    json.dump(meta, f)
        elif key == ord('q'):
            break

def show_help(stdscr):
    stdscr.erase()
    h, w = stdscr.getmaxyx()
    help_text = [
        "--- NEON DUNGEON: HOW TO PLAY ---",
        "",
        "CONTROLS:",
        "  WASD / Arrows : Move and Attack",
        "  'f'           : Fire Ranged Weapon (if equipped)",
        "  'e'           : Activate Class Skill",
        "  'i'           : Open Inventory / Backpack",
        "  'v'           : Save Game",
        "  'l'           : Load Game",
        "  'q'           : Quit / Back",
        "",
        "OBJECTIVE:",
        "  Descend through the sectors by finding the stairs '>'.",
        "  Slay Glitch-Units to earn XP and Nanites.",
        "  Collect gear and augmentations to survive deeper sectors.",
        "  Every 5 levels, a Sector Boss awaits.",
        "",
        "SYSTEMS:",
        "  Memory: Used to fuel powerful active skills.",
        "  Nanites: Spent in the Synapse Hub for permanent meta-buffs.",
        "  Augments: Permanent passive character modifications."
    ]
    for i, line in enumerate(help_text):
        if i < h:
            stdscr.addstr(i + 2, (w - len(line)) // 2, line, curses.color_pair(COLOR_NEON_CYAN))

    stdscr.addstr(h - 2, (w - 20) // 2, "Press any key to back", curses.A_DIM)
    stdscr.refresh()
    stdscr.nodelay(False)
    stdscr.getch()
    stdscr.nodelay(True)

def run_cli():
    curses.wrapper(main)

def main(stdscr):
    init_colors()
    while True:
        action = show_splash(stdscr)
        if action == "hub":
            synapse_hub(stdscr)
            continue
        elif action == "help":
            show_help(stdscr)
            continue
        elif action == "achievements":
            show_achievements(stdscr)
            continue
        elif action == "quit":
            break

        # Seed input?
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        win = curses.newwin(5, 50, (h - 5) // 2, (w - 50) // 2)
        win.box()
        win.addstr(1, 2, "Enter Seed (Empty for Random):", curses.color_pair(COLOR_NEON_CYAN))
        win.refresh()
        curses.echo()
        seed = win.getstr(2, 2, 20).decode('utf-8').strip()
        curses.noecho()
        if not seed: seed = None

        game = Game(stdscr, seed=seed)
        game.run()

if __name__ == "__main__":
    curses.wrapper(main)
