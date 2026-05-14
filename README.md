# Neon Dungeon CLI

Neon Dungeon CLI is an offline Python terminal roguelite where the player explores a cyberpunk dungeon, fights corrupted enemies, collects loot, upgrades gear, discovers events, defeats bosses, and tries to survive to Floor 25.

## Features

- **Cyberpunk Roguelite:** Explore a neon-lit dungeon filled with glitchy enemies and advanced tech.
- **Classes:** Choose from Hacker, Runner, Tank, or Glitch Mage, each with unique starting stats and skills.
- **Combat:** Turn-based combat featuring weapons, skills, dodges, and crits.
- **Loot & Upgrades:** Collect credits to buy items and gear at shop terminals.
- **Mystery Events:** Encounter random scenarios that offer risks and rewards.
- **Codex:** Track your discovered enemies, items, and classes across all runs.
- **Best Runs:** Save and view your most successful attempts.
- **Offline & Safe:** Completely offline. No tracking, no ads, no API keys, no login, no paywalls. All data is saved locally.
- **Free & Open Source:** The game is fully open source and free forever.

## How to Run

1. Clone the repository.
2. Ensure you have Python 3 installed. No external dependencies are required.
3. Run the game from the terminal:

```bash
python3 neon_dungeon.py
```

## Controls

The game is played entirely through your keyboard by typing in numbered choices or simple commands at the prompt. Just follow the on-screen instructions!

## Classes

- **Hacker:** Balanced. Starts with the *Data Spike* skill (ignores some defense).
- **Runner:** Faster, higher dodge chance. Starts with the *Phase Dash* skill (high dodge for one turn).
- **Tank:** More HP and defense. Starts with the *Shield Wall* skill (reduces incoming damage).
- **Glitch Mage:** Lower HP, stronger special skill. Starts with the *Byte Storm* skill (deals massive damage but costs HP).

## Save Files

Your save data is stored locally in the `neon_dungeon_data` folder in the project directory:
- `save.json`: Your active run.
- `best_runs.json`: Your past run records.
- `codex.json`: Discoveries.

You can safely delete this folder to completely reset your progress.

## Privacy Note

Neon Dungeon CLI respects your privacy. It requires no internet connection, no accounts, and performs no tracking. Everything happens locally on your machine.

## Roadmap

Future planned features:
- Curses visual mode
- Richer ASCII map mode
- More classes
- Skill tree
- Achievements
- Daily dungeon seed
- Optional donations later
