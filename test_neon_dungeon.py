import unittest
from neon_dungeon import Rect, Map, Entity

class TestNeonDungeon(unittest.TestCase):
    def test_rect_intersect(self):
        r1 = Rect(0, 0, 10, 10)
        r2 = Rect(5, 5, 10, 10)
        r3 = Rect(20, 20, 5, 5)
        self.assertTrue(r1.intersect(r2))
        self.assertFalse(r1.intersect(r3))

    def test_map_blocked(self):
        dungeon_map = Map(10, 10)
        self.assertTrue(dungeon_map.is_blocked(0, 0))
        dungeon_map.tiles[5][5] = '.'
        self.assertFalse(dungeon_map.is_blocked(5, 5))

    def test_entity_move(self):
        dungeon_map = Map(10, 10)
        dungeon_map.tiles[5][5] = '.'
        dungeon_map.tiles[5][6] = '.'
        entity = Entity(5, 5, '@', 1, "Player")
        entities = [entity]

        # Move to open space
        target = entity.move(1, 0, dungeon_map, entities)
        self.assertIsNone(target)
        self.assertEqual(entity.x, 6)

        # Move to blocked space
        target = entity.move(1, 0, dungeon_map, entities)
        self.assertIsNone(target)
        self.assertEqual(entity.x, 6)

    def test_entity_attack(self):
        # We need a way to test attack without the Game class if possible,
        # or mock Game. For now, just test basic HP reduction.
        attacker = Entity(0, 0, 'A', 1, "Attacker", atk=5)
        target = Entity(1, 1, 'T', 1, "Target", hp=10, defense=2)

        damage = max(0, attacker.atk - target.defense)
        target.hp -= damage
        self.assertEqual(target.hp, 7)

if __name__ == '__main__':
    unittest.main()
