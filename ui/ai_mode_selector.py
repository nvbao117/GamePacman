# =============================================================================
# AI_MODE_SELECTOR.PY - SELECTOR CHO CÁC CHẾ ĐỘ AI
# =============================================================================
# Component UI để chọn giữa các chế độ AI: Traditional, Hybrid, Online, Offline

import pygame
from constants import *

class AIModeSelector:
    """
    AI Mode Selector - Dropdown để chọn chế độ AI
    
    Các chế độ:
    - TRADITIONAL: Sử dụng thuật toán cũ (BFS, DFS, A*, etc.)
    - HYBRID: Kết hợp offline + online (mặc định)
    - ONLINE: Chỉ sử dụng online decision-making
    - OFFLINE: Chỉ sử dụng offline planning
    """
    
    def __init__(self, x, y, width=200, height=40):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        
        # Font
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        
        # AI Modes
        self.modes = [
            {"id": "TRADITIONAL", "name": "Traditional AI", "desc": "BFS, DFS, A*, UCS, IDS, Greedy"},
            {"id": "HYBRID", "name": "Hybrid AI", "desc": "Offline + Online (Recommended)"},
            {"id": "ONLINE", "name": "Online AI", "desc": "Real-time decisions only"},
            {"id": "OFFLINE", "name": "Offline AI", "desc": "Pre-planned strategy only"}
        ]
        
        self.current_mode = 1  # Mặc định là HYBRID
        self.is_open = False
        self.hovered_item = -1
        
        # Colors
        self.bg_color = (40, 40, 40)
        self.hover_color = (60, 60, 60)
        self.selected_color = (0, 100, 200)
        self.border_color = WHITE
        self.text_color = WHITE
        
        # Animation
        self.animation_speed = 0.3
        self.dropdown_height = 0
        self.target_dropdown_height = 0
        
    def handle_events(self, event):
        """Xử lý events cho selector"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                # Kiểm tra click vào main button
                if self._is_point_in_main_button(mouse_x, mouse_y):
                    self.is_open = not self.is_open
                    self.target_dropdown_height = len(self.modes) * self.height if self.is_open else 0
                    return True
                
                # Kiểm tra click vào dropdown items
                elif self.is_open and self._is_point_in_dropdown(mouse_x, mouse_y):
                    clicked_index = self._get_clicked_item(mouse_x, mouse_y)
                    if clicked_index >= 0:
                        self.current_mode = clicked_index
                        self.is_open = False
                        self.target_dropdown_height = 0
                        return True
        
        elif event.type == pygame.MOUSEMOTION:
            if self.is_open:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                self.hovered_item = self._get_hovered_item(mouse_x, mouse_y)
        
        return False
    
    def update(self, dt):
        """Cập nhật animation"""
        # Smooth animation cho dropdown
        if self.dropdown_height < self.target_dropdown_height:
            self.dropdown_height += self.animation_speed * dt * 1000
            if self.dropdown_height > self.target_dropdown_height:
                self.dropdown_height = self.target_dropdown_height
        elif self.dropdown_height > self.target_dropdown_height:
            self.dropdown_height -= self.animation_speed * dt * 1000
            if self.dropdown_height < self.target_dropdown_height:
                self.dropdown_height = self.target_dropdown_height
    
    def draw(self, screen):
        """Vẽ selector lên màn hình"""
        # Vẽ main button
        self._draw_main_button(screen)
        
        # Vẽ dropdown nếu đang mở
        if self.is_open and self.dropdown_height > 0:
            self._draw_dropdown(screen)
    
    def _draw_main_button(self, screen):
        """Vẽ nút chính"""
        # Background
        pygame.draw.rect(screen, self.bg_color, 
                        (self.x, self.y, self.width, self.height))
        
        # Border
        pygame.draw.rect(screen, self.border_color, 
                        (self.x, self.y, self.width, self.height), 2)
        
        # Text
        current_mode = self.modes[self.current_mode]
        text_surface = self.font.render(current_mode["name"], True, self.text_color)
        text_rect = text_surface.get_rect(center=(self.x + self.width//2, self.y + self.height//2))
        screen.blit(text_surface, text_rect)
        
        # Dropdown arrow
        arrow_points = [
            (self.x + self.width - 20, self.y + self.height//2 - 5),
            (self.x + self.width - 15, self.y + self.height//2 + 5),
            (self.x + self.width - 10, self.y + self.height//2 - 5)
        ]
        pygame.draw.polygon(screen, self.text_color, arrow_points)
    
    def _draw_dropdown(self, screen):
        """Vẽ dropdown menu"""
        dropdown_y = self.y + self.height
        
        # Background
        pygame.draw.rect(screen, self.bg_color, 
                        (self.x, dropdown_y, self.width, self.dropdown_height))
        
        # Border
        pygame.draw.rect(screen, self.border_color, 
                        (self.x, dropdown_y, self.width, self.dropdown_height), 2)
        
        # Items
        for i, mode in enumerate(self.modes):
            if i * self.height >= self.dropdown_height:
                break
                
            item_y = dropdown_y + i * self.height
            
            # Highlight hovered item
            if i == self.hovered_item:
                pygame.draw.rect(screen, self.hover_color, 
                               (self.x + 2, item_y + 2, self.width - 4, self.height - 4))
            
            # Highlight selected item
            if i == self.current_mode:
                pygame.draw.rect(screen, self.selected_color, 
                               (self.x + 2, item_y + 2, self.width - 4, self.height - 4))
            
            # Mode name
            name_surface = self.font.render(mode["name"], True, self.text_color)
            screen.blit(name_surface, (self.x + 10, item_y + 5))
            
            # Mode description
            desc_surface = self.small_font.render(mode["desc"], True, (200, 200, 200))
            screen.blit(desc_surface, (self.x + 10, item_y + 25))
    
    def _is_point_in_main_button(self, x, y):
        """Kiểm tra click vào main button"""
        return (self.x <= x <= self.x + self.width and 
                self.y <= y <= self.y + self.height)
    
    def _is_point_in_dropdown(self, x, y):
        """Kiểm tra click vào dropdown"""
        dropdown_y = self.y + self.height
        return (self.x <= x <= self.x + self.width and 
                dropdown_y <= y <= dropdown_y + self.dropdown_height)
    
    def _get_clicked_item(self, x, y):
        """Lấy index của item được click"""
        if not self._is_point_in_dropdown(x, y):
            return -1
        
        dropdown_y = self.y + self.height
        relative_y = y - dropdown_y
        item_index = relative_y // self.height
        
        if 0 <= item_index < len(self.modes):
            return int(item_index)
        return -1
    
    def _get_hovered_item(self, x, y):
        """Lấy index của item đang hover"""
        if not self._is_point_in_dropdown(x, y):
            return -1
        
        dropdown_y = self.y + self.height
        relative_y = y - dropdown_y
        item_index = relative_y // self.height
        
        if 0 <= item_index < len(self.modes):
            return int(item_index)
        return -1
    
    def get_current_mode(self):
        """Lấy mode hiện tại"""
        return self.modes[self.current_mode]["id"]
    
    def get_current_mode_name(self):
        """Lấy tên mode hiện tại"""
        return self.modes[self.current_mode]["name"]
    
    def set_mode(self, mode_id):
        """Đặt mode theo ID"""
        for i, mode in enumerate(self.modes):
            if mode["id"] == mode_id:
                self.current_mode = i
                break
    
    def is_open(self):
        """Kiểm tra dropdown có đang mở không"""
        return self.is_open
