import pygame
class SelectBox:
    def __init__(self, x, y, width, height, options, font_size=20):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_option = 0 if options else -1
        self.is_open = False
        self.font = pygame.font.Font(None, font_size)
        self.option_height = height
        self.max_visible_options = 5
        self.scroll_offset = 0
        
        # Colors
        self.bg_color = (240, 240, 240)
        self.border_color = (100, 100, 100)
        self.selected_color = (70, 130, 180)
        self.hover_color = (200, 200, 200)
        self.text_color = (0, 0, 0)
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.rect.collidepoint(event.pos):
                    self.is_open = not self.is_open
                    return True
                elif self.is_open:
                    # Check if clicking on dropdown options
                    dropdown_rect = pygame.Rect(
                        self.rect.x, 
                        self.rect.y + self.rect.height,
                        self.rect.width, 
                        min(len(self.options), self.max_visible_options) * self.option_height
                    )
                    if dropdown_rect.collidepoint(event.pos):
                        rel_y = event.pos[1] - dropdown_rect.y
                        option_index = rel_y // self.option_height + self.scroll_offset
                        if 0 <= option_index < len(self.options):
                            self.selected_option = option_index
                        self.is_open = False
                        return True
                    else:
                        self.is_open = False
        
        elif event.type == pygame.MOUSEWHEEL and self.is_open:
            dropdown_rect = pygame.Rect(
                self.rect.x, 
                self.rect.y + self.rect.height,
                self.rect.width, 
                min(len(self.options), self.max_visible_options) * self.option_height
            )
            mouse_pos = pygame.mouse.get_pos()
            if dropdown_rect.collidepoint(mouse_pos):
                self.scroll_offset = max(0, min(
                    len(self.options) - self.max_visible_options,
                    self.scroll_offset - event.y
                ))
                return True
        
        return False
    
    def get_selected_value(self):
        if 0 <= self.selected_option < len(self.options):
            return self.options[self.selected_option]
        return None
    
    def draw(self, screen):
        # Draw main box
        pygame.draw.rect(screen, self.bg_color, self.rect)
        pygame.draw.rect(screen, self.border_color, self.rect, 2)
        
        # Draw selected text
        if 0 <= self.selected_option < len(self.options):
            text_surface = self.font.render(self.options[self.selected_option], True, self.text_color)
            text_rect = text_surface.get_rect(
                left=self.rect.x + 10,
                centery=self.rect.centery
            )
            screen.blit(text_surface, text_rect)
        
        # Draw dropdown arrow
        arrow_x = self.rect.right - 20
        arrow_y = self.rect.centery
        if self.is_open:
            # Up arrow
            pygame.draw.polygon(screen, self.text_color, [
                (arrow_x - 5, arrow_y + 3),
                (arrow_x + 5, arrow_y + 3),
                (arrow_x, arrow_y - 3)
            ])
        else:
            # Down arrow
            pygame.draw.polygon(screen, self.text_color, [
                (arrow_x - 5, arrow_y - 3),
                (arrow_x + 5, arrow_y - 3),
                (arrow_x, arrow_y + 3)
            ])
        
        # Draw dropdown options
        if self.is_open:
            visible_options = min(len(self.options), self.max_visible_options)
            dropdown_height = visible_options * self.option_height
            dropdown_rect = pygame.Rect(
                self.rect.x,
                self.rect.y + self.rect.height,
                self.rect.width,
                dropdown_height
            )
            
            pygame.draw.rect(screen, self.bg_color, dropdown_rect)
            pygame.draw.rect(screen, self.border_color, dropdown_rect, 2)
            
            mouse_pos = pygame.mouse.get_pos()
            
            for i in range(visible_options):
                option_index = i + self.scroll_offset
                if option_index >= len(self.options):
                    break
                    
                option_rect = pygame.Rect(
                    dropdown_rect.x,
                    dropdown_rect.y + i * self.option_height,
                    dropdown_rect.width,
                    self.option_height
                )
                
                # Highlight hovered option
                if option_rect.collidepoint(mouse_pos):
                    pygame.draw.rect(screen, self.hover_color, option_rect)
                # Highlight selected option
                elif option_index == self.selected_option:
                    pygame.draw.rect(screen, self.selected_color, option_rect)
                
                text_surface = self.font.render(self.options[option_index], True, self.text_color)
                text_rect = text_surface.get_rect(
                    left=option_rect.x + 10,
                    centery=option_rect.centery
                )
                screen.blit(text_surface, text_rect)
            
            # Draw scroll indicator if needed
            if len(self.options) > self.max_visible_options:
                scroll_bar_rect = pygame.Rect(
                    dropdown_rect.right - 10,
                    dropdown_rect.y,
                    8,
                    dropdown_rect.height
                )
                pygame.draw.rect(screen, (150, 150, 150), scroll_bar_rect)
                
                # Scroll thumb
                thumb_height = max(20, (self.max_visible_options / len(self.options)) * dropdown_rect.height)
                thumb_y = dropdown_rect.y + (self.scroll_offset / (len(self.options) - self.max_visible_options)) * (dropdown_rect.height - thumb_height)
                thumb_rect = pygame.Rect(
                    scroll_bar_rect.x + 1,
                    thumb_y,
                    6,
                    thumb_height
                )
                pygame.draw.rect(screen, (100, 100, 100), thumb_rect)