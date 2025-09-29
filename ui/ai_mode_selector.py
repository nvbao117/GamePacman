# =============================================================================
# AI_MODE_SELECTOR.PY - SELECTOR CHO CÁC CHẾ ĐỘ AI (ĐẸP HƠN)
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

    def __init__(self, x, y, width=220, height=44):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

        # Font
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 20)
        self.icon_font = pygame.font.Font(None, 32)

        # AI Modes
        self.modes = [
            {"id": "ONLINE", "name": "Online AI", "desc": "Real-time decisions only", "icon": ""},
            {"id": "OFFLINE", "name": "Offline AI", "desc": "Pre-planned strategy only", "icon": ""}
        ]

        self.current_mode = 1  # Mặc định là HYBRID
        self.is_open = False
        self.hovered_item = -1

        # Colors (gradient & shadow)
        self.bg_color_top = (50, 60, 90)
        self.bg_color_bottom = (30, 35, 50)
        self.hover_color = (70, 110, 180)
        self.selected_color = (0, 140, 255)
        self.border_color = (180, 200, 255)
        self.text_color = (255, 255, 255)
        self.desc_color = (200, 220, 255)
        self.shadow_color = (0, 0, 0, 80)
        self.arrow_color = (180, 200, 255)

        # Animation
        self.animation_speed = 2
        self.dropdown_height = 0
        self.target_dropdown_height = 0

        # For smooth shadow
        self.shadow_offset = 6

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
            else:
                self.hovered_item = -1

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
        # Vẽ shadow cho main button
        self._draw_shadow(screen, self.x, self.y, self.width, self.height, self.shadow_offset)
        # Vẽ main button
        self._draw_main_button(screen)

        # Vẽ dropdown nếu đang mở
        if self.is_open or self.dropdown_height > 0:
            self._draw_shadow(screen, self.x, self.y + self.height, self.width, self.dropdown_height, self.shadow_offset)
            self._draw_dropdown(screen)

    def _draw_main_button(self, screen):
        """Vẽ nút chính với gradient, bo góc, icon, arrow"""
        rect = pygame.Rect(self.x, self.y, self.width, self.height)
        self._draw_rounded_gradient_rect(screen, rect, self.bg_color_top, self.bg_color_bottom, radius=14)

        # Border
        pygame.draw.rect(screen, self.border_color, rect, 2, border_radius=14)

        # Icon
        current_mode = self.modes[self.current_mode]
        icon_surface = self.icon_font.render(current_mode.get("icon", ""), True, self.selected_color)
        screen.blit(icon_surface, (self.x + 12, self.y + self.height // 2 - icon_surface.get_height() // 2))

        # Text
        text_surface = self.font.render(current_mode["name"], True, self.text_color)
        text_rect = text_surface.get_rect(midleft=(self.x + 48, self.y + self.height // 2))
        screen.blit(text_surface, text_rect)

        # Dropdown arrow (animated)
        arrow_center = (self.x + self.width - 28, self.y + self.height // 2)
        arrow_size = 10
        if self.is_open or self.dropdown_height > 0:
            # Arrow down
            arrow_points = [
                (arrow_center[0] - arrow_size, arrow_center[1] - 4),
                (arrow_center[0] + arrow_size, arrow_center[1] - 4),
                (arrow_center[0], arrow_center[1] + 8)
            ]
        else:
            # Arrow right
            arrow_points = [
                (arrow_center[0] - 4, arrow_center[1] - arrow_size),
                (arrow_center[0] - 4, arrow_center[1] + arrow_size),
                (arrow_center[0] + 8, arrow_center[1])
            ]
        pygame.draw.polygon(screen, self.arrow_color, arrow_points)

    def _draw_dropdown(self, screen):
        """Vẽ dropdown menu với hiệu ứng đẹp"""
        dropdown_y = self.y + self.height
        rect = pygame.Rect(self.x, dropdown_y, self.width, self.dropdown_height)
        self._draw_rounded_gradient_rect(screen, rect, self.bg_color_top, self.bg_color_bottom, radius=14)

        # Border
        pygame.draw.rect(screen, self.border_color, rect, 2, border_radius=14)

        # Items
        for i, mode in enumerate(self.modes):
            item_top = i * self.height
            if item_top >= self.dropdown_height:
                break

            item_y = dropdown_y + item_top
            item_rect = pygame.Rect(self.x + 2, item_y + 2, self.width - 4, self.height - 4)

            # Highlight hovered item
            if i == self.hovered_item:
                pygame.draw.rect(screen, self.hover_color, item_rect, border_radius=10)
            # Highlight selected item
            if i == self.current_mode:
                pygame.draw.rect(screen, self.selected_color, item_rect, border_radius=10)

            # Icon
            icon_surface = self.icon_font.render(mode.get("icon", ""), True, self.selected_color if i == self.current_mode else self.arrow_color)
            screen.blit(icon_surface, (self.x + 12, item_y + self.height // 2 - icon_surface.get_height() // 2))

            # Mode name
            name_surface = self.font.render(mode["name"], True, self.text_color)
            screen.blit(name_surface, (self.x + 48, item_y + 7))

            # Mode description
            desc_surface = self.small_font.render(mode["desc"], True, self.desc_color)
            screen.blit(desc_surface, (self.x + 48, item_y + 27))

    def _draw_rounded_gradient_rect(self, surface, rect, color_top, color_bottom, radius=12):
        """Vẽ một rounded-rect với gradient dọc"""
        gradient = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        for y in range(rect.height):
            ratio = y / max(1, rect.height - 1)
            r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
            g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
            b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
            pygame.draw.line(gradient, (r, g, b), (0, y), (rect.width, y))
        rounded = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(rounded, (255, 255, 255), (0, 0, rect.width, rect.height), border_radius=radius)
        gradient.blit(rounded, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(gradient, (rect.x, rect.y))

    def _draw_shadow(self, surface, x, y, w, h, offset):
        """Vẽ shadow mờ phía sau"""
        shadow_rect = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(shadow_rect, self.shadow_color, (0, 0, w, h), border_radius=16)
        surface.blit(shadow_rect, (x + offset, y + offset))

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

    def is_opened(self):
        """Kiểm tra dropdown có đang mở không"""
        return self.is_open
