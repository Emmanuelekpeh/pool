import pygame
import pymunk.pygame_util
from world import WIDTH, HEIGHT, POCKET_POSITIONS, POCKET_RADIUS

class Renderer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Evolutionary Billiards")
        self.clock = pygame.time.Clock()
        self.draw_options = pymunk.pygame_util.DrawOptions(self.screen)
        self.font = pygame.font.SysFont(None, 24)
        self.small_font = pygame.font.SysFont(None, 16)
        
    def render(self, space, agents=None, player=None, aim_line=None, show_thoughts=False):
        self.screen.fill((30, 100, 30)) # Green felt
        
        # Draw pockets
        for pos in POCKET_POSITIONS:
            pygame.draw.circle(self.screen, (10, 10, 10), pos, POCKET_RADIUS)
            
        # Draw thought processes (Internal Simulation Reveal)
        if show_thoughts and agents:
            for agent in agents:
                if agent.alive and hasattr(agent, 'thought_process'):
                    start_pos = (int(agent.body.position.x), int(agent.body.position.y))
                    
                    # Find best score to highlight the chosen shot
                    best_score = max([t["score"] for t in agent.thought_process]) if agent.thought_process else 0
                    
                    for thought in agent.thought_process:
                        is_best = (thought["score"] == best_score)
                        
                        # Draw candidate action line
                        ax, ay = thought["action"]
                        end_pos = (int(start_pos[0] + ax * 30), int(start_pos[1] + ay * 30))
                        line_color = (255, 255, 255, 150) if is_best else (150, 150, 150, 50)
                        pygame.draw.line(self.screen, line_color, start_pos, end_pos, 2 if is_best else 1)
                        
                        # Draw predicted future position (Ghost Ball)
                        fx, fy = thought["future_pos"]
                        ghost_pos = (int(fx * WIDTH), int(fy * HEIGHT))
                        
                        # Create a transparent surface for the ghost ball
                        ghost_surface = pygame.Surface((30, 30), pygame.SRCALPHA)
                        ghost_color = list(agent.color)
                        ghost_color[3] = 150 if is_best else 50 # Alpha
                        pygame.draw.circle(ghost_surface, ghost_color, (15, 15), 15)
                        self.screen.blit(ghost_surface, (ghost_pos[0]-15, ghost_pos[1]-15))
                        
                        # Draw Director Score
                        if is_best:
                            score_text = self.small_font.render(f"{thought['score']:.2f}", True, (255, 255, 255))
                            self.screen.blit(score_text, (ghost_pos[0] + 15, ghost_pos[1] - 15))
                            
        # Draw pymunk objects
        space.debug_draw(self.draw_options)
        
        # Draw agent numbers
        if agents:
            for agent in agents:
                if agent.alive:
                    pos = int(agent.body.position.x), int(agent.body.position.y)
                    text_color = (255, 255, 255) if agent.color == (0, 0, 0, 255) else (0, 0, 0)
                    text = self.font.render(str(agent.id), True, text_color)
                    text_rect = text.get_rect(center=pos)
                    self.screen.blit(text, text_rect)
                    
        # Draw player indicator
        if player and player.alive:
            pos = int(player.body.position.x), int(player.body.position.y)
            text = self.font.render("P", True, (0, 0, 0))
            text_rect = text.get_rect(center=pos)
            self.screen.blit(text, text_rect)
            
        # Draw aim line
        if aim_line and player and player.alive:
            start_pos, end_pos = aim_line
            pygame.draw.line(self.screen, (255, 255, 255), start_pos, end_pos, 3)
            
        # Draw UI overlay
        ui_text = self.font.render(f"Thoughts (T): {'ON' if show_thoughts else 'OFF'} | Player (P)", True, (255, 255, 255))
        self.screen.blit(ui_text, (10, 10))
        
        pygame.display.flip()
        
    def tick(self, fps):
        self.clock.tick(fps)
