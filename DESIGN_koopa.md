# Koopa Troopa (Green) - World 1-1

## State Machine

### State 1: Walking Enemy (Default)
- **Speed:** 0.5 px/frame (30 px/sec NTSC)
- **Edge handling:** No edge detection. Falls off ledges with gravity.
- **Mario collision from above:** If Mario's vy > 0 and bottom intersects Koopa top → Koopa enters State 2, Mario bounces up (reverse vy).
- **Mario collision from sides/bottom:** Mario takes damage/dies.

### State 2: Stationary Shell
- **Speed:** 0
- **Wake-up timer:** 4-5 seconds countdown. When expires → animates legs briefly → transitions back to State 1.
- **Mario collision (side):** No damage. Kicks shell: if Mario is left, shell goes right (+vx). If Mario is right, shell goes left (-vx). Transitions to State 3.

### State 3: Moving Shell (Kicked)
- **Speed:** 3.0 px/frame (high constant)
- **Wall bounce:** Hits solid tile from side → invert vx.
- **Enemy collision:** Overlaps any enemy → instantly kills that enemy + score popup.
- **Mario collision (side):** Mario takes damage.
- **Mario collision (top):** Mario jumps on top → shell halts, reverts to State 2.
