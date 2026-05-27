import torch
import math
from models.policy import PolicyNetwork
from models.director import DirectorNetwork
from models.future import FutureNetwork
from world import WIDTH, HEIGHT, POCKET_POSITIONS

class Agent:
    def __init__(self, body, shape, agent_id=0, color=(255,255,255,255), max_force=1000):
        self.id = agent_id
        self.color = color
        self.body = body
        self.shape = shape
        self.max_force = max_force
        self.policy = PolicyNetwork(input_dim=70, output_dim=2) 
        self.future = FutureNetwork(input_dim=72, output_dim=70)
        self.director = DirectorNetwork(input_dim=206) 
        self.alive = True
        self.recent_ball_collision = 0.0
        self.recent_wall_collision = 0.0
        self.last_hit_step = 0
        self.fitness_history = []
        self.fitness = 0
        self.enemies_sunk = 0
        self.last_action = [0.0, 0.0]
        self.overall_rating = 0.0
        self.thought_process = [] # Stores candidate actions, futures, and scores
        
    def get_state(self, enemies=[], step_ratio=0.0):
        # 1. Position (normalized)
        px, py = self.body.position
        norm_px = px / WIDTH
        norm_py = py / HEIGHT
        
        # 2. Velocity (normalized roughly)
        vx, vy = self.body.velocity
        norm_vx = vx / 1000.0
        norm_vy = vy / 1000.0
        
        # 3. Proprioception additions
        norm_angular_vel = self.body.angular_velocity / 20.0
        norm_fitness = self.fitness / 1000.0
        norm_overall_rating = self.overall_rating / 1000.0
        
        # 4. Distance to pockets
        pocket_dists = []
        for pocket_x, pocket_y in POCKET_POSITIONS:
            dx = (pocket_x - px) / WIDTH
            dy = (pocket_y - py) / HEIGHT
            pocket_dists.extend([dx, dy])
            
        # 5. Distance to walls
        dist_top = py / HEIGHT
        dist_bottom = (HEIGHT - py) / HEIGHT
        dist_left = px / WIDTH
        dist_right = (WIDTH - px) / WIDTH
        
        # 6. Enemies (7 enemies max, sorted by distance so we can handle >7 entities)
        enemy_states = []
        enemies_sorted = sorted(enemies, key=lambda e: (e.body.position.x - px)**2 + (e.body.position.y - py)**2)
        for enemy in enemies_sorted[:7]:
            if enemy.alive:
                epx, epy = enemy.body.position
                evx, evy = enemy.body.velocity
                edx = (epx - px) / WIDTH
                edy = (epy - py) / HEIGHT
                edvx = (evx - vx) / 1000.0
                edvy = (evy - vy) / 1000.0
                efit = enemy.fitness / 1000.0
                enemy_states.extend([edx, edy, edvx, edvy, efit, 1.0]) # 1.0 means alive
            else:
                enemy_states.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0]) # 0.0 means dead
                
        # Pad to 7 enemies
        while len(enemy_states) < 7 * 6:
            enemy_states.extend([0.0, 0.0, 0.0, 0.0, 0.0, 0.0])
            
        # 7. Recent collisions (decaying flags)
        collision_states = [self.recent_ball_collision, self.recent_wall_collision]
        
        # Decay collision flags
        self.recent_ball_collision *= 0.9
        self.recent_wall_collision *= 0.9
            
        state = [norm_px, norm_py, norm_vx, norm_vy, norm_angular_vel, self.last_action[0], self.last_action[1], norm_fitness, norm_overall_rating] + pocket_dists + [dist_top, dist_bottom, dist_left, dist_right] + enemy_states + collision_states + [step_ratio]
        return torch.tensor(state, dtype=torch.float32)
        
    def select_action(self, state):
        with torch.no_grad():
            base_action, hidden = self.policy(state)
            
            # Generate candidate actions (base + noise)
            candidates = [base_action]
            for _ in range(4):
                noise = torch.randn_like(base_action) * 0.5
                candidates.append(torch.clamp(base_action + noise, -1.0, 1.0))
                
            # Director scores candidates
            best_action = candidates[0]
            best_score = -float('inf')
            
            self.thought_process = []
            
            for action in candidates:
                future_input = torch.cat([state, action])
                predicted_future = self.future(future_input)
                director_input = torch.cat([state, action, hidden, predicted_future])
                score = self.director(director_input).item()
                
                # Store thought process for visualization
                self.thought_process.append({
                    "action": action.numpy(),
                    "future_pos": (predicted_future[0].item(), predicted_future[1].item()), # Normalized px, py
                    "score": score
                })
                
                if score > best_score:
                    best_score = score
                    best_action = action
                    
        return best_action.numpy()
        
    def apply_action(self, action):
        if not self.alive:
            return
        self.last_action = [float(action[0]), float(action[1])]
        fx, fy = action
        # Scale to max force
        force = (fx * self.max_force, fy * self.max_force)
        self.body.apply_impulse_at_local_point(force)
