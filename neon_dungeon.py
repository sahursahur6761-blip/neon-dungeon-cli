import curses
import json
import random
import os

# Constants
MAP_WIDTH = 80
MAP_HEIGHT = 20
UI_HEIGHT = 7
MSG_LOG_SIZE = 5

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

class Tile:
    def __init__(self, blocked, block_sight=None):
        self.blocked = blocked
        if block_sight is None: block_sight = blocked
        self.block_sight = block_sight
        self.explored = False

class Entity:
    def __init__(self, x, y, char, color, name, blocks=False, ai=None, fighter=None, item=None):
        self.x = x
        self.y = y
        self.char = char
        self.color = color
        self.name = name
        self.blocks = blocks
        self.ai = ai
        self.fighter = fighter
        self.item = item
        if self.fighter:
            self.fighter.owner = self
        if self.ai:
            self.ai.owner = self
        if self.item:
            self.item.owner = self

    def move(self, dx, dy, game_map, entities):
        if not game_map.tiles[self.x + dx][self.y + dy].blocked:
            if not get_blocking_entities_at_location(entities, self.x + dx, self.y + dy):
                self.x += dx
                self.y += dy

class Fighter:
    def __init__(self, hp, defense, power, xp_reward=0):
        self.max_hp = hp
        self.hp = hp
        self.defense = defense
        self.power = power
        self.xp_reward = xp_reward

    def take_damage(self, amount):
        self.hp -= amount
        if self.hp <= 0:
            self.hp = 0

    def attack(self, target, game):
        damage = self.power - target.fighter.defense
        if damage > 0:
            target.fighter.take_damage(damage)
            game.log_message(f"{self.owner.name} attacks {target.name} for {damage} hit points.")
            if target.fighter.hp <= 0:
                game.log_message(f"{target.name} is dead!")
                if self.owner == game.player:
                    self.owner.xp += target.fighter.xp_reward
                    game.check_level_up()
        else:
            game.log_message(f"{self.owner.name} attacks {target.name} but does no damage.")

class BasicMonster:
    def take_turn(self, player, game_map, entities, game):
        monster = self.owner
        # Move towards player if in range (simple AI)
        if abs(monster.x - player.x) <= 5 and abs(monster.y - player.y) <= 5:
            dx = 1 if player.x > monster.x else -1 if player.x < monster.x else 0
            dy = 1 if player.y > monster.y else -1 if player.y < monster.y else 0

            target = get_blocking_entities_at_location(entities, monster.x + dx, monster.y + dy)
            if target == player:
                monster.fighter.attack(player, game)
            elif not target:
                monster.move(dx, dy, game_map, entities)

class Item:
    def __init__(self, use_function=None, amount=0):
        self.use_function = use_function
        self.amount = amount

    def pick_up(self, player, entities, game):
        game.log_message(f"You picked up a {self.owner.name}!")
        player.inventory.append(self.owner)
        entities.remove(self.owner)

    def use(self, player, game):
        if self.use_function:
            self.use_function(player, self.amount, game)
            player.inventory.remove(self.owner)

def heal(player, amount, game):
    if player.fighter.hp == player.fighter.max_hp:
        game.log_message("You are already at full health.")
        return
    player.fighter.hp = min(player.fighter.hp + amount, player.fighter.max_hp)
    game.log_message(f"Your wounds start to feel better! Healed {amount} HP.")

def get_blocking_entities_at_location(entities, destination_x, destination_y):
    for entity in entities:
        if entity.blocks and entity.x == destination_x and entity.y == destination_y:
            return entity
    return None

