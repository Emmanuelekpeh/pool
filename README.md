# Evolutionary Billiards

A continuous physics simulation where 8 independent AI agents learn to play a survival-based billiards game through neuroevolution, self-play, and internal latent simulation. 

You can also drop into the arena as a 9th player to test your skills against the evolving AI ecosystem.

## Core Concept

This project explores **Learned Optimization Signals** and **Internal Continuous Simulation**. 

Instead of a standard Reinforcement Learning setup where agents react to a fixed reward function, these agents possess three distinct neural networks:
1. **PolicyNetwork (The Actor):** Proposes physical actions (force vectors).
2. **FutureNetwork (The Oracle):** Takes the current state and a proposed action, and predicts the future state of the table (including opponent positions and intent).
3. **DirectorNetwork (The Critic/Worldview):** Evaluates the "cognitive quality" and strategic value of the imagined future state.

Before taking a shot, an agent generates multiple candidate actions, uses its `FutureNetwork` to imagine the outcomes, and uses its `DirectorNetwork` to score those futures. It then executes the action that leads to the highest-scoring imagined future.

## Evolutionary Mechanics

The agents evolve over generations (blocks of 5 episodes) using a custom **Hierarchical Mutation** and **Weight Meshing** system:

- **The Elite (Top 4):** Survive to the next generation with a tiny mutation rate (1%) to prevent absolute stagnation.
- **The Failures (Bottom 4):** 
  - **Skill Exchange:** Their `PolicyNetwork` is replaced by a 50/50 "weight mesh" (crossover) of two successful parents, allowing them to rapidly adopt proven physical skills.
  - **Worldview Inheritance:** Their `Director` and `Future` networks (their "identity anchors") are inherited from a successful parent with a slow mutation drift (5%).
  - **Paradigm Shifts:** 20% of the time, failing agents undergo a "Paradigm Shift" where their inherited worldview is hit with massive noise (15% mutation rate, high scale). This forces the discovery of completely alien, non-human strategies (like sacrificial positioning or corner traps).

## Setup & Installation

This project is designed to run entirely on the CPU.

```bash
# Create a virtual environment (optional but recommended)
python -m venv venv
source venv/Scripts/activate  # On Windows

# Install dependencies
pip install pygame pymunk torch
```

## Running the Simulation

```bash
python main.py
```

The simulation will automatically load the latest weights from the `checkpoints/` directory if they exist, allowing you to seamlessly resume evolution.

## Player Controls

You can participate in the evolutionary arena as the **White Ball (P)**. The AI agents are fully aware of your presence, velocity, and score, and will attempt to knock you into the pockets.

- **Movement / Aiming:** Press and hold `W`, `A`, `S`, `D` (or Arrow Keys) to aim.
- **Charging:** The longer you hold the movement keys, the longer the white aim line grows, representing the stored force of your shot.
- **Shooting:** Release all movement keys to fire.
- **Toggle Presence:** Press `P` at any time to toggle your presence. If you toggle off, you will immediately vanish. If you toggle on, you will spawn at the start of the next episode.

## Scoring System

- **Survival:** +1 point per step survived.
- **Self-Destruct:** -500 points for falling into a pocket.
- **Aggression:** +1000 points for knocking an opponent into a pocket (credit is awarded to the last agent to hit the victim, provided the hit occurred within the last 2 seconds).

## Architecture Details

- **Physics Engine:** `pymunk` (120 FPS for stable collisions and momentum transfer).
- **Renderer:** `pygame` (Visualizes the table, agent IDs, and player aim lines).
- **Neural Networks:** `PyTorch` (CPU-bound).
- **Decision Frequency:** Agents make decisions at 10 Hz (every 12 physics steps) to prevent twitchy, chaotic behavior and encourage strategic, deliberate shots.
