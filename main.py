import pygame
import torch
import random
from physics import create_space, create_ball
from world import setup_table, COLLISION_TYPE_BALL, COLLISION_TYPE_POCKET, COLLISION_TYPE_WALL, WIDTH, HEIGHT
from renderer import Renderer
from models.agent import Agent
from training.evolution import mutate_network, mesh_networks
from models.director import DirectorNetwork
from models.policy import PolicyNetwork

NUM_AGENTS = 8
MAX_STEPS = 1200
EVALUATION_EPISODES = 5

BALL_COLORS = [
    (255, 215, 0, 255),   # 1: Yellow
    (0, 0, 255, 255),     # 2: Blue
    (255, 0, 0, 255),     # 3: Red
    (128, 0, 128, 255),   # 4: Purple
    (255, 165, 0, 255),   # 5: Orange
    (0, 128, 0, 255),     # 6: Green
    (128, 0, 0, 255),     # 7: Maroon
    (0, 0, 0, 255),       # 8: Black
]

class Player:
    def __init__(self, body, shape):
        self.id = 99
        self.color = (255, 255, 255, 255)
        self.body = body
        self.shape = shape
        self.alive = True
        self.fitness = 0
        self.enemies_sunk = 0
        self.last_hit_by = None
        self.last_hit_step = 0

