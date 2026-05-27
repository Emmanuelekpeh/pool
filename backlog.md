# Evolutionary Billiards Backlog & Architecture

## Architecture & Tech Stack
- **Physics**: Pymunk (stable collisions, momentum)
- **Rendering**: Pygame (fast iteration, visual overlays)
- **AI/Brains**: PyTorch (CPU only, as per system constraints)
- **Core Loop**: Physics at 120 FPS, Agent decisions at 5-10 Hz.

## MVP Progression (Phases)
- [x] **Phase 1: Single Ball Survival**
  - Setup Pymunk + Pygame environment (walls, pockets, single ball).
  - Implement basic MLP policy (Inputs: pos, vel, wall dist, pocket dist. Outputs: angle, force).
  - Train agent to avoid holes (Reward: survival +, falling in -).
- [x] **Phase 2: Static Enemies**
  - Add static enemy balls.
  - Update inputs to include enemy positions.
  - Train agent to hit enemies into holes (Reward: enemy sunk +, self sunk -).
- [x] **Phase 3: Moving Enemies**
  - Enemies have basic movement/physics.
- [x] **Phase 4: Director Network**
  - Implement the "Loss Director" to evaluate state desirability and learning usefulness.
- [x] **Phase 5: Multi-Agent Evolution (Self-Play)**
  - 8 independent agents with persistent identities, weights, and memories.
  - Evolutionary mutation for worst performers.

## System Structure
- `main.py`: Entry point, runs the simulation loop.
- `world.py`: Manages the pool table, pockets, and boundaries.
- `physics.py`: Pymunk integration.
- `renderer.py`: Pygame rendering and visual overlays.
- `models/policy.py`: PyTorch MLP for agent decisions.
- `training/rewards.py`: Reward calculation logic.
- `training/replay_buffer.py`: Memory for training.
