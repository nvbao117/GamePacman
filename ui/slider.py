import pygame
from ui.uicomponent import UIComponent
from ui.utils import * 
class Slider():
    def __init__(self, x, y, width, height, min_value=0, max_value=100, initial_value=50):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.dragging = False
        
        # Track and handle dimensions
        self.track_height = height // 4
        self.handle_size = height
        
        # Colors
        self.track_color = (200, 200, 200)
        self.track_fill_color = (70, 130, 180)
        self.handle_color = (255, 255, 255)
        self.handle_border_color = (100, 100, 100)
        self.handle_hover_color = (240, 240, 240)
        
        self.hovered = False
    
    def handle_event(self, event):
        handle_x = self.rect.x + (self.value - self.min_value) / (self.max_value - self.min_value) * (self.rect.width - self.handle_size)
        handle_rect = pygame.Rect(
            handle_x,
            self.rect.y,
            self.handle_size,
            self.rect.height
        )
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if handle_rect.collidepoint(event.pos):
                    self.dragging = True
                    return True
                elif self.rect.collidepoint(event.pos):
                    # Click on track to jump to position
                    relative_x = event.pos[0] - self.rect.x - self.handle_size // 2
                    relative_x = max(0, min(self.rect.width - self.handle_size, relative_x))
                    self.value = self.min_value + (relative_x / (self.rect.width - self.handle_size)) * (self.max_value - self.min_value)
                    self.dragging = True
                    return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging:
                self.dragging = False
                return True
        
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                relative_x = event.pos[0] - self.rect.x - self.handle_size // 2
                relative_x = max(0, min(self.rect.width - self.handle_size, relative_x))
                self.value = self.min_value + (relative_x / (self.rect.width - self.handle_size)) * (self.max_value - self.min_value)
                return True
            else:
                self.hovered = handle_rect.collidepoint(event.pos)
        
        return False
    
    def get_value(self):
        return self.value
    
    def set_value(self, value):
        self.value = max(self.min_value, min(self.max_value, value))
    
    def draw(self, screen):
        # Draw track background
        track_rect = pygame.Rect(
            self.rect.x,
            self.rect.centery - self.track_height // 2,
            self.rect.width,
            self.track_height
        )
        pygame.draw.rect(screen, self.track_color, track_rect, border_radius=self.track_height // 2)
        
        # Draw track fill (progress)
        handle_x = self.rect.x + (self.value - self.min_value) / (self.max_value - self.min_value) * (self.rect.width - self.handle_size)
        fill_width = handle_x - self.rect.x + self.handle_size // 2
        if fill_width > 0:
            fill_rect = pygame.Rect(
                self.rect.x,
                self.rect.centery - self.track_height // 2,
                fill_width,
                self.track_height
            )
            pygame.draw.rect(screen, self.track_fill_color, fill_rect, border_radius=self.track_height // 2)
        
        # Draw handle
        handle_rect = pygame.Rect(
            handle_x,
            self.rect.y,
            self.handle_size,
            self.rect.height
        )
        
        handle_color = self.handle_hover_color if self.hovered or self.dragging else self.handle_color
        pygame.draw.ellipse(screen, handle_color, handle_rect)
        pygame.draw.ellipse(screen, self.handle_border_color, handle_rect, 2)
    