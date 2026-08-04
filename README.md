# World 1-1

A local multiplayer platform fighter inspired by Super Smash Bros., built with Python and Pygame. Features 4 playable characters, 2 stages, NPC enemies, AI opponents, and full controller support.

## Features

- **4 Characters**: Mario, Luigi, Yoshi, Donkey Kong — each with unique stats, sprites, and movesets
- **2 Stages**: World 1-1 (classic pipes & platforms) and Factory (hazards, bullet bill cannons)
- **Game Modes**: Local 2-player, CPU vs CPU, and Tutorial
- **NPC Enemies**: Goombas, Koopas, Shy Guys, Buzzy Beetles, Bullet Bills, and Kamek
- **Combat System**: Smash-style knockback, combo system, shield, DI (directional influence), counter-hits, L-canceling, and rage scaling
- **Controller Support**: Xbox/PS4 controllers via DS4Windows (Windows), keyboard + mouse
- **Particle Effects**: Hit sparks, KO explosions, dust, shield hits, blast-zone ring explosions

## Installation

```bash
# Clone the repository
git clone https://github.com/your-username/Mario_multiplayer.git
cd Mario_multiplayer

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

### Requirements

- Python 3.8+
- pygame 2.1+

## Controls

### Keyboard (Player 1)
| Action | Key |
|--------|-----|
| Move | A/D |
| Jump | W |
| Crouch | S |
| Light Attack | F |
| Heavy Attack | G |
| Special | E |
| Shield | Q |

### Keyboard (Player 2)
| Action | Key |
|--------|-----|
| Move | Arrow Keys |
| Jump | Up Arrow |
| Crouch | Down Arrow |
| Light Attack | J |
| Heavy Attack | K |
| Special | O |
| Shield | P |

### Controller (DS4Windows / Xbox)
| Action | Button |
|--------|--------|
| Jump | A / X (PS4) |
| Light Attack | X / Square (PS4) |
| Heavy Attack | B / Circle (PS4) |
| Special | Y / Triangle (PS4) |
| Shield | LB / L1 (PS4) |

### Menu Navigation
| Action | Keyboard | Controller |
|--------|----------|------------|
| Confirm | Enter | O (Circle) |
| Cancel/Back | Escape | X (Cross) |
| Navigate | Arrow Keys / WASD | D-Pad / Left Stick |

## Known Limitations

- **PS4 Controller**: Requires DS4Windows on Windows for full support. Auto-detection and setup is Windows-only.
- **Platform**: Tested primarily on Windows. macOS and Linux should work for keyboard/mouse gameplay, but controller auto-setup is not available.
- **Local Multiplayer Only**: Online multiplayer is not yet implemented.

## Credits

Sprites by: JumpmanMFFG, Chrispriter, Squishy Rex, Rogultgot, NO Body, BidBood, ChaoticYoshi, DotStudio, VannyArts, Avi, Mageker, Racoon Sam, Yoshiguy

## License

MIT License — see [LICENSE](LICENSE) for details.
