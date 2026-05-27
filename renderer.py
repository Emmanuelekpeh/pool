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
        
    def render(self, space, agents=None, player=None, aim_line=None):
        self.screen.fill((30, 100, 30)) # Green felt
        
        # Draw pockets
        for pos in POCKET_POSITIONS:
            pygame.draw.circle(self.screen, (10, 10, 10), pos, POCKET_RADIUS)
            
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
        
        pygame.display.flip()
        
    def tick(self, fps):
        self.clock.tick(fps)