def run_episode(agents, renderer=None, player_wants_to_play=True, show_thoughts=False):
    space = create_space()
    setup_table(space)
    
    # Initialize bodies for all agents
    for agent in agents:
        x = random.uniform(100, WIDTH-100)
        y = random.uniform(100, HEIGHT-100)
        body, shape = create_ball(space, (x, y), collision_type=COLLISION_TYPE_BALL)
        shape.color = pygame.Color(*agent.color)
        agent.body = body
        agent.shape = shape
        agent.alive = True
        agent.fitness = 0
        agent.enemies_sunk = 0
        agent.last_hit_by = None
        agent.last_hit_step = 0
        body.apply_impulse_at_local_point((random.uniform(-300, 300), random.uniform(-300, 300)))
        
    # Initialize Player (White Ball)
    px = random.uniform(100, WIDTH-100)
    py = random.uniform(100, HEIGHT-100)
    player_body, player_shape = create_ball(space, (px, py), collision_type=COLLISION_TYPE_BALL)
    player_shape.color = pygame.Color(255, 255, 255, 255)
    player = Player(player_body, player_shape)
    
    if not player_wants_to_play:
        player.alive = False
        space.remove(player.body, player.shape)
        
    all_entities = agents + [player]
        
    to_remove = []
    
    def ball_pocket_collision(arbiter, space, data):
        shape = arbiter.shapes[0]
        for entity in all_entities:
            if entity.shape == shape and entity.alive:
                entity.alive = False
                to_remove.append(entity)
                
                # Huge negative for sinking yourself
                entity.fitness -= 500
                
                # Reward the opponent who knocked you in, if it was recent (within 2 seconds / 240 steps)
                if entity.last_hit_by and entity.last_hit_by.alive:
                    if steps - entity.last_hit_step < 240:
                        entity.last_hit_by.fitness += 1000
                        entity.last_hit_by.enemies_sunk += 1
                    
        return False
        
    def ball_ball_collision(arbiter, space, data):
        shape_a, shape_b = arbiter.shapes
        entity_a = next((e for e in all_entities if e.shape == shape_a), None)
        entity_b = next((e for e in all_entities if e.shape == shape_b), None)
        
        if entity_a and entity_b:
            entity_a.last_hit_by = entity_b
            entity_a.last_hit_step = steps
            entity_b.last_hit_by = entity_a
            entity_b.last_hit_step = steps
            if hasattr(entity_a, 'recent_ball_collision'):
                entity_a.recent_ball_collision = 1.0
            if hasattr(entity_b, 'recent_ball_collision'):
                entity_b.recent_ball_collision = 1.0
            
        return True # Continue with normal physics resolution
        
    def ball_wall_collision(arbiter, space, data):
        shape = arbiter.shapes[0]
        entity = next((e for e in all_entities if e.shape == shape), None)
        if entity and hasattr(entity, 'recent_wall_collision'):
            entity.recent_wall_collision = 1.0
        return True
        
    handler_pocket = space.add_collision_handler(COLLISION_TYPE_BALL, COLLISION_TYPE_POCKET)
    handler_pocket.begin = ball_pocket_collision
    
    handler_ball = space.add_collision_handler(COLLISION_TYPE_BALL, COLLISION_TYPE_BALL)
    handler_ball.post_solve = ball_ball_collision
    
    handler_wall = space.add_collision_handler(COLLISION_TYPE_BALL, COLLISION_TYPE_WALL)
    handler_wall.post_solve = ball_wall_collision
    
    steps = 0
    decision_interval = 12
    
    player_charge = 0.0
    player_dir = [0.0, 0.0]
    charging = False
    
    while any(a.alive for a in agents) and steps < MAX_STEPS:
        if renderer:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    import sys
                    sys.exit(0)
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_t:
                        show_thoughts = not show_thoughts
                    elif event.key == pygame.K_p:
                        player_wants_to_play = not player_wants_to_play
                        if not player_wants_to_play and player.alive:
                            # Remove immediately if toggled off
                            player.alive = False
                            if player.shape in space.shapes:
                                space.remove(player.body, player.shape)
                        # If toggled ON, we don't spawn immediately. It takes effect next round.

            keys = pygame.key.get_pressed()
            dx, dy = 0, 0
            if keys[pygame.K_w] or keys[pygame.K_UP]: dy -= 1
            if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy += 1
            if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx -= 1
            if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx += 1
            
            if (dx != 0 or dy != 0) and player.alive:
                charging = True
                player_dir = [dx, dy]
                player_charge += 15.0 # Charge rate
                player_charge = min(player_charge, 1500.0) # Max force
            elif charging:
                charging = False
                if player.alive:
                    length = (player_dir[0]**2 + player_dir[1]**2)**0.5
                    if length > 0:
                        ndx = player_dir[0] / length
                        ndy = player_dir[1] / length
                        player.body.apply_impulse_at_local_point((ndx * player_charge, ndy * player_charge))
                player_charge = 0.0
                        
        if steps % decision_interval == 0:
            step_ratio = steps / MAX_STEPS
            for agent in agents:
                if agent.alive:
                    # Treat other entities (including player) as enemies
                    enemies = [e for e in all_entities if e != agent]
                    state = agent.get_state(enemies, step_ratio)
                    action = agent.select_action(state)
                    agent.apply_action(action)
                    
        space.step(1/120.0)
        
        for entity in to_remove:
            if entity.shape in space.shapes:
                space.remove(entity.body, entity.shape)
        to_remove.clear()
        
        for agent in agents:
            if agent.alive:
                agent.fitness += 1
                
        steps += 1
        
        if renderer:
            aim_line = None
            if charging and player.alive:
                length = (player_dir[0]**2 + player_dir[1]**2)**0.5
                if length > 0:
                    ndx = player_dir[0] / length
                    ndy = player_dir[1] / length
                    # Line length proportional to charge
                    line_len = player_charge / 1500.0 * 100.0 
                    start_pos = (int(player.body.position.x), int(player.body.position.y))
                    end_pos = (int(start_pos[0] + ndx * line_len), int(start_pos[1] + ndy * line_len))
                    aim_line = (start_pos, end_pos)
            
            renderer.render(space, agents, player, aim_line, show_thoughts)
            renderer.tick(120)
            
    return player_wants_to_play, show_thoughts

import os
import torch

CHECKPOINT_DIR = "checkpoints"

def save_population(agents, generation, filename="latest.pt"):
    os.makedirs(CHECKPOINT_DIR, exist_ok=True)
    data = {"generation": generation, "agents": []}
    for agent in agents:
        data["agents"].append({
            "id": agent.id,
            "color": agent.color,
            "overall_rating": agent.overall_rating,
            "policy": agent.policy.state_dict(),
            "director": agent.director.state_dict(),
            "future": agent.future.state_dict()
        })
    filepath = os.path.join(CHECKPOINT_DIR, filename)
    torch.save(data, filepath)
    print(f"Saved checkpoint to {filepath}")