class Map:
    def __init__(self):
        self.width = MAP_WIDTH
        self.height = MAP_HEIGHT
        self.tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]
        self.rooms = []

    def create_room(self, room):
        for x in range(room.x1 + 1, room.x2):
            for y in range(room.y1 + 1, room.y2):
                self.tiles[x][y].blocked = False
                self.tiles[x][y].block_sight = False

    def create_h_tunnel(self, x1, x2, y):
        for x in range(min(x1, x2), max(x1, x2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def create_v_tunnel(self, y1, y2, x):
        for y in range(min(y1, y2), max(y1, y2) + 1):
            self.tiles[x][y].blocked = False
            self.tiles[x][y].block_sight = False

    def generate_dungeon(self, entities):
        self.tiles = [[Tile(True) for y in range(self.height)] for x in range(self.width)]
        self.rooms = []
        max_rooms = 15
        room_min_size = 5
        room_max_size = 10

        for r in range(max_rooms):
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

                if len(self.rooms) == 0:
                    self.start_pos = (new_x, new_y)
                else:
                    (prev_x, prev_y) = self.rooms[len(self.rooms)-1].center()
                    if random.randint(0, 1) == 1:
                        self.create_h_tunnel(prev_x, new_x, prev_y)
                        self.create_v_tunnel(prev_y, new_y, new_x)
                    else:
                        self.create_v_tunnel(prev_y, new_y, prev_x)
                        self.create_h_tunnel(prev_x, new_x, new_y)

                self.place_entities(new_room, entities)
                self.rooms.append(new_room)

        # Add stairs in the last room
        last_room = self.rooms[-1]
        sx, sy = last_room.center()
        stairs = Entity(sx, sy, '>', 3, 'Stairs', blocks=False)
        entities.append(stairs)
        self.stairs_pos = (sx, sy)

    def place_entities(self, room, entities):
        number_of_monsters = random.randint(0, 2)
        for i in range(number_of_monsters):
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)

            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                if random.randint(0, 100) < 80:
                    fighter_component = Fighter(hp=10, defense=0, power=3, xp_reward=35)
                    ai_component = BasicMonster()
                    monster = Entity(x, y, 'o', 2, 'Orc', blocks=True, ai=ai_component, fighter=fighter_component)
                else:
                    fighter_component = Fighter(hp=16, defense=1, power=4, xp_reward=100)
                    ai_component = BasicMonster()
                    monster = Entity(x, y, 'T', 2, 'Troll', blocks=True, ai=ai_component, fighter=fighter_component)
                entities.append(monster)

        number_of_items = random.randint(0, 1)
        for i in range(number_of_items):
            x = random.randint(room.x1 + 1, room.x2 - 1)
            y = random.randint(room.y1 + 1, room.y2 - 1)
            if not any([entity for entity in entities if entity.x == x and entity.y == y]):
                item_component = Item(use_function=heal, amount=10)
                item = Entity(x, y, '!', 4, 'Healing Potion', item=item_component)
                entities.append(item)

class Game:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.message_log = []
        self.setup_curses()

        self.entities = []
        self.map = Map()
        self.map.generate_dungeon(self.entities)

        px, py = self.map.start_pos
        fighter_component = Fighter(hp=30, defense=2, power=5)
        self.player = Entity(px, py, "@", 1, "Player", blocks=True, fighter=fighter_component)
        self.player.level = 1
        self.player.xp = 0
        self.player.inventory = []
        self.player.dungeon_level = 1
        self.entities.append(self.player)

        self.running = True
        self.game_state = "PLAYING"
        self.log_message("Welcome to Neon Dungeon!")

    def setup_curses(self):
        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()
        curses.init_pair(1, curses.COLOR_CYAN, -1)   # Player
        curses.init_pair(2, curses.COLOR_RED, -1)    # Enemy
        curses.init_pair(3, curses.COLOR_WHITE, -1)  # Wall/Stairs
        curses.init_pair(4, curses.COLOR_YELLOW, -1) # Item
        curses.init_pair(5, curses.COLOR_BLUE, -1)   # Floor

    def log_message(self, text):
        self.message_log.append(text)
        if len(self.message_log) > MSG_LOG_SIZE:
            self.message_log.pop(0)

    def draw(self):
        self.stdscr.clear()

        # Simple FOV
        for x in range(self.player.x - 10, self.player.x + 11):
            for y in range(self.player.y - 10, self.player.y + 11):
                if 0 <= x < self.map.width and 0 <= y < self.map.height:
                    self.map.tiles[x][y].explored = True

        # Draw map
        for x in range(self.map.width):
            for y in range(self.map.height):
                if self.map.tiles[x][y].explored:
                    is_wall = self.map.tiles[x][y].blocked
                    if is_wall:
                        self.stdscr.addch(y, x, "#", curses.color_pair(3))
                    else:
                        self.stdscr.addch(y, x, ".", curses.color_pair(5))

        # Draw entities
        for entity in sorted(self.entities, key=lambda x: x.blocks):
            if self.map.tiles[entity.x][entity.y].explored:
                self.stdscr.addch(entity.y, entity.x, entity.char, curses.color_pair(entity.color))

        # Draw UI
        sh, sw = self.stdscr.getmaxyx()

        # Status line
        status = f" HP: {self.player.fighter.hp}/{self.player.fighter.max_hp} | Lvl: {self.player.level} | XP: {self.player.xp} | Dng: {self.player.dungeon_level} "
        self.stdscr.addstr(MAP_HEIGHT, 0, status.center(sw), curses.A_REVERSE)

        # Message log
        for i, msg in enumerate(self.message_log):
            self.stdscr.addstr(MAP_HEIGHT + 1 + i, 0, f"> {msg}")

        # Controls
        controls = " [Q] Quit | [P] Save | [L] Load | [G] Get | [H] Heal | [Arrows/WASD] Move "
        self.stdscr.addstr(sh-1, 0, controls.center(sw))

        if self.game_state == "DEAD":
            self.stdscr.addstr(MAP_HEIGHT // 2, (sw - 10) // 2, " GAME OVER ", curses.A_REVERSE | curses.color_pair(2))

        self.stdscr.refresh()

    def check_level_up(self):
        xp_to_next_level = 200 + self.player.level * 150
        if self.player.xp >= xp_to_next_level:
            self.player.level += 1
            self.player.xp -= xp_to_next_level
            self.player.fighter.max_hp += 20
            self.player.fighter.hp = self.player.fighter.max_hp
            self.player.fighter.power += 1
            self.player.fighter.defense += 1
            self.log_message(f"Level up! You are now level {self.player.level}!")

    def handle_input(self):
        key = self.stdscr.getch()

        if key == ord('q'):
            self.running = False
            return "EXIT"

        if self.game_state == "DEAD":
            return "NO_ACTION"

        dx, dy = 0, 0
        if key in [curses.KEY_UP, ord('w')]: dy = -1
        elif key in [curses.KEY_DOWN, ord('s')]: dy = 1
        elif key in [curses.KEY_LEFT, ord('a')]: dx = -1
        elif key in [curses.KEY_RIGHT, ord('d')]: dx = 1
        elif key == ord('p'):
            self.save_game()
            self.log_message("Game saved.")
            return "NO_ACTION"
        elif key == ord('l'):
            self.load_game()
            return "NO_ACTION"
        elif key == ord('g'):
            for entity in self.entities:
                if entity.item and entity.x == self.player.x and entity.y == self.player.y:
                    entity.item.pick_up(self.player, self.entities, self)
                    return "PLAYER_TURN"
            self.log_message("There is nothing here to pick up.")
        elif key == ord('h'):
            for entity in self.player.inventory:
                if entity.item and entity.item.use_function == heal:
                    entity.item.use(self.player, self)
                    return "PLAYER_TURN"
            self.log_message("You don't have any healing potions.")

        if dx != 0 or dy != 0:
            target = get_blocking_entities_at_location(self.entities, self.player.x + dx, self.player.y + dy)
            if target:
                self.player.fighter.attack(target, self)
            else:
                self.player.move(dx, dy, self.map, self.entities)
                # Check for stairs
                if self.player.x == self.map.stairs_pos[0] and self.player.y == self.map.stairs_pos[1]:
                    self.next_level()
            return "PLAYER_TURN"

        return "NO_ACTION"

    def next_level(self):
        self.player.dungeon_level += 1
        self.log_message("You descend deeper into the dungeon...")
        self.entities = [self.player]
        self.map.generate_dungeon(self.entities)
        self.player.x, self.player.y = self.map.start_pos
        self.player.fighter.hp = min(self.player.fighter.hp + self.player.fighter.max_hp // 2, self.player.fighter.max_hp)

    def save_game(self):
        data = {
            "player": {
                "x": self.player.x,
                "y": self.player.y,
                "hp": self.player.fighter.hp,
                "max_hp": self.player.fighter.max_hp,
                "power": self.player.fighter.power,
                "defense": self.player.fighter.defense,
                "level": self.player.level,
                "xp": self.player.xp,
                "dungeon_level": self.player.dungeon_level,
                "inventory": [{"name": i.name, "amount": i.item.amount} for i in self.player.inventory]
            },
            "map": {
                "width": self.map.width,
                "height": self.map.height,
                "tiles": [[t.blocked for t in row] for row in self.map.tiles],
                "explored": [[t.explored for t in row] for row in self.map.tiles],
                "stairs_pos": self.map.stairs_pos
            },
            "entities": [
                {
                    "x": e.x, "y": e.y, "char": e.char, "color": e.color, "name": e.name, "blocks": e.blocks,
                    "hp": e.fighter.hp if e.fighter else None,
                    "max_hp": e.fighter.max_hp if e.fighter else None,
                    "power": e.fighter.power if e.fighter else None,
                    "defense": e.fighter.defense if e.fighter else None,
                    "xp_reward": e.fighter.xp_reward if e.fighter else None,
                    "is_item": e.item is not None,
                    "item_amount": e.item.amount if e.item else None
                } for e in self.entities if e != self.player
            ]
        }
        with open("savegame.json", "w") as f:
            json.dump(data, f)

    def load_game(self):
        if not os.path.exists("savegame.json"):
            self.log_message("No save file found.")
            return
        with open("savegame.json", "r") as f:
            data = json.load(f)

        # Load map
        m_data = data["map"]
        self.map.width = m_data["width"]
        self.map.height = m_data["height"]
        self.map.tiles = [[Tile(blocked) for blocked in row] for row in m_data["tiles"]]
        for x, explored_row in enumerate(m_data["explored"]):
            for y, explored in enumerate(explored_row):
                self.map.tiles[x][y].explored = explored
        self.map.stairs_pos = tuple(m_data["stairs_pos"])

        # Load player
        p_data = data["player"]
        self.player.x = p_data["x"]
        self.player.y = p_data["y"]
        self.player.fighter.hp = p_data["hp"]
        self.player.fighter.max_hp = p_data["max_hp"]
        self.player.fighter.power = p_data["power"]
        self.player.fighter.defense = p_data["defense"]
        self.player.level = p_data["level"]
        self.player.xp = p_data["xp"]
        self.player.dungeon_level = p_data["dungeon_level"]
        self.player.inventory = []
        for i_data in p_data["inventory"]:
            item_component = Item(use_function=heal, amount=i_data["amount"])
            item = Entity(0, 0, '!', 4, i_data["name"], item=item_component)
            self.player.inventory.append(item)

        # Load other entities
        self.entities = [self.player]
        for e_data in data["entities"]:
            fighter_component = None
            if e_data["hp"] is not None:
                fighter_component = Fighter(hp=e_data["hp"], defense=e_data["defense"], power=e_data["power"], xp_reward=e_data["xp_reward"])
                fighter_component.max_hp = e_data["max_hp"]

            ai_component = None
            if e_data["char"] in ['o', 'T']:
                ai_component = BasicMonster()

            item_component = None
            if e_data["is_item"]:
                item_component = Item(use_function=heal, amount=e_data["item_amount"])

            entity = Entity(e_data["x"], e_data["y"], e_data["char"], e_data["color"], e_data["name"],
                            blocks=e_data["blocks"], ai=ai_component, fighter=fighter_component, item=item_component)
            self.entities.append(entity)

        self.log_message("Game loaded.")

    def run(self):
        while self.running:
            self.draw()
            action = self.handle_input()

            if action == "PLAYER_TURN" and self.game_state == "PLAYING":
                for entity in self.entities:
                    if entity.ai:
                        entity.ai.take_turn(self.player, self.map, self.entities, self)

                # Check player death
                if self.player.fighter.hp <= 0:
                    self.game_state = "DEAD"
                    self.log_message("You died!")

                # Remove dead entities
                self.entities = [e for e in self.entities if e == self.player or (not e.fighter or e.fighter.hp > 0)]

def main(stdscr):
    sh, sw = stdscr.getmaxyx()
    if sh < MAP_HEIGHT + UI_HEIGHT or sw < MAP_WIDTH:
        stdscr.addstr(0, 0, f"Terminal too small! Need {MAP_WIDTH}x{MAP_HEIGHT + UI_HEIGHT}")
        stdscr.addstr(1, 0, "Press any key to exit.")
        stdscr.getch()
        return

    game = Game(stdscr)
    game.run()

if __name__ == "__main__":
    curses.wrapper(main)
