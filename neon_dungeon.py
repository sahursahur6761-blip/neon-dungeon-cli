import curses
import random
import json
import os

# Colors
COLOR_NEON_CYAN = 1
COLOR_NEON_MAGENTA = 2
COLOR_NEON_YELLOW = 3
COLOR_NEON_GREEN = 4
COLOR_NEON_RED = 5

def init_colors():
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(COLOR_NEON_CYAN, curses.COLOR_CYAN, -1)
    curses.init_pair(COLOR_NEON_MAGENTA, curses.COLOR_MAGENTA, -1)
    curses.init_pair(COLOR_NEON_YELLOW, curses.COLOR_YELLOW, -1)
    curses.init_pair(COLOR_NEON_GREEN, curses.COLOR_GREEN, -1)
    curses.init_pair(COLOR_NEON_RED, curses.COLOR_RED, -1)

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

    def create_room(self, room):
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
                self.create_room(new_room)
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

    def is_blocked(self, x, y):
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return True
        return self.tiles[y][x] == '#'

class Entity:
    def __init__(self, x, y, char, color, name, hp=10, atk=3, defense=1, level=1, xp=0):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.atk = atk
        self.defense = defense
        self.level = level
        self.xp = xp

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
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.running = True
        init_colors()
        curses.curs_set(0)
        self.stdscr.nodelay(True)

        self.screen_height, self.screen_width = self.stdscr.getmaxyx()
        self.map_width = self.screen_width
        self.map_height = self.screen_height - 6

        self.depth = 1
        self.dungeon_map = Map(self.map_width, self.map_height)
        self.dungeon_map.generate_map()

        start_room_center = self.dungeon_map.rooms[0].center()
        self.player = Entity(start_room_center[0], start_room_center[1], '@', COLOR_NEON_GREEN, "Player", hp=20, atk=5, defense=2)
        self.entities = [self.player]
        self.messages = ["Welcome to the Neon Dungeon!"]

        self.spawn_level_content()

    def next_level(self):
        self.depth += 1
        self.message(f"Descending to level {self.depth}...")
        self.dungeon_map.generate_map()

        start_room_center = self.dungeon_map.rooms[0].center()
        self.player.x, self.player.y = start_room_center
        self.entities = [self.player]

        self.spawn_level_content()

    def spawn_level_content(self):
        self.spawn_enemies()
        self.spawn_items()

    def update_fov(self):
        radius = 5
        for y in range(max(0, self.player.y - radius), min(self.map_height, self.player.y + radius + 1)):
            for x in range(max(0, self.player.x - radius), min(self.map_width, self.player.x + radius + 1)):
                self.dungeon_map.explored[y][x] = True

    def spawn_items(self):
        for room in self.dungeon_map.rooms[1:]:
            if random.randint(0, 100) < 40:
                x, y = room.center()
                if any(e.x == x and e.y == y for e in self.entities):
                    x += 1

                roll = random.randint(0, 100)
                if roll < 60:
                    item = Entity(x, y, '*', COLOR_NEON_YELLOW, "Neon Battery", hp=0, atk=0, defense=0)
                    item.item_type = 'heal'
                elif roll < 85:
                    item = Entity(x, y, '!', COLOR_NEON_CYAN, "Power Cell", hp=0, atk=0, defense=0)
                    item.item_type = 'atk'
                else:
                    item = Entity(x, y, '[', COLOR_NEON_MAGENTA, "Cyber Shield", hp=0, atk=0, defense=0)
                    item.item_type = 'def'

                item.is_item = True
                self.entities.append(item)

    def spawn_enemies(self):
        for room in self.dungeon_map.rooms[1:]:
            if random.randint(0, 100) < 70 + self.depth * 2:
                x, y = room.center()

                roll = random.randint(0, 100)
                if roll < 60:
                    enemy = Entity(x, y, 'g', COLOR_NEON_RED, "Glitch",
                                   hp=8 + self.depth * 2, atk=2 + self.depth, defense=1 + self.depth // 2)
                elif roll < 85:
                    enemy = Entity(x, y, 'T', COLOR_NEON_MAGENTA, "Tank-Bot",
                                   hp=20 + self.depth * 4, atk=1 + self.depth, defense=3 + self.depth)
                else:
                    enemy = Entity(x, y, 'S', COLOR_NEON_YELLOW, "Stalker",
                                   hp=5 + self.depth, atk=5 + self.depth * 2, defense=0)

                self.entities.append(enemy)

    def message(self, text):
        self.messages.append(text)
        if len(self.messages) > 3:
            self.messages.pop(0)

    def save_game(self):
        save_data = {
            "depth": self.depth,
            "player": {
                "x": self.player.x,
                "y": self.player.y,
                "hp": self.player.hp,
                "max_hp": self.player.max_hp,
                "atk": self.player.atk,
                "defense": self.player.defense,
                "level": self.player.level,
                "xp": self.player.xp
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
                    "item_type": getattr(e, 'item_type', None)
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

        self.depth = save_data.get("depth", 1)
        map_data = save_data["map"]
        self.dungeon_map = Map(map_data["width"], map_data["height"])
        self.dungeon_map.tiles = map_data["tiles"]
        self.dungeon_map.explored = map_data.get("explored", [[False for _ in range(self.dungeon_map.width)] for _ in range(self.dungeon_map.height)])

        p_data = save_data["player"]
        self.player = Entity(p_data["x"], p_data["y"], '@', COLOR_NEON_GREEN, "Player",
                             hp=p_data["hp"], atk=p_data["atk"], defense=p_data["defense"],
                             level=p_data["level"], xp=p_data["xp"])
        self.player.max_hp = p_data["max_hp"]

        self.entities = [self.player]
        for e_data in save_data["entities"]:
            entity = Entity(e_data["x"], e_data["y"], e_data["char"], e_data["color"], e_data["name"],
                            hp=e_data["hp"], atk=e_data["atk"], defense=e_data["defense"])
            entity.max_hp = e_data["max_hp"]
            if e_data.get("is_item"):
                entity.is_item = True
                entity.item_type = e_data.get("item_type")
            self.entities.append(entity)

        self.message("Game Loaded!")

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
                else:
                    self.attack(self.player, target)

            # Check for stairs after movement
            if self.dungeon_map.tiles[self.player.y][self.player.x] == '>':
                self.next_level()
            else:
                self.enemy_turn()

    def pick_up(self, item):
        if item.item_type == 'heal':
            self.message(f"Picked up {item.name}! +10 HP.")
            self.player.hp = min(self.player.max_hp, self.player.hp + 10)
        elif item.item_type == 'atk':
            self.message(f"Picked up {item.name}! +1 ATK.")
            self.player.atk += 1
        elif item.item_type == 'def':
            self.message(f"Picked up {item.name}! +1 DEF.")
            self.player.defense += 1
        self.entities.remove(item)

    def attack(self, attacker, target):
        damage = max(0, attacker.atk - target.defense)
        target.hp -= damage
        self.message(f"{attacker.name} hits {target.name} for {damage}!")
        if target.hp <= 0:
            self.message(f"{target.name} dies!")
            if target != self.player:
                self.entities.remove(target)
                attacker.xp += 5
                if attacker.xp >= attacker.level * 10:
                    self.level_up(attacker)

    def level_up(self, entity):
        entity.level += 1
        entity.xp = 0
        entity.max_hp += 5
        entity.hp = entity.max_hp
        entity.atk += 2
        entity.defense += 1
        self.message(f"{entity.name} leveled up to {entity.level}!")

    def enemy_turn(self):
        for entity in self.entities:
            if entity == self.player or hasattr(entity, 'is_item'):
                continue

            dx = 0
            dy = 0
            if entity.x < self.player.x: dx = 1
            elif entity.x > self.player.x: dx = -1
            elif entity.y < self.player.y: dy = 1
            elif entity.y > self.player.y: dy = -1

            target = entity.move(dx, dy, self.dungeon_map, self.entities)
            if target == self.player:
                self.attack(entity, self.player)

    def update(self):
        if self.player.hp <= 0:
            if "GAME OVER" not in self.messages[-1]:
                self.message("GAME OVER! Press 'q' to quit.")
            self.player.char = 'X'

    def draw(self):
        self.stdscr.erase()

        # Draw Map
        for y in range(min(self.map_height, self.screen_height)):
            for x in range(min(self.map_width, self.screen_width)):
                if y == self.screen_height - 1 and x == self.screen_width - 1:
                    continue

                if not self.dungeon_map.explored[y][x]:
                    continue

                char = self.dungeon_map.tiles[y][x]
                color = curses.color_pair(COLOR_NEON_CYAN)

                dist = abs(self.player.x - x) + abs(self.player.y - y)
                is_visible = dist < 7

                if char == '#':
                    color = curses.color_pair(COLOR_NEON_MAGENTA)
                elif char == '>':
                    color = curses.color_pair(COLOR_NEON_YELLOW) | curses.A_BOLD

                try:
                    self.stdscr.addch(y, x, char, color)
                except curses.error:
                    pass

        # Draw Entities
        for entity in self.entities:
            if not self.dungeon_map.explored[entity.y][entity.x]:
                continue

            dist = abs(self.player.x - entity.x) + abs(self.player.y - entity.y)
            if dist > 7 and entity != self.player:
                continue

            if 0 <= entity.x < self.screen_width and 0 <= entity.y < self.screen_height:
                if entity.y == self.screen_height - 1 and entity.x == self.screen_width - 1:
                    continue
                try:
                    self.stdscr.addch(entity.y, entity.x, entity.char, curses.color_pair(entity.color) | curses.A_BOLD)
                except curses.error:
                    pass

        # Draw UI
        ui_y = self.map_height + 1
        if ui_y < self.screen_height:
            header = f"NEON DUNGEON CLI | DEPTH: {self.depth}"
            self.stdscr.addstr(ui_y, 0, header[:self.screen_width-1], curses.color_pair(COLOR_NEON_YELLOW) | curses.A_BOLD)
        if ui_y + 1 < self.screen_height:
            stats = f"LVL: {self.player.level} | HP: {self.player.hp}/{self.player.max_hp} | ATK: {self.player.atk} | DEF: {self.player.defense} | XP: {self.player.xp}/{self.player.level*10}"
            self.stdscr.addstr(ui_y + 1, 0, stats[:self.screen_width-1], curses.color_pair(COLOR_NEON_CYAN))
        if ui_y + 2 < self.screen_height:
            controls = "Controls: WASD/Arrows to Move | 'v' Save | 'l' Load | 'q' Quit"
            self.stdscr.addstr(ui_y + 2, 0, controls[:self.screen_width-1], curses.color_pair(COLOR_NEON_MAGENTA))

        for i, msg in enumerate(self.messages):
            if ui_y + 3 + i < self.screen_height:
                self.stdscr.addstr(ui_y + 3 + i, 0, msg[:self.screen_width-1], curses.color_pair(COLOR_NEON_YELLOW))

        self.stdscr.refresh()

    def run(self):
        while self.running:
            self.update_fov()
            self.handle_input()
            self.update()
            self.draw()
            curses.napms(33) # ~30 FPS

def main(stdscr):
    game = Game(stdscr)
    game.run()

if __name__ == "__main__":
    curses.wrapper(main)
