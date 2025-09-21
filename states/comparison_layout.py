# =============================================================================
# COMPARISON_LAYOUT.PY - LAYOUT UI CHO SO SÁNH AI VÀ NGƯỜI CHƠI
# =============================================================================
# File này chứa ComparisonLayout - quản lý giao diện UI cho comparison mode
# Bao gồm 2 game areas song song và control panel ở dưới

import pygame
import math
from ui.uicomponent import UIComponent
from ui.constants import *
from ui.selectbox import SelectBox


class ComparisonLayout(UIComponent):
    """
    ComparisonLayout - Quản lý layout UI cho comparison mode
    - Chia màn hình thành 2 game areas song song và control panel ở dưới
    - Quản lý thông tin game cho cả AI và Player
    - Có hiệu ứng visual và animation đẹp mắt
    - Hỗ trợ selectbox để chọn thuật toán AI
    """
    def __init__(self, app):
        """
        Khởi tạo ComparisonLayout
        Args:
            app: Tham chiếu đến App chính
        """
        super().__init__(app)
        # Các rectangle chính
        self.ai_game_area_rect = None      # Khu vực game AI (bên trái)
        self.player_game_area_rect = None  # Khu vực game Player (bên phải)
        self.control_panel_rect = None     # Panel điều khiển (ở dưới)
        self.background_rect = None        # Background chính
        
        # Setup layout dimensions
        self._setup_layout()
        
        # Thông tin game cho AI
        self.ai_score = 0
        self.ai_lives = 5
        self.ai_level = 1
        
        # Thông tin game cho Player
        self.player_score = 0
        self.player_lives = 5
        self.player_level = 1
        
        # Thông tin chung
        self.algorithm = "BFS"  # Thuật toán AI
        self.is_playing = False # Trạng thái play/pause
        
        # Tùy chọn thuật toán cho selectbox
        self.algorithm_options = ["BFS", "DFS", "A*", "UCS", "IDS"]
        
        # Khởi tạo selectbox
        self.algorithm_selectbox = None
        self._setup_selectbox()
        
        # Animation
        self.animation_time = 0
        
    def _setup_layout(self):
        """
        Setup kích thước layout cho comparison mode
        - Chia màn hình thành 2 game areas song song và control panel ở dưới
        - Giữ aspect ratio của game gốc
        - Tối ưu hóa không gian cho cả 2 game
        """
        # Background chính chiếm toàn bộ màn hình
        self.background_rect = pygame.Rect(0, 0, self.app.WIDTH, self.app.HEIGHT)
        
        # Control panel - ở dưới cùng
        panel_height = 180  # Giảm chiều cao control panel
        panel_width = self.app.WIDTH
        panel_x = 0
        panel_y = self.app.HEIGHT - panel_height
        
        self.control_panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        # Tính toán kích thước cho 2 game areas - chia đều
        # Để chỗ cho title và margins
        available_width = self.app.WIDTH - 40  # 20px margin mỗi bên
        available_height = self.app.HEIGHT - panel_height - 100  # Thêm chỗ cho title và control panel
        
        # Chia đều chiều rộng cho 2 game areas
        game_area_width = (available_width - 30) // 2  # 30px khoảng cách giữa 2 game
        game_area_height = available_height
        
        # Tính scale để giữ aspect ratio cho game
        from constants import SCREENSIZE
        original_width, original_height = SCREENSIZE
        
        scale_x = game_area_width / original_width
        scale_y = game_area_height / original_height
        scale = min(scale_x, scale_y)  # Dùng scale nhỏ hơn để giữ aspect ratio
        
        # Tính kích thước game area cuối cùng
        final_game_width = int(original_width * scale)
        final_game_height = int(original_height * scale)
        
        # AI Game area - bên trái (căn giữa trong nửa trái)
        ai_area_x = 20  # Margin trái
        ai_game_x = ai_area_x + (game_area_width - final_game_width) // 2  # Căn giữa
        ai_game_y = 80  # Thêm chỗ cho title
        self.ai_game_area_rect = pygame.Rect(ai_game_x, ai_game_y, final_game_width, final_game_height)
        
        # Player Game area - bên phải (căn giữa trong nửa phải)
        player_area_x = ai_area_x + game_area_width + 30  # Khoảng cách 30px
        player_game_x = player_area_x + (game_area_width - final_game_width) // 2  # Căn giữa
        player_game_y = 80  # Cùng chiều cao với AI game
        self.player_game_area_rect = pygame.Rect(player_game_x, player_game_y, final_game_width, final_game_height)
    
    def _setup_selectbox(self):
        """Setup the algorithm selectbox"""
        # Position selectbox in the algorithm section
        selectbox_x = self.control_panel_rect.x + 20
        selectbox_y = self.control_panel_rect.y + 60  # Below the algorithm label
        selectbox_width = 200
        selectbox_height = 40
        
        self.algorithm_selectbox = SelectBox(
            selectbox_x, selectbox_y, selectbox_width, selectbox_height,
            self.algorithm_options, font_size=12
        )
        
        # Use game font
        try:
            self.algorithm_selectbox.font = pygame.font.Font(FONT_PATH, 12)
        except:
            self.algorithm_selectbox.font = pygame.font.Font(None, 12)
        
        # Customize colors to match Pac-Man theme
        self.algorithm_selectbox.bg_color = (70, 70, 100)
        self.algorithm_selectbox.border_color = PAC_YELLOW
        self.algorithm_selectbox.selected_color = (120, 200, 240)
        self.algorithm_selectbox.hover_color = (90, 90, 120)
        self.algorithm_selectbox.text_color = DOT_WHITE
        
        # Set initial selection based on current algorithm
        if self.algorithm in self.algorithm_options:
            self.algorithm_selectbox.selected_option = self.algorithm_options.index(self.algorithm)
    
    def set_game_info(self, ai_score=0, ai_lives=3, ai_level=1, 
                     player_score=0, player_lives=3, player_level=1, algorithm="BFS"):
        """
        Cập nhật thông tin game cho cả AI và Player
        Args:
            ai_score: Điểm số AI hiện tại
            ai_lives: Số mạng AI còn lại
            ai_level: Level AI hiện tại
            player_score: Điểm số Player hiện tại
            player_lives: Số mạng Player còn lại
            player_level: Level Player hiện tại
            algorithm: Thuật toán AI đang sử dụng
        """
        self.ai_score = ai_score
        self.ai_lives = ai_lives
        self.ai_level = ai_level
        self.player_score = player_score
        self.player_lives = player_lives
        self.player_level = player_level
        self.algorithm = algorithm
    
    def render(self):
        """
        Render toàn bộ comparison layout
        - Vẽ background với hiệu ứng
        - Vẽ 2 game area frames
        - Vẽ control panel
        - Vẽ thông tin game cho cả AI và Player
        """
        # Vẽ background chính
        self._draw_background()
        
        # Vẽ frame cho 2 game areas
        self._draw_game_areas()
        
        # Vẽ control panel
        self._draw_control_panel()
    
    def _draw_background(self):
        """Draw the main background with enhanced transparency effects"""
        # Create a more subtle gradient background
        for y in range(self.app.HEIGHT):
            intensity = int(8 + (y / self.app.HEIGHT) * 15)
            color = (intensity, intensity, intensity + 20)
            pygame.draw.line(self.surface, color, (0, y), (self.app.WIDTH, y))
        
        # Add animated starfield with more transparency
        self.animation_time += 0.02
        for i in range(150):
            x = (i * 37 + self.animation_time * 10) % self.app.WIDTH
            y = (i * 23 + self.animation_time * 5) % self.app.HEIGHT
            alpha = int(30 + 20 * math.sin(self.animation_time * 2 + i * 0.1))
            color = (alpha, alpha, alpha + 30)
            size = 1 + int(1 * math.sin(self.animation_time * 3 + i * 0.2))
            pygame.draw.circle(self.surface, color, (int(x), int(y)), size)
        
        # Add floating particles with transparency
        for i in range(30):
            x = (self.animation_time * 15 + i * 80) % self.app.WIDTH
            y = 100 + 200 * math.sin(self.animation_time * 1.5 + i * 0.3)
            alpha = int(40 + 30 * math.sin(self.animation_time * 2 + i))
            color = (alpha, alpha // 2, alpha + 20)
            pygame.draw.circle(self.surface, color, (int(x), int(y)), 2)
    
    def _draw_game_areas(self):
        """Draw both game areas with enhanced transparency and full-screen effect"""
        # Draw AI Game Area (Left)
        self._draw_single_game_area(self.ai_game_area_rect, "AI PLAYER", GHOST_BLUE)
        
        # Draw Player Game Area (Right)
        self._draw_single_game_area(self.player_game_area_rect, "HUMAN PLAYER", GHOST_PINK)
    
    def _draw_single_game_area(self, game_rect, title_text, border_color):
        """Draw a single game area with title and effects"""
        # Create a semi-transparent overlay for the game area
        overlay_surface = pygame.Surface((game_rect.width, game_rect.height), pygame.SRCALPHA)
        
        # Semi-transparent background with gradient
        for y in range(game_rect.height):
            alpha = int(20 + (y / game_rect.height) * 10)
            color = (alpha, alpha, alpha + 15, alpha)
            pygame.draw.line(overlay_surface, color, (0, y), (game_rect.width, y))
        
        # Add subtle animated particles inside game area
        for i in range(20):
            x = (self.animation_time * 8 + i * 50) % game_rect.width
            y = (self.animation_time * 5 + i * 30) % game_rect.height
            alpha = int(15 + 10 * math.sin(self.animation_time * 2 + i * 0.3))
            color = (alpha, alpha, alpha + 20, alpha)
            size = 1 + int(1 * math.sin(self.animation_time * 3 + i * 0.2))
            pygame.draw.circle(overlay_surface, color, (int(x), int(y)), size)
        
        # Blit the overlay to create transparency effect
        self.surface.blit(overlay_surface, game_rect.topleft)
        
        # Enhanced outer glow effect
        for i in range(6, 0, -1):
            alpha = int(40 - i * 6)
            color = (alpha, alpha + 40, alpha + 80)
            glow_rect = game_rect.inflate(i * 3, i * 3)
            pygame.draw.rect(self.surface, color, glow_rect, 2)
        
        # Main outer frame with animated glow
        glow_intensity = int(100 + 50 * math.sin(self.animation_time * 2))
        pygame.draw.rect(self.surface, (glow_intensity, glow_intensity + 50, glow_intensity + 100), game_rect, 4)
        pygame.draw.rect(self.surface, border_color, game_rect, 2)
        pygame.draw.rect(self.surface, (0, 150, 255), game_rect, 1)
        
        # Inner frame with enhanced animation
        inner_rect = game_rect.inflate(-12, -12)
        pulse = int(3 + 2 * math.sin(self.animation_time * 4))
        pulse_r = max(0, min(255, int(255 + 30 * math.sin(self.animation_time * 3))))
        pulse_g = max(0, min(255, int(255 + 30 * math.sin(self.animation_time * 3))))
        pulse_b = max(0, min(255, int(100 + 30 * math.sin(self.animation_time * 3))))
        pulse_color = (pulse_r, pulse_g, pulse_b)
        pygame.draw.rect(self.surface, pulse_color, inner_rect, pulse)
        pygame.draw.rect(self.surface, (255, 255, 150), inner_rect, 1)
        
        # Title positioned above game area, centered
        try:
            font_title = pygame.font.Font(FONT_PATH, 24)
            font_subtitle = pygame.font.Font(FONT_PATH, 14)
        except:
            font_title = pygame.font.Font(None, 24)
            font_subtitle = pygame.font.Font(None, 14)
        
        # Main title
        title_surface = font_title.render(title_text, True, border_color)
        title_rect = title_surface.get_rect(center=(game_rect.centerx, game_rect.y - 30))
        
        # Glow effect for title
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            glow_text = font_title.render(title_text, True, (100, 100, 0))
            self.surface.blit(glow_text, (title_rect.x + offset[0], title_rect.y + offset[1]))
        
        # Main title with subtle pulsing
        pulse_alpha = int(255 + 20 * math.sin(self.animation_time * 3))
        pulse_alpha = max(200, min(255, pulse_alpha))
        title_color = (pulse_alpha, pulse_alpha, 0) if border_color == GHOST_BLUE else (pulse_alpha, 0, pulse_alpha)
        title_surface = font_title.render(title_text, True, title_color)
        self.surface.blit(title_surface, title_rect)
        
        # Thêm selectbox cho AI player (bên phải màn hình)
        if border_color == GHOST_BLUE:  # Chỉ cho AI player
            # Selectbox ở bên phải màn hình AI - đẹp và thân thiện hơn
            selectbox_x = game_rect.right + 20  # Bên phải game area
            selectbox_y = game_rect.y + 30      # Cùng chiều cao với title
            
            # Vẽ background đẹp cho selectbox với gradient
            selectbox_bg_rect = pygame.Rect(selectbox_x, selectbox_y, 220, 80)
            
            # Gradient background
            for i in range(selectbox_bg_rect.height):
                alpha = int(40 + (i / selectbox_bg_rect.height) * 20)
                color = (alpha, alpha, alpha + 30)
                pygame.draw.line(self.surface, color, 
                               (selectbox_bg_rect.x, selectbox_bg_rect.y + i),
                               (selectbox_bg_rect.right, selectbox_bg_rect.y + i))
            
            # Border với hiệu ứng glow
            pygame.draw.rect(self.surface, GHOST_BLUE, selectbox_bg_rect, 3)
            pygame.draw.rect(self.surface, (0, 200, 255), selectbox_bg_rect, 1)
            
            # Algorithm label
            algo_label = font_subtitle.render("AI Algorithm", True, GHOST_BLUE)
            self.surface.blit(algo_label, (selectbox_x + 10, selectbox_y + 5))
            
            # Draw selectbox với styling đẹp hơn
            if self.algorithm_selectbox:
                # Reposition selectbox
                self.algorithm_selectbox.rect.x = selectbox_x + 15
                self.algorithm_selectbox.rect.y = selectbox_y + 30
                self.algorithm_selectbox.rect.width = 190
                self.algorithm_selectbox.rect.height = 35
                
                # Customize selectbox colors để đẹp hơn
                self.algorithm_selectbox.bg_color = (80, 80, 120)
                self.algorithm_selectbox.border_color = PAC_YELLOW
                self.algorithm_selectbox.selected_color = (120, 200, 240)
                self.algorithm_selectbox.hover_color = (100, 100, 140)
                self.algorithm_selectbox.text_color = DOT_WHITE
                
                self.algorithm_selectbox.draw(self.surface)
    
    def _draw_control_panel(self):
        """Draw the control panel with enhanced transparency effects"""
        # Create semi-transparent panel background
        panel_surface = pygame.Surface((self.control_panel_rect.width, self.control_panel_rect.height), pygame.SRCALPHA)
        
        # Enhanced gradient with transparency
        for i in range(self.control_panel_rect.height):
            alpha = int(30 + (i / self.control_panel_rect.height) * 20)
            color = (alpha, alpha, alpha + 25, alpha)
            pygame.draw.line(panel_surface, color, 
                           (0, i), (self.control_panel_rect.width, i))
        
        # Add subtle animated particles
        for i in range(15):
            x = (self.animation_time * 5 + i * 30) % self.control_panel_rect.width
            y = (self.animation_time * 3 + i * 40) % self.control_panel_rect.height
            alpha = int(20 + 15 * math.sin(self.animation_time * 2 + i * 0.5))
            color = (alpha, alpha, alpha + 30, alpha)
            size = 1 + int(1 * math.sin(self.animation_time * 3 + i * 0.3))
            pygame.draw.circle(panel_surface, color, (int(x), int(y)), size)
        
        # Blit the panel surface
        self.surface.blit(panel_surface, self.control_panel_rect.topleft)
        
        # Enhanced animated border glow
        glow_intensity = max(0, min(255, int(60 + 40 * math.sin(self.animation_time * 3))))
        for i in range(3, 0, -1):
            alpha = max(0, min(255, int(glow_intensity - i * 15)))
            color = (alpha, max(0, min(255, alpha + 30)), max(0, min(255, alpha + 60)))
            glow_rect = self.control_panel_rect.inflate(i * 2, i * 2)
            pygame.draw.rect(self.surface, color, glow_rect, 2)
        
        pygame.draw.rect(self.surface, GHOST_BLUE, self.control_panel_rect, 3)
        pygame.draw.rect(self.surface, (0, 150, 255), self.control_panel_rect, 1)
        
        # Panel title with enhanced neon effect
        try:
            font = pygame.font.Font(FONT_PATH, 20)
        except:
            font = pygame.font.Font(None, 20)
        
        title_text = font.render("COMPARISON CONTROL PANEL", True, PAC_YELLOW)
        title_rect = title_text.get_rect(center=(self.control_panel_rect.centerx, self.control_panel_rect.y + 20))
        
        # Multiple glow layers
        glow_colors = [(80, 80, 0), (120, 120, 0), (160, 160, 0)]
        for i, glow_color in enumerate(glow_colors):
            for offset in [(i+1, i+1), (-i-1, -i-1), (i+1, -i-1), (-i-1, i+1)]:
                glow_text = font.render("COMPARISON CONTROL PANEL", True, glow_color)
                self.surface.blit(glow_text, (title_rect.x + offset[0], title_rect.y + offset[1]))
        
        # Pulsing title
        pulse_alpha = int(255 + 30 * math.sin(self.animation_time * 4))
        pulse_alpha = max(0, min(255, pulse_alpha))
        title_color = (pulse_alpha, pulse_alpha, 0)
        title_text = font.render("COMPARISON CONTROL PANEL", True, title_color)
        self.surface.blit(title_text, title_rect)
        
        # Draw panel sections
        self._draw_comparison_stats()
        self._draw_controls_section()
        self._draw_play_section()
    
    def _draw_comparison_stats(self):
        """Draw comparison statistics between AI and Player"""
        y_start = self.control_panel_rect.y + 50
        try:
            font_large = pygame.font.Font(FONT_PATH, 16)
            font_medium = pygame.font.Font(FONT_PATH, 14)
            font_small = pygame.font.Font(FONT_PATH, 12)
        except:
            font_large = pygame.font.Font(None, 16)
            font_medium = pygame.font.Font(None, 14)
            font_small = pygame.font.Font(None, 12)
        
        # AI Stats Section (Left side) - Chỉ có Score, Lives, Level
        ai_section_rect = pygame.Rect(self.control_panel_rect.x + 20, y_start, 
                                     (self.control_panel_rect.width - 60) // 2, 100)
        
        # AI section background
        pygame.draw.rect(self.surface, (50, 50, 80), ai_section_rect)
        pygame.draw.rect(self.surface, GHOST_BLUE, ai_section_rect, 2)
        pygame.draw.rect(self.surface, (0, 150, 255), ai_section_rect, 1)
        
        # AI title
        ai_title = font_large.render("AI PLAYER", True, GHOST_BLUE)
        self.surface.blit(ai_title, (ai_section_rect.x + 10, ai_section_rect.y + 5))
        
        # AI stats - sắp xếp theo chiều ngang với spacing rộng hơn
        ai_stats_y = ai_section_rect.y + 30
        ai_stats_spacing = 150  # Tăng khoảng cách lên 150px để rộng hơn
        
        # Score
        ai_score_text = font_medium.render(f"Score: {self.ai_score:,}", True, DOT_WHITE)
        self.surface.blit(ai_score_text, (ai_section_rect.x + 10, ai_stats_y))
        
        # Lives
        ai_lives_text = font_medium.render(f"Lives: {self.ai_lives}", True, DOT_WHITE)
        self.surface.blit(ai_lives_text, (ai_section_rect.x + 10 + ai_stats_spacing, ai_stats_y))
        
        # Level
        ai_level_text = font_medium.render(f"Level: {self.ai_level + 1}", True, DOT_WHITE)
        self.surface.blit(ai_level_text, (ai_section_rect.x + 10 + ai_stats_spacing * 2, ai_stats_y))
        
        
        # Player Stats Section (Right side) - Chỉ có Score, Lives, Level
        player_section_rect = pygame.Rect(ai_section_rect.right + 20, y_start, 
                                         (self.control_panel_rect.width - 60) // 2, 100)
        
        # Player section background
        pygame.draw.rect(self.surface, (50, 50, 80), player_section_rect)
        pygame.draw.rect(self.surface, GHOST_PINK, player_section_rect, 2)
        pygame.draw.rect(self.surface, (0, 150, 255), player_section_rect, 1)
        
        # Player title
        player_title = font_large.render("HUMAN PLAYER", True, GHOST_PINK)
        self.surface.blit(player_title, (player_section_rect.x + 10, player_section_rect.y + 5))
        
        # Player stats - sắp xếp theo chiều ngang (chỉ 3 stats)
        player_stats_y = player_section_rect.y + 30
        player_stats_spacing = 150  # Tăng khoảng cách lên 150px để rộng hơn
        
        # Score
        player_score_text = font_medium.render(f"Score: {self.player_score:,}", True, DOT_WHITE)
        self.surface.blit(player_score_text, (player_section_rect.x + 10, player_stats_y))
        
        # Lives
        player_lives_text = font_medium.render(f"Lives: {self.player_lives}", True, DOT_WHITE)
        self.surface.blit(player_lives_text, (player_section_rect.x + 10 + player_stats_spacing, player_stats_y))
        
        # Level
        player_level_text = font_medium.render(f"Level: {self.player_level + 1}", True, DOT_WHITE)
        self.surface.blit(player_level_text, (player_section_rect.x + 10 + player_stats_spacing * 2, player_stats_y))
    
    def _draw_controls_section(self):
        """Draw controls section"""
        y_start = self.control_panel_rect.y + 160
        try:
            font = pygame.font.Font(FONT_PATH, 12)
        except:
            font = pygame.font.Font(None, 12)
        
        # Controls section background
        controls_rect = pygame.Rect(self.control_panel_rect.x + 20, y_start, 
                                   self.control_panel_rect.width - 40, 20)
        pygame.draw.rect(self.surface, (40, 40, 60), controls_rect)
        pygame.draw.rect(self.surface, GHOST_BLUE, controls_rect, 1)
        
        # Controls text - sắp xếp theo chiều ngang
        controls_text = "CONTROLS: ↑↓←→ Move (Player) | SPACE Pause | ESC Menu | R Restart"
        text_surface = font.render(controls_text, True, PAC_YELLOW)
        self.surface.blit(text_surface, (controls_rect.x + 10, controls_rect.y + 3))
    
    
    def _draw_play_section(self):
        """Draw play/pause button section"""
        # Play button ở giữa 2 màn hình chơi - đẹp và thân thiện hơn
        button_width = 140
        button_height = 60
        button_x = (self.ai_game_area_rect.right + self.player_game_area_rect.x) // 2 - button_width // 2
        button_y = (self.ai_game_area_rect.y + self.ai_game_area_rect.height) // 2 - button_height // 2
        
        try:
            font = pygame.font.Font(FONT_PATH, 18)
        except:
            font = pygame.font.Font(None, 18)
        
        # Play/Pause button
        button_rect = pygame.Rect(button_x, button_y, button_width, button_height)
        
        # Button glow effect với animation
        glow_size = int(8 + 4 * math.sin(self.animation_time * 4))
        button_glow = button_rect.inflate(glow_size, glow_size)
        glow_color = (100 + int(50 * math.sin(self.animation_time * 3)), 
                     100 + int(50 * math.sin(self.animation_time * 3)), 
                     150 + int(50 * math.sin(self.animation_time * 3)))
        pygame.draw.rect(self.surface, glow_color, button_glow, 4)
        
        # Button background với gradient
        for i in range(button_rect.height):
            alpha = int(60 + (i / button_rect.height) * 40)
            color = (alpha, alpha, alpha + 40)
            pygame.draw.line(self.surface, color, 
                           (button_rect.x, button_rect.y + i),
                           (button_rect.right, button_rect.y + i))
        
        # Button border
        pygame.draw.rect(self.surface, PAC_YELLOW, button_rect, 4)
        pygame.draw.rect(self.surface, (255, 255, 100), button_rect, 2)
        
        # Button text
        button_text_str = "PAUSE" if self.is_playing else "PLAY"
        button_text = font.render(button_text_str, True, PAC_YELLOW)
        text_rect = button_text.get_rect(center=button_rect.center)
        self.surface.blit(button_text, text_rect)
        
        # Store button rect for click detection
        self.play_button_rect = button_rect
    
    def get_ai_game_area_rect(self):
        """
        Lấy rectangle của AI game area để render game
        Returns:
            pygame.Rect của AI game area
        """
        return self.ai_game_area_rect
    
    def get_player_game_area_rect(self):
        """
        Lấy rectangle của Player game area để render game
        Returns:
            pygame.Rect của Player game area
        """
        return self.player_game_area_rect
    
    def get_control_panel_rect(self):
        """
        Lấy rectangle của control panel
        Returns:
            pygame.Rect của control panel
        """
        return self.control_panel_rect
    
    def handle_selectbox_event(self, event):
        """
        Xử lý sự kiện selectbox và trả về nếu algorithm thay đổi
        Args:
            event: Pygame event
        Returns:
            True nếu algorithm thay đổi, False nếu không
        """
        if self.algorithm_selectbox:
            if self.algorithm_selectbox.handle_event(event):
                # Kiểm tra xem selection có thay đổi không
                new_algorithm = self.algorithm_selectbox.get_selected_value()
                if new_algorithm and new_algorithm != self.algorithm:
                    self.algorithm = new_algorithm
                    return True
        return False
    
    def handle_play_button_click(self, event):
        """
        Xử lý sự kiện click play button
        Args:
            event: Pygame event
        Returns:
            True nếu play state thay đổi, False nếu không
        """
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  # Left click
            if hasattr(self, 'play_button_rect') and self.play_button_rect.collidepoint(event.pos):
                self.is_playing = not self.is_playing
                return True  # Báo hiệu play state đã thay đổi
        return False
    
    def update(self):
        """
        Cập nhật animation của layout
        - Tăng animation_time mỗi frame
        """
        self.animation_time += 0.02
