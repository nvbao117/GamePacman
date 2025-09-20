import pygame

class CheckBox:
    def __init__(self, x, y, size, text="", font_size=20, checked=False):
        self.rect = pygame.Rect(x, y, size, size)
        self.checked = checked
        self.text = text
        self.font = pygame.font.Font(None, font_size)
        
        # Calculate text rect
        if text:
            text_surface = self.font.render(text, True, (0, 0, 0))
            self.text_rect = pygame.Rect(
                x + size + 10,
                y + (size - text_surface.get_height()) // 2,
                text_surface.get_width(),
                text_surface.get_height()
            )
            self.full_rect = pygame.Rect(x, y, size + 10 + text_surface.get_width(), size)
        else:
            self.text_rect = None
            self.full_rect = self.rect
        
        # Colors
        self.bg_color = (255, 255, 255)
        self.border_color = (100, 100, 100)
        self.check_color = (70, 130, 180)
        self.text_color = (0, 0, 0)
        self.hover_color = (230, 230, 230)
        
        self.hovered = False
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.full_rect.collidepoint(event.pos):
                self.checked = not self.checked
                return True
        elif event.type == pygame.MOUSEMOTION:
            self.hovered = self.full_rect.collidepoint(event.pos)
        
        return False
    
    def is_checked(self):
        return self.checked
    
    def set_checked(self, checked):
        self.checked = checked
    
    def draw(self, screen):
        # Draw checkbox background
        color = self.hover_color if self.hovered else self.bg_color
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)
        
        # Draw checkmark if checked
        if self.checked:
            # Draw checkmark
            points = [
                (self.rect.x + 4, self.rect.centery),
                (self.rect.centerx - 2, self.rect.bottom - 6),
                (self.rect.right - 4, self.rect.y + 4)
            ]
            pygame.draw.lines(screen, self.check_color, False, points, 3)
        
        # Draw text
        if self.text and self.text_rect:
            text_surface = self.font.render(self.text, True, self.text_color)
            screen.blit(text_surface, self.text_rect)