def load_population(agents, filename="latest.pt"):
    filepath = os.path.join(CHECKPOINT_DIR, filename)
    if not os.path.exists(filepath):
        return 1
    data = torch.load(filepath)
    for agent, agent_data in zip(agents, data["agents"]):
        agent.id = agent_data["id"]
        agent.color = agent_data["color"]
        agent.overall_rating = agent_data["overall_rating"]
        agent.policy.load_state_dict(agent_data["policy"])
        agent.director.load_state_dict(agent_data["director"])
        agent.future.load_state_dict(agent_data["future"])
    print(f"Loaded checkpoint from {filepath} (Generation {data['generation']})")
    return data["generation"]

def main():
    renderer = Renderer()
    
    # Initialize 8 distinct agents
    agents = []
    for i in range(NUM_AGENTS):
        # Create dummy body/shape just to initialize the Agent object
        space = create_space()
        body, shape = create_ball(space, (0, 0))
        color = BALL_COLORS[i % len(BALL_COLORS)]
        agent = Agent(body, shape, agent_id=i+1, color=color)
        agents.append(agent)
        
    generation = load_population(agents)
    player_wants_to_play = True
    show_thoughts = False
    
    while True:
        print(f"--- Generation {generation} (Evaluating over {EVALUATION_EPISODES} episodes) ---")
        
        for ep in range(EVALUATION_EPISODES):
            # Render all episodes if renderer is available
            player_wants_to_play, show_thoughts = run_episode(agents, renderer, player_wants_to_play, show_thoughts)
            
            for agent in agents:
                agent.fitness_history.append(agent.fitness)
        
        # Print results based on average fitness
        agents.sort(key=lambda a: sum(a.fitness_history)/EVALUATION_EPISODES, reverse=True)
        for i, agent in enumerate(agents):
            avg_fit = sum(agent.fitness_history)/EVALUATION_EPISODES
            agent.overall_rating = avg_fit # Update their internal overall rating
            print(f"Rank {i+1}: Agent {agent.id} - Avg Fitness {avg_fit:.1f}")
            
        # Evolution: Bottom 4 inherit from Top 4
        top_agents = agents[:4]
        
        # 1. Top agents get a very tiny mutation to prevent absolute stagnation (explore new strategies)
        for i in range(4):
            agents[i].policy = mutate_network(agents[i].policy, mutation_rate=0.01, mutation_scale=0.02)
            
        # 2. Bottom 4 get replaced
        for i in range(4, 8):
            agent = agents[i]
            parent1, parent2 = random.sample(top_agents, 2)
            
            # Policy: Fast adaptation via meshing two successful parents + higher mutation
            agent.policy = mesh_networks(parent1.policy, parent2.policy, mutation_rate=0.1, mutation_scale=0.1)
            
            # Director & Future: Inherit from primary parent.
            # We add moderate noise to create a variant of the successful worldview.
            # 20% of the time, we inject MASSIVE noise to force a "paradigm shift" and discover completely new tactics.
            if random.random() < 0.20:
                # Paradigm Shift: High mutation rate and scale
                agent.director = mutate_network(parent1.director, mutation_rate=0.15, mutation_scale=0.3)
                agent.future = mutate_network(parent1.future, mutation_rate=0.15, mutation_scale=0.3)
                shift_msg = " [PARADIGM SHIFT!]"
            else:
                # Normal Drift: Moderate noise
                agent.director = mutate_network(parent1.director, mutation_rate=0.05, mutation_scale=0.1)
                agent.future = mutate_network(parent1.future, mutation_rate=0.05, mutation_scale=0.1)
                shift_msg = ""
            
            print(f"Agent {agent.id} inherited worldview from Agent {parent1.id}, policy meshed with Agent {parent2.id}{shift_msg}")
            
        # Clear history for next generation
        for agent in agents:
            agent.fitness_history.clear()
            
        generation += 1
        save_population(agents, generation)

if __name__ == "__main__":
    main()
