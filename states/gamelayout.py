
# =============================================================================
# GAMELAYOUT.PY - LAYOUT UI CHO GAME PAC-MAN
# =============================================================================
# File này chứa GameLayout - quản lý giao diện UI trong game
# Bao gồm control panel, game area, và các hiệu ứng visual
import pygame
import math
from ui.uicomponent import UIComponent
from ui.constants import *
from ui.selectbox import SelectBox
from ui.ai_mode_selector import AIModeSelector

class GameLayout(UIComponent):
    """
    GameLayout - Quản lý layout UI cho game Pac-Man
    - Chia màn hình thành game area và control panel
    - Quản lý thông tin game (score, lives, level, algorithm)
    - Có hiệu ứng visual và animation đẹp mắt
    - Hỗ trợ selectbox để chọn thuật toán AI
    """
    def __init__(self, app):
        """
        Khởi tạo GameLayout
        Args:
            app: Tham chiếu đến App chính
        """
        super().__init__(app)
        # Các rectangle chính
        self.game_area_rect = None      # Khu vực game
        self.control_panel_rect = None  # Panel điều khiển
        self.background_rect = None     # Background chính
        
        # Setup layout dimensions
        self._setup_layout()
        
        # Thông tin game
        self.score = 0          # Điểm số
        self.lives = 55          # Số mạng
        self.level = 1          # Level hiện tại
        self.algorithm = "BFS"  # Thuật toán AI
        self.ghost_mode = True  # Chế độ Ghost
        self.is_playing = False # Trạng thái play/pause
        
        # Tùy chọn thuật toán cho selectbox - sẽ được cập nhật dựa trên AI mode
        # Thêm các thuật toán mới vào danh sách bên dưới nếu cần
        self.algorithm_options = [
            "BFS", "DFS", "A*", 
            "UCS", "IDS", "GBFS",
            "Hill Climbing", "Genetic Algorithm", "Minimax",
            "Alpha-Beta", "A* Online"
        ] 

        self.online_algorithms = [
            "Hill Climbing", "Minimax",
            "Genetic Algorithm", "Alpha-Beta", "A* Online" ,"GBFS"
        ]

        self.offline_algorithms = ["BFS", "DFS", "A*", "UCS", "IDS"]  

        # Tùy chọn Ghost mode cho selectbox
        self.ghost_mode_options = ["Ghost ON", "Ghost OFF"]
        
        self.heuristic_options = ["NONE", "MANHATTAN", "EUCLIDEAN", "MAZEDISTANCE"]
        self.current_heuristic = 0  # Mặc định NONE
        
        # Few pellets mode settings
        self.few_pellets_mode = False
        self.few_pellets_count = 20
        self.preset_modes = [
            {"name": "Normal", "count": 0, "description": "All pellets"},
            {"name": "Few (7)", "count": 7, "description": "7 pellets only"},
        ]
        self.selected_preset = 0  # Normal mode by default
        
        # Current AI mode để track thay đổi
        self.current_ai_mode = "OFFLINE"  # Mặc định
        
        # Khởi tạo selectbox
        self.algorithm_selectbox = None
        self.ghost_mode_selectbox = None
        self.few_pellets_selectbox = None
        self.heuristic_selectbox = None
        self.ai_mode_selector = None
        self._setup_selectbox()
        
        self.update_algorithm_options_for_ai_mode(self.current_ai_mode)
        
        # Animation
        self.animation_time = 0
        
    def update_algorithm_options_for_ai_mode(self, ai_mode):
        if ai_mode == "ONLINE":
            self.algorithm_options = self.online_algorithms.copy()
        elif ai_mode == "OFFLINE":
            self.algorithm_options = self.offline_algorithms.copy()
        
        # Cập nhật algorithm selectbox nếu đã được khởi tạo
        if self.algorithm_selectbox:
            self.algorithm_selectbox.options = self.algorithm_options
            # Reset selection nếu algorithm hiện tại không có trong danh sách mới
            if self.algorithm not in self.algorithm_options:
                self.algorithm = self.algorithm_options[0] if self.algorithm_options else "BFS"
            # Cập nhật selected option
            if self.algorithm in self.algorithm_options:
                self.algorithm_selectbox.selected_option = self.algorithm_options.index(self.algorithm)
            else:
                self.algorithm_selectbox.selected_option = 0
        
        self.current_ai_mode = ai_mode
        
    def _setup_layout(self):
        """
        Setup kích thước layout cho game
        - Chia màn hình thành game area và control panel
        - Giữ aspect ratio của game gốc
        - Tối ưu hóa không gian cho game
        """
        # Background chính chiếm toàn bộ màn hình
        self.background_rect = pygame.Rect(0, 0, self.app.WIDTH, self.app.HEIGHT)
        
        panel_width = 300 
        panel_height = self.app.HEIGHT
        panel_x = self.app.WIDTH - panel_width
        panel_y = 0
        
        self.control_panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        
        # Game area - giữ aspect ratio đúng cho Pac-Man
        # Tính toán kích thước tối ưu dựa trên kích thước game gốc
        from constants import SCREENSIZE
        original_width, original_height = SCREENSIZE
        
        # Để chỗ cho title và margins
        available_width = self.app.WIDTH - panel_width - 40  # 20px margin mỗi bên
        available_height = self.app.HEIGHT - 120  # Thêm chỗ cho title
        
        # Tính scale để giữ aspect ratio
        scale_x = available_width / original_width
        scale_y = available_height / original_height
        scale = min(scale_x, scale_y)  # Dùng scale nhỏ hơn để giữ aspect ratio
        
        # Tính kích thước game area cuối cùng
        game_width = int(original_width * scale)
        game_height = int(original_height * scale)
        
        # Căn giữa game area - di chuyển xuống nhiều hơn
        game_x = (self.app.WIDTH - panel_width - game_width) // 2
        game_y = 100  # Thêm chỗ cho title
        
        self.game_area_rect = pygame.Rect(game_x, game_y, game_width, game_height)
    
    def _setup_selectbox(self):
        """Setup the algorithm and ghost mode selectboxes"""
        
        selectbox_x = self.control_panel_rect.x + 15
        selectbox_y = 660  # Di chuyển xuống thấp hơn nữa
        selectbox_width = self.control_panel_rect.width - 30 
        selectbox_height = 40  
        

        # Ghost mode selectbox
        self.ghost_mode_selectbox = SelectBox(
            selectbox_x, selectbox_y, selectbox_width, selectbox_height,
            self.ghost_mode_options, font_size=12
        )
        try:
            self.ghost_mode_selectbox.font = pygame.font.Font(FONT_PATH, 12)
        except:
            self.ghost_mode_selectbox.font = pygame.font.Font(None, 12)
        
        self.ghost_mode_selectbox.bg_color = (70, 70, 100) 
        self.ghost_mode_selectbox.border_color = GHOST_PINK  
        self.ghost_mode_selectbox.selected_color = (200, 120, 240) 
        self.ghost_mode_selectbox.hover_color = (90, 90, 120) 
        self.ghost_mode_selectbox.text_color = DOT_WHITE  
        
        # Set initial selection based on current ghost mode
        if self.ghost_mode:
            self.ghost_mode_selectbox.selected_option = 0  # Ghost ON
        else:
            self.ghost_mode_selectbox.selected_option = 1  # Ghost OFF
        

        # Heuristic selectbox
        heuristic_selectbox_y = selectbox_y + selectbox_height + 50
        self.heuristic_selectbox = SelectBox(
            selectbox_x, heuristic_selectbox_y, selectbox_width, selectbox_height,
            self.heuristic_options, font_size=12
        )
        
        try:
            self.heuristic_selectbox.font = pygame.font.Font(FONT_PATH, 12)
        except:
            self.heuristic_selectbox.font = pygame.font.Font(None, 12)
        
        self.heuristic_selectbox.bg_color = (70, 70, 100) 
        self.heuristic_selectbox.border_color = (0, 200, 100)  # Green color
        self.heuristic_selectbox.selected_color = (100, 255, 150) 
        self.heuristic_selectbox.hover_color = (90, 90, 120) 
        self.heuristic_selectbox.text_color = DOT_WHITE  
        self.heuristic_selectbox.selected_option = self.current_heuristic

        # Algorithm selectbox
        algorithm_selectbox_y = selectbox_y + selectbox_height + 150
        self.algorithm_selectbox = SelectBox(
            selectbox_x, algorithm_selectbox_y, selectbox_width, selectbox_height,
            self.algorithm_options, font_size=12
        )
        
        try:
            self.algorithm_selectbox.font = pygame.font.Font(FONT_PATH, 12)
        except:
            self.algorithm_selectbox.font = pygame.font.Font(None, 12)
        
        self.algorithm_selectbox.bg_color = (70, 70, 100) 
        self.algorithm_selectbox.border_color = PAC_YELLOW  
        self.algorithm_selectbox.selected_color = (120, 200, 240) 
        self.algorithm_selectbox.hover_color = (90, 90, 120) 
        self.algorithm_selectbox.text_color = DOT_WHITE  
        
        if self.algorithm in self.algorithm_options:
            self.algorithm_selectbox.selected_option = self.algorithm_options.index(self.algorithm)
        
      
        
        # AI Mode Selector
        ai_selector_y = 920
        self.ai_mode_selector = AIModeSelector(
            selectbox_x, ai_selector_y, selectbox_width, selectbox_height
        )

        # Few Pellets Mode selectbox (trong section riêng)
        few_pellets_options = [mode["name"] for mode in self.preset_modes]
        few_pellets_y = 340  # Vị trí trong few pellets section
        self.few_pellets_selectbox = SelectBox(
            selectbox_x, few_pellets_y, selectbox_width, selectbox_height,
            few_pellets_options, font_size=12
        )
        
        # Use game font
        try:
            self.few_pellets_selectbox.font = pygame.font.Font(FONT_PATH, 12)
        except:
            self.few_pellets_selectbox.font = pygame.font.Font(None, 12)
        
        self.few_pellets_selectbox.bg_color = (70, 70, 100) 
        self.few_pellets_selectbox.border_color = GHOST_ORANGE  
        self.few_pellets_selectbox.selected_color = (240, 160, 80) 
        self.few_pellets_selectbox.hover_color = (90, 90, 120) 
        self.few_pellets_selectbox.text_color = DOT_WHITE  
        
        # Set initial selection
        self.few_pellets_selectbox.selected_option = self.selected_preset
              
    def set_game_info(self, score=0, lives=3, level=1, algorithm="BFS", ghost_mode=True, game_time="00:00", game_instance=None):
        """
        Cập nhật thông tin game
        Args:
            score: Điểm số hiện tại
            lives: Số mạng còn lại
            level: Level hiện tại
            algorithm: Thuật toán AI đang sử dụng
            ghost_mode: Chế độ Ghost (True/False)
            game_time: Thời gian game hiện tại
            game_instance: Instance của game để lấy thông tin path
        """
        self.score = score
        self.lives = lives
        self.level = level
        self.algorithm = algorithm
        self._game_instance = game_instance
        self.ghost_mode = ghost_mode
        self.game_time = game_time
        
        # Lấy thông tin steps từ game instance
        if game_instance and hasattr(game_instance, 'get_step_info'):
            self.step_info = game_instance.get_step_info()
        else:
            self.step_info = {
                'total_steps': 0,
                'ai_steps': 0,
                'player_steps': 0,
                'current_mode': 'Unknown'
            }
    
    def update(self):
        """Cập nhật layout animations"""
        super().update()
    
    def render(self):
        """
        Render toàn bộ game layout
        - Vẽ background với hiệu ứng
        - Vẽ game area frame
        - Vẽ control panel
        - Vẽ thông tin game
        - Vẽ banner sinh viên
        """
        self._draw_background()
        self._draw_game_area()
        self._draw_control_panel()
        self._draw_game_info()
        self._draw_student_banner()
    
    def _draw_background(self):
        """Draw the main background with enhanced transparency effects"""
        # Create a more subtle gradient background
        for y in range(self.app.HEIGHT):
            intensity = int(8 + (y / self.app.HEIGHT) * 15)  # More subtle gradient
            color = (intensity, intensity, intensity + 20)
            pygame.draw.line(self.surface, color, (0, y), (self.app.WIDTH, y))
        
        # Add animated starfield with more transparency
        self.animation_time += 0.02
        for i in range(150):  # More stars for better effect
            x = (i * 37 + self.animation_time * 10) % self.app.WIDTH
            y = (i * 23 + self.animation_time * 5) % self.app.HEIGHT
            alpha = int(30 + 20 * math.sin(self.animation_time * 2 + i * 0.1))  # More transparent
            color = (alpha, alpha, alpha + 30)
            size = 1 + int(1 * math.sin(self.animation_time * 3 + i * 0.2))
            pygame.draw.circle(self.surface, color, (int(x), int(y)), size)
        
        # Add floating particles with transparency
        for i in range(30):  # More particles
            x = (self.animation_time * 15 + i * 80) % self.app.WIDTH
            y = 100 + 200 * math.sin(self.animation_time * 1.5 + i * 0.3)
            alpha = int(40 + 30 * math.sin(self.animation_time * 2 + i))  # More transparent
            color = (alpha, alpha // 2, alpha + 20)
            pygame.draw.circle(self.surface, color, (int(x), int(y)), 2)
        
        # Add nebula-like effects for more depth
        for i in range(5):
            x = (self.animation_time * 5 + i * 200) % self.app.WIDTH
            y = (self.animation_time * 3 + i * 150) % self.app.HEIGHT
            alpha = int(15 + 10 * math.sin(self.animation_time * 1 + i))
            color = (alpha, alpha // 3, alpha + 15)
            size = 30 + int(20 * math.sin(self.animation_time * 0.5 + i))
            pygame.draw.circle(self.surface, color, (int(x), int(y)), size)
    
    def _draw_game_area(self):
        overlay_surface = pygame.Surface((self.game_area_rect.width, self.game_area_rect.height), pygame.SRCALPHA)
        
        # Semi-transparent background with gradient
        for y in range(self.game_area_rect.height):
            alpha = int(20 + (y / self.game_area_rect.height) * 10)  # Very subtle gradient
            color = (alpha, alpha, alpha + 15, alpha)
            pygame.draw.line(overlay_surface, color, (0, y), (self.game_area_rect.width, y))
        
        # Add subtle animated particles inside game area
        for i in range(20):
            x = (self.animation_time * 8 + i * 50) % self.game_area_rect.width
            y = (self.animation_time * 5 + i * 30) % self.game_area_rect.height
            alpha = int(15 + 10 * math.sin(self.animation_time * 2 + i * 0.3))
            color = (alpha, alpha, alpha + 20, alpha)
            size = 1 + int(1 * math.sin(self.animation_time * 3 + i * 0.2))
            pygame.draw.circle(overlay_surface, color, (int(x), int(y)), size)
        
        # Blit the overlay to create transparency effect
        self.surface.blit(overlay_surface, self.game_area_rect.topleft)
        
        # Enhanced outer glow effect - more dramatic
        for i in range(6, 0, -1):
            alpha = int(40 - i * 6)
            color = (alpha, alpha + 40, alpha + 80)
            glow_rect = self.game_area_rect.inflate(i * 3, i * 3)
            pygame.draw.rect(self.surface, color, glow_rect, 2)
        
        # Main outer frame with animated glow
        glow_intensity = int(100 + 50 * math.sin(self.animation_time * 2))
        pygame.draw.rect(self.surface, (glow_intensity, glow_intensity + 50, glow_intensity + 100), self.game_area_rect, 4)
        pygame.draw.rect(self.surface, GHOST_BLUE, self.game_area_rect, 2)
        pygame.draw.rect(self.surface, (0, 150, 255), self.game_area_rect, 1)
        
        # Inner frame with enhanced animation
        inner_rect = self.game_area_rect.inflate(-12, -12)
        pulse = int(3 + 2 * math.sin(self.animation_time * 4))
        pulse_r = max(0, min(255, int(255 + 30 * math.sin(self.animation_time * 3))))
        pulse_g = max(0, min(255, int(255 + 30 * math.sin(self.animation_time * 3))))
        pulse_b = max(0, min(255, int(100 + 30 * math.sin(self.animation_time * 3))))
        pulse_color = (pulse_r, pulse_g, pulse_b)
        pygame.draw.rect(self.surface, pulse_color, inner_rect, pulse)
        pygame.draw.rect(self.surface, (255, 255, 150), inner_rect, 1)
        
        # Corner decorations removed for cleaner interface
        
        # Title positioned above game area, centered
        try:
            font_title = pygame.font.Font(FONT_PATH, 32)
            font_subtitle = pygame.font.Font(FONT_PATH, 16)
        except:
            font_title = pygame.font.Font(None, 32)
            font_subtitle = pygame.font.Font(None, 16)
        
        title_text = "PAC-MAN GAME"
        title_surface = font_title.render(title_text, True, (255, 255, 0))
        title_rect = title_surface.get_rect(center=(self.game_area_rect.centerx, 40))
        
        # Simple glow effect - just 2 layers for clean look
        for offset in [(2, 2), (-2, -2), (2, -2), (-2, 2)]:
            glow_text = font_title.render(title_text, True, (100, 100, 0))
            self.surface.blit(glow_text, (title_rect.x + offset[0], title_rect.y + offset[1]))
        
        # Main title with subtle pulsing
        pulse_alpha = int(255 + 20 * math.sin(self.animation_time * 3))
        pulse_alpha = max(200, min(255, pulse_alpha))
        title_color = (pulse_alpha, pulse_alpha, 0)
        title_surface = font_title.render(title_text, True, title_color)
        self.surface.blit(title_surface, title_rect)
        
        # Subtitle positioned below title
        subtitle_text = "AI-POWERED CLASSIC"
        subtitle_surface = font_subtitle.render(subtitle_text, True, (200, 200, 255))
        subtitle_rect = subtitle_surface.get_rect(center=(self.game_area_rect.centerx, 70))
        
        # Subtitle with subtle glow
        for offset in [(1, 1), (-1, -1)]:
            subtitle_glow = font_subtitle.render(subtitle_text, True, (50, 50, 100))
            self.surface.blit(subtitle_glow, (subtitle_rect.x + offset[0], subtitle_rect.y + offset[1]))
        
        # Main subtitle
        subtitle_color = (200, 200, 255)
        subtitle_surface = font_subtitle.render(subtitle_text, True, subtitle_color)
        self.surface.blit(subtitle_surface, subtitle_rect)
    
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
        
        title_text = font.render("CONTROL PANEL", True, PAC_YELLOW)
        title_rect = title_text.get_rect(center=(self.control_panel_rect.centerx, 40))
        
        # Multiple glow layers
        glow_colors = [(80, 80, 0), (120, 120, 0), (160, 160, 0)]
        for i, glow_color in enumerate(glow_colors):
            for offset in [(i+1, i+1), (-i-1, -i-1), (i+1, -i-1), (-i-1, i+1)]:
                glow_text = font.render("CONTROL PANEL", True, glow_color)
                self.surface.blit(glow_text, (title_rect.x + offset[0], title_rect.y + offset[1]))
        
        # Pulsing title
        pulse_alpha = int(255 + 30 * math.sin(self.animation_time * 4))
        pulse_alpha = max(0, min(255, pulse_alpha))
        title_color = (pulse_alpha, pulse_alpha, 0)
        title_text = font.render("CONTROL PANEL", True, title_color)
        self.surface.blit(title_text, title_rect)
        
        # Draw panel sections with better spacing - reordered
        self._draw_score_section()
        self._draw_lives_section()
        self._draw_stats_section()
        self._draw_few_pellets_section()  
        self._draw_play_section() 
        self._draw_algorithm_section()  
        
        # Draw selectboxes on top (highest z-index)
        self._draw_selectboxes()
    
    def _draw_selectboxes(self):
        """Draw all selectboxes on top of other elements"""
        # AI Mode Selector
        if self.ai_mode_selector:
            self.ai_mode_selector.draw(self.surface)
        
        # Few Pellets Selectbox
        if self.few_pellets_selectbox:
            glow_intensity = int(100 + 50 * math.sin(self.animation_time * 5))
            glow_rect = pygame.Rect(
                self.few_pellets_selectbox.rect.x - 3,
                self.few_pellets_selectbox.rect.y - 3,
                self.few_pellets_selectbox.rect.width + 6,
                self.few_pellets_selectbox.rect.height + 6
            )
        pygame.draw.rect(self.surface, (glow_intensity, glow_intensity // 2, 0), glow_rect, 2)
        self.few_pellets_selectbox.draw(self.surface)

        
        # Algorithm Selectbox (only in AI mode)
        is_ai_mode = True
        if hasattr(self.app, 'state_machine') and self.app.state_machine.current_state:
            current_state = self.app.state_machine.current_state
            if hasattr(current_state, 'game') and hasattr(current_state.game, 'ai_mode'):
                is_ai_mode = current_state.game.ai_mode
        
        if self.algorithm_selectbox and is_ai_mode:
            glow_intensity = int(100 + 50 * math.sin(self.animation_time * 6))
            glow_rect = pygame.Rect(
                self.algorithm_selectbox.rect.x - 3,
                self.algorithm_selectbox.rect.y - 3,
                self.algorithm_selectbox.rect.width + 6,
                self.algorithm_selectbox.rect.height + 6
            )
            pygame.draw.rect(self.surface, (glow_intensity, glow_intensity, 0), glow_rect, 2)
            self.algorithm_selectbox.draw(self.surface)
        
        # Heuristic Selectbox (for all algorithms in AI mode)
        if self.heuristic_selectbox and is_ai_mode:
            glow_intensity = int(100 + 50 * math.sin(self.animation_time * 5))
            glow_rect = pygame.Rect(
                self.heuristic_selectbox.rect.x - 3,
                self.heuristic_selectbox.rect.y - 3,
                self.heuristic_selectbox.rect.width + 6,
                self.heuristic_selectbox.rect.height + 6
            )
            pygame.draw.rect(self.surface, (0, glow_intensity, glow_intensity//2), glow_rect, 2)
            self.heuristic_selectbox.draw(self.surface)
        
        # Ghost Mode Selectbox
        if self.ghost_mode_selectbox:
            glow_intensity = int(100 + 50 * math.sin(self.animation_time * 4))
            glow_rect = pygame.Rect(
                self.ghost_mode_selectbox.rect.x - 3,
                self.ghost_mode_selectbox.rect.y - 3,
                self.ghost_mode_selectbox.rect.width + 6,
                self.ghost_mode_selectbox.rect.height + 6
            )
            pygame.draw.rect(self.surface, (glow_intensity, 0, glow_intensity), glow_rect, 2)
            self.ghost_mode_selectbox.draw(self.surface)
    
    def _draw_score_section(self):
        """Draw score section with enhanced design"""
        y_start = 80
        try:
            font_large = pygame.font.Font(FONT_PATH, 16)
            font_medium = pygame.font.Font(FONT_PATH, 14)
            font_small = pygame.font.Font(FONT_PATH, 12)
        except:
            font_large = pygame.font.Font(None, 16)
            font_medium = pygame.font.Font(None, 14)
            font_small = pygame.font.Font(None, 12)
        
        # Section background with enhanced glow
        section_rect = pygame.Rect(self.control_panel_rect.x + 20, y_start - 5, 
                                 self.control_panel_rect.width - 40, 110)  # Adjusted height
        
        # Enhanced glow effect
        glow_rect = section_rect.inflate(6, 6)
        pygame.draw.rect(self.surface, (80, 80, 120), glow_rect, 3)
        
        # Main background with gradient
        for i in range(section_rect.height):
            alpha = int(50 + (i / section_rect.height) * 20)
            color = (alpha, alpha, alpha + 30)
            pygame.draw.line(self.surface, color, 
                           (section_rect.x, section_rect.y + i),
                           (section_rect.right, section_rect.y + i))
        
        pygame.draw.rect(self.surface, GHOST_BLUE, section_rect, 3)
        pygame.draw.rect(self.surface, (0, 150, 255), section_rect, 1)
        
        # Score section
        score_text = font_large.render("SCORE", True, PAC_YELLOW)
        self.surface.blit(score_text, (self.control_panel_rect.x + 30, y_start))
        
        # Animated score value with better formatting
        score_pulse = int(255 + 40 * math.sin(self.animation_time * 4))
        score_pulse = max(0, min(255, score_pulse))
        score_color = (score_pulse, score_pulse, score_pulse)
        score_value = font_medium.render(f"{self.score:,}", True, score_color)
        self.surface.blit(score_value, (self.control_panel_rect.x + 30, y_start + 25))
        
        # Level section
        level_text = font_large.render("LEVEL", True, PAC_YELLOW)
        self.surface.blit(level_text, (self.control_panel_rect.x + 30, y_start + 55))
        
        # Animated level value (display level + 1 for user-friendly display)
        level_pulse = int(255 + 30 * math.sin(self.animation_time * 3 + 1))
        level_pulse = max(0, min(255, level_pulse))
        level_color = (level_pulse, level_pulse, level_pulse)
        display_level = self.level + 1  # Show level + 1 to user
        level_value = font_medium.render(f"{display_level}", True, level_color)
        self.surface.blit(level_value, (self.control_panel_rect.x + 30, y_start + 80))
    
    def _draw_play_section(self):
        """Draw play/pause button section"""
        y_start = 1100  # Above algorithm section
        try:
            font = pygame.font.Font(FONT_PATH, 14)
        except:
            font = pygame.font.Font(None, 14)
        
        # Section background with glow
        section_rect = pygame.Rect(self.control_panel_rect.x + 20, y_start - 5, 
                                 self.control_panel_rect.width - 40, 80)
        
        # Enhanced glow effect
        glow_rect = section_rect.inflate(6, 6)
        pygame.draw.rect(self.surface, (80, 80, 120), glow_rect, 3)
        
        # Main background with gradient
        for i in range(section_rect.height):
            alpha = int(50 + (i / section_rect.height) * 20)
            color = (alpha, alpha, alpha + 30)
            pygame.draw.line(self.surface, color, 
                           (section_rect.x, section_rect.y + i),
                           (section_rect.right, section_rect.y + i))
        
        pygame.draw.rect(self.surface, GHOST_BLUE, section_rect, 3)
        pygame.draw.rect(self.surface, (0, 150, 255), section_rect, 1)
        
        # Play/Pause button
        button_rect = pygame.Rect(self.control_panel_rect.x + 30, y_start + 15, 
                                 self.control_panel_rect.width - 60, 50)
        
        # Button glow effect
        button_glow = button_rect.inflate(4, 4)
        pygame.draw.rect(self.surface, (100, 100, 150), button_glow, 2)
        
        # Button background
        pygame.draw.rect(self.surface, (60, 60, 100), button_rect)
        pygame.draw.rect(self.surface, PAC_YELLOW, button_rect, 2)
        
        # Button text - show PLAY or PAUSE based on state
        button_text_str = "PAUSE" if self.is_playing else "PLAY"
        button_text = font.render(button_text_str, True, PAC_YELLOW)
        text_rect = button_text.get_rect(center=button_rect.center)
        self.surface.blit(button_text, text_rect)
        
        # Store button rect for click detection
        self.play_button_rect = button_rect
    
    def _draw_lives_section(self):
        """Draw lives section"""
        y_start = 200  # Moved down to accommodate taller score section
        try:
            font = pygame.font.Font(FONT_PATH, 14)
        except:
            font = pygame.font.Font(None, 14)
        
        # Section background with glow
        section_rect = pygame.Rect(self.control_panel_rect.x + 20, y_start - 5, 
                                 self.control_panel_rect.width - 40, 70)  # Taller section
        
        # Glow effect
        glow_rect = section_rect.inflate(4, 4)
        pygame.draw.rect(self.surface, (60, 60, 100), glow_rect, 2)
        
        # Main background
        pygame.draw.rect(self.surface, (45, 45, 70), section_rect)
        pygame.draw.rect(self.surface, GHOST_BLUE, section_rect, 2)
        pygame.draw.rect(self.surface, (0, 150, 255), section_rect, 1)
        
        lives_text = font.render("LIVES", True, PAC_YELLOW)
        self.surface.blit(lives_text, (self.control_panel_rect.x + 30, y_start))
        
        # Draw life indicators with enhanced design
        for i in range(self.lives):
            x = self.control_panel_rect.x + 30 + (i * 40)  # More spacing between lives
            y = y_start + 30
            
            # Animated Pac-Man
            pac_size = int(12 + 2 * math.sin(self.animation_time * 4 + i))
            
            # Glow effect
            for j in range(3, 0, -1):
                glow_alpha = int(100 - j * 30)
                glow_color = (glow_alpha, glow_alpha, 0)
                pygame.draw.circle(self.surface, glow_color, (x, y), pac_size + j * 2, 1)
            
            # Pac-Man body
            pygame.draw.circle(self.surface, PAC_YELLOW, (x, y), pac_size)
            
            # Pac-Man mouth (animated)
            mouth_angle = math.pi * 0.2 + self.animation_time * 3 + i * 0.5
            mouth_width = math.pi * 0.8 + 0.3 * math.sin(self.animation_time * 5 + i)
            pygame.draw.arc(self.surface, (0, 0, 0), (x-pac_size, y-pac_size, pac_size*2, pac_size*2), 
                           mouth_angle, mouth_angle + mouth_width, 4)
            
            # Eye
            eye_x = x + int(3 * math.cos(mouth_angle + mouth_width/2))
            eye_y = y + int(3 * math.sin(mouth_angle + mouth_width/2))
            pygame.draw.circle(self.surface, (0, 0, 0), (eye_x, eye_y), 2)
    
    def _draw_algorithm_section(self):
        y_start = 620  
        try:
            font = pygame.font.Font(FONT_PATH, 14)
        except:
            font = pygame.font.Font(None, 14)
        section_rect = pygame.Rect(self.control_panel_rect.x + 20, y_start - 5, 
                                 self.control_panel_rect.width - 40, 300)  
        
        glow_rect = section_rect.inflate(6, 6)
        pygame.draw.rect(self.surface, (80, 80, 120), glow_rect, 3)
        
        pygame.draw.rect(self.surface, (50, 50, 80), section_rect)
        pygame.draw.rect(self.surface, PAC_YELLOW, section_rect, 3)  
        pygame.draw.rect(self.surface, (0, 180, 255), section_rect, 1)
        
        ghost_text = font.render("GHOST MODE", True, GHOST_PINK)
        self.surface.blit(ghost_text, (self.control_panel_rect.x + 30, y_start))
        
        ghost_mode_text = "Ghost: ON" if self.ghost_mode else "Ghost: OFF"
        ghost_mode_color = GHOST_PINK if self.ghost_mode else DOT_WHITE
        ghost_mode_surface = font.render(ghost_mode_text, True, ghost_mode_color)
        self.surface.blit(ghost_mode_surface, (self.control_panel_rect.x + 30, y_start + 20))
        
        algo_text = font.render("AI ALGORITHM", True, PAC_YELLOW)
        self.surface.blit(algo_text, (self.control_panel_rect.x + 30, y_start + 200))  
        
        mode_text = "Mode: AI"
        if hasattr(self.app, 'state_machine') and self.app.state_machine.current_state:
            current_state = self.app.state_machine.current_state
            if hasattr(current_state, 'game') and hasattr(current_state.game, 'ai_mode'):
                mode_text = "Mode: AI" if current_state.game.ai_mode else "Mode: Player"
        
        mode_color = PAC_YELLOW if "AI" in mode_text else GHOST_PINK
        mode_surface = font.render(mode_text, True, mode_color)
        self.surface.blit(mode_surface, (self.control_panel_rect.x + 30, y_start + 180)) 
        
        # Draw heuristic label (hiện cho tất cả algorithms)
        if self.heuristic_selectbox and "AI" in mode_text:
            heuristic_label = font.render("ALGORITHM HEURISTIC", True, (0, 200, 100))
            self.surface.blit(heuristic_label, (self.control_panel_rect.x + 30, y_start + 100))
                            
    def _draw_stats_section(self):
        """Draw additional stats section"""
        y_start = 450  # Moved down to accommodate taller controls section
        try:
            font = pygame.font.Font(FONT_PATH, 12)
        except:
            font = pygame.font.Font(None, 12)
        
        # Section background with glow
        section_rect = pygame.Rect(self.control_panel_rect.x + 20, y_start - 5, 
                                 self.control_panel_rect.width - 40, 150)
        
        # Glow effect
        glow_rect = section_rect.inflate(4, 4)
        pygame.draw.rect(self.surface, (60, 60, 100), glow_rect, 2)
        
        # Main background
        pygame.draw.rect(self.surface, (45, 45, 70), section_rect)
        pygame.draw.rect(self.surface, GHOST_BLUE, section_rect, 2)
        pygame.draw.rect(self.surface, (0, 150, 255), section_rect, 1)
        
        # Stats title
        stats_text = font.render("GAME STATE", True, PAC_YELLOW)
        self.surface.blit(stats_text, (self.control_panel_rect.x + 30, y_start))
        
        # Game Time display
        time_text = font.render(f"Time: {self.game_time}", True, GHOST_PINK)
        self.surface.blit(time_text, (self.control_panel_rect.x + 30, y_start + 25))
        
        # Algorithm display
        algo_text = font.render(f"Algorithm: {self.algorithm}", True, DOT_WHITE)
        self.surface.blit(algo_text, (self.control_panel_rect.x + 30, y_start + 45))
        
        # Steps display
        if hasattr(self, 'step_info'):
            # AI/Player steps breakdown
            if self.step_info['ai_steps'] > 0 or self.step_info['player_steps'] > 0:
                breakdown_text = f"AI: {self.step_info['ai_steps']} | Player: {self.step_info['player_steps']}"
                breakdown_color = GHOST_BLUE if self.step_info['current_mode'] == 'AI' else PAC_YELLOW
                breakdown_surface = font.render(breakdown_text, True, breakdown_color)
                self.surface.blit(breakdown_surface, (self.control_panel_rect.x + 30, y_start + 105))
        else:
            # Debug: Hiển thị khi không có step_info
            debug_text = "No step_info"
            debug_surface = font.render(debug_text, True, (255, 0, 0))
            self.surface.blit(debug_surface, (self.control_panel_rect.x + 30, y_start + 85))
        
        # AI Path progress (giữ lại để hiển thị tiến trình AI)
        try:
            if hasattr(self, '_game_instance') and hasattr(self._game_instance, 'pacman'):
                path_info = self._game_instance.pacman.get_path_info()
                
                if isinstance(path_info, dict) and path_info['total_steps'] > 0:
                    # Display AI PATH progress
                    path_title = font.render("AI PATH:", True, GHOST_BLUE)
                    self.surface.blit(path_title, (self.control_panel_rect.x + 200, y_start))
                    
                    progress_text = f"{path_info['current_step']}/{path_info['total_steps']} ({path_info['progress_percent']:.1f}%)"
                    progress_color = GHOST_BLUE if not path_info['is_completed'] else PAC_YELLOW
                    text = font.render(progress_text, True, progress_color)
                    self.surface.blit(text, (self.control_panel_rect.x + 200, y_start + 20))
        except Exception:
            # Không hiển thị error
            pass
    
    def _draw_few_pellets_section(self):
        """Draw few pellets mode section"""
        y_start = 290  # Between stats and play sections
        try:
            font = pygame.font.Font(FONT_PATH, 14)
            font_small = pygame.font.Font(FONT_PATH, 12)
        except:
            font = pygame.font.Font(None, 14)
            font_small = pygame.font.Font(None, 12)
        
        # Section background with glow
        section_rect = pygame.Rect(self.control_panel_rect.x + 20, y_start - 5, 
                                 self.control_panel_rect.width - 40, 80)
        
        # Enhanced glow effect
        glow_rect = section_rect.inflate(6, 6)
        pygame.draw.rect(self.surface, (80, 80, 120), glow_rect, 3)
        
        # Main background with gradient
        for i in range(section_rect.height):
            alpha = int(50 + (i / section_rect.height) * 20)
            color = (alpha, alpha, alpha + 30)
            pygame.draw.line(self.surface, color, 
                           (section_rect.x, section_rect.y + i),
                           (section_rect.right, section_rect.y + i))
        
        pygame.draw.rect(self.surface, GHOST_ORANGE, section_rect, 3)
        pygame.draw.rect(self.surface, (255, 160, 0), section_rect, 1)
        
        # Section title
        title_text = font.render("PELLETS MODE", True, GHOST_ORANGE)
        self.surface.blit(title_text, (self.control_panel_rect.x + 30, y_start))
        
        # Current mode display
        if self.few_pellets_mode:
            mode_text = f"Few Pellets: {self.few_pellets_count}"
            mode_color = GHOST_ORANGE
        else:
            mode_text = "Normal: All Pellets"
            mode_color = DOT_WHITE
        
        mode_surface = font_small.render(mode_text, True, mode_color)
        self.surface.blit(mode_surface, (self.control_panel_rect.x + 30, y_start + 25))
        
        # Mode selector
        selector_text = font_small.render("Select Mode:", True, DOT_WHITE)
        self.surface.blit(selector_text, (self.control_panel_rect.x + 30, y_start + 45))
    
    def _draw_game_info(self):
        """Draw additional game information"""
        # Draw some floating elements
        for i in range(5):
            x = (self.animation_time * 20 + i * 100) % self.app.WIDTH
            y = 50 + 30 * math.sin(self.animation_time * 2 + i)
            pygame.draw.circle(self.surface, GHOST_PINK, (int(x), int(y)), 3)
    
    def get_game_area_rect(self):
        return self.game_area_rect
    
    def get_control_panel_rect(self):
        return self.control_panel_rect
    
    def handle_selectbox_event(self, event):
        """
        Xử lý sự kiện selectbox và trả về nếu algorithm hoặc ghost mode thay đổi
        """
        algorithm_changed = False
        ghost_mode_changed = False
        ai_mode_changed = False
        few_pellets_changed = False
        heuristic_changed = False
        
        # Chỉ xử lý selectbox khi ở AI mode
        is_ai_mode = True  # Mặc định
        if hasattr(self.app, 'state_machine') and self.app.state_machine.current_state:
            current_state = self.app.state_machine.current_state
            if hasattr(current_state, 'game') and hasattr(current_state.game, 'ai_mode'):
                is_ai_mode = current_state.game.ai_mode
        
        # Xử lý AI Mode Selector (luôn xử lý)
        if self.ai_mode_selector:
            if self.ai_mode_selector.handle_events(event):
                new_ai_mode = self.ai_mode_selector.get_current_mode()
                if new_ai_mode != self.current_ai_mode:
                    self.current_ai_mode = new_ai_mode
                    ai_mode_changed = True
        
        ghost_locked = self.current_ai_mode == "OFFLINE"
        
        if self.ghost_mode_selectbox:
            if ghost_locked:
                self.ghost_mode = False
                self.ghost_mode_selectbox.selected_option = 1
                self.ghost_mode_selectbox.is_open = False
                self._ghost_selectbox_hovered = False
            else:
                if event.type == pygame.MOUSEMOTION:
                    if hasattr(self.ghost_mode_selectbox, 'rect') and self.ghost_mode_selectbox.rect.collidepoint(event.pos):
                        if not getattr(self, '_ghost_selectbox_hovered', False):
                            self.app.sound_system.play_sound('button_hover')
                            self._ghost_selectbox_hovered = True
                    else:
                        self._ghost_selectbox_hovered = False

                if self.ghost_mode_selectbox.handle_event(event):
                    new_ghost_mode_text = self.ghost_mode_selectbox.get_selected_value()
                    if new_ghost_mode_text:
                        new_ghost_mode = (new_ghost_mode_text == 'Ghost ON')
                        if new_ghost_mode != self.ghost_mode:
                            self.ghost_mode = new_ghost_mode
                            ghost_mode_changed = True

        # Xử lý algorithm selectbox (ở dưới)
        if self.algorithm_selectbox and is_ai_mode:
            # Xử lý mouse hover cho selectbox
            if event.type == pygame.MOUSEMOTION:
                if hasattr(self.algorithm_selectbox, 'rect') and self.algorithm_selectbox.rect.collidepoint(event.pos):
                    if not getattr(self, '_algorithm_selectbox_hovered', False):
                        self.app.sound_system.play_sound('button_hover')
                        self._algorithm_selectbox_hovered = True
                else:
                    self._algorithm_selectbox_hovered = False
            
            if self.algorithm_selectbox.handle_event(event):
                # Kiểm tra xem selection có thay đổi không
                new_algorithm = self.algorithm_selectbox.get_selected_value()
                if new_algorithm and new_algorithm != self.algorithm:
                    self.algorithm = new_algorithm
                    algorithm_changed = True
        
        # Xử lý few pellets selectbox
        if self.few_pellets_selectbox:
            if event.type == pygame.MOUSEMOTION:
                if hasattr(self.few_pellets_selectbox, 'rect') and self.few_pellets_selectbox.rect.collidepoint(event.pos):
                    if not getattr(self, '_few_pellets_selectbox_hovered', False):
                        self.app.sound_system.play_sound('button_hover')
                        self._few_pellets_selectbox_hovered = True
                else:
                    self._few_pellets_selectbox_hovered = False
            
            if self.few_pellets_selectbox.handle_event(event):
                # Kiểm tra xem selection có thay đổi không
                new_preset_index = self.few_pellets_selectbox.selected_option
                if new_preset_index != self.selected_preset:
                    self.selected_preset = new_preset_index
                    selected_mode = self.preset_modes[new_preset_index]
                    
                    if selected_mode["count"] == 0:  # Normal mode
                        self.few_pellets_mode = False
                    elif selected_mode["count"] == -1:  # Custom mode
                        # Keep current settings for custom
                        pass
                    else:  # Specific count
                        self.few_pellets_mode = True
                        self.few_pellets_count = selected_mode["count"]
                    
                    few_pellets_changed = True
        
        # Xử lý heuristic selectbox 
        if self.heuristic_selectbox and is_ai_mode:
            if event.type == pygame.MOUSEMOTION:
                if hasattr(self.heuristic_selectbox, 'rect') and self.heuristic_selectbox.rect.collidepoint(event.pos):
                    if not getattr(self, '_heuristic_selectbox_hovered', False):
                        self.app.sound_system.play_sound('button_hover')
                        self._heuristic_selectbox_hovered = True
                else:
                    self._heuristic_selectbox_hovered = False
            
            if self.heuristic_selectbox.handle_event(event):
                # Kiểm tra xem selection có thay đổi không
                new_heuristic_index = self.heuristic_selectbox.selected_option
                if new_heuristic_index != self.current_heuristic:
                    self.current_heuristic = new_heuristic_index
                    heuristic_changed = True
        
        return algorithm_changed, ghost_mode_changed, ai_mode_changed, few_pellets_changed, heuristic_changed
    
    def handle_play_button_click(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:  
            if hasattr(self, 'play_button_rect') and self.play_button_rect.collidepoint(event.pos):
                self.app.sound_system.play_sound('button_click')
                self.is_playing = not self.is_playing
                return True 
                
        elif event.type == pygame.MOUSEMOTION:
            if hasattr(self, 'play_button_rect') and self.play_button_rect.collidepoint(event.pos):
                if not getattr(self, '_play_button_hovered', False):
                    self.app.sound_system.play_sound('button_hover')
                    self._play_button_hovered = True
            else:
                self._play_button_hovered = False
        return False
    
    def update(self):
        """
        Cập nhật animation của layout
        - Tăng animation_time mỗi frame
        """
        self.animation_time += 0.02
    
    def _draw_student_banner(self):
        """Vẽ banner thông tin sinh viên ở góc trái màn hình"""
        # Font cho banner - sử dụng Times New Roman hoặc font hệ thống
        font = None
        font_name = "Unknown"
        try:
            font = pygame.font.SysFont("Times New Roman", 18, bold=True)
            font_name = "Times New Roman"
        except:
            try:
                font = pygame.font.SysFont("Arial", 18, bold=True)
                font_name = "Arial"
            except:
                try:
                    font = pygame.font.SysFont("Calibri", 18, bold=True)
                    font_name = "Calibri"
                except:
                    try:
                        font = pygame.font.SysFont("Tahoma", 18, bold=True)
                        font_name = "Tahoma"
                    except:
                        # Fallback cuối cùng - font mặc định với kích thước lớn
                        font = pygame.font.Font(None, 20)
                        font_name = "Default"
        
        # Font đã được load thành công
        
        # Màu sắc - tất cả màu trắng
        name_color = (255, 255, 255)    # Trắng
        mssv_color = (255, 255, 255)    # Trắng
        border_color = (150, 150, 150)  # Xám sáng hơn
        
        # Vị trí góc trái
        start_x = 10
        start_y = 10
        
        # Thông tin sinh viên
        student1_name = "Nguyễn Vũ Bảo"
        student1_mssv = "MSSV: 23110079"
        student2_name = "Trần Hoàng Phúc Quân"
        student2_mssv = "MSSV: 23110146"
        
        # Vẽ background cho banner
        banner_rect = pygame.Rect(start_x - 5, start_y - 5, 250, 95)
        pygame.draw.rect(self.surface, (0, 0, 0, 180), banner_rect)  # Nền đen trong suốt
        pygame.draw.rect(self.surface, border_color, banner_rect, 2)  # Viền
        
        # Vẽ text
        texts = [
            (student1_name, name_color, start_x, start_y),
            (student1_mssv, mssv_color, start_x, start_y + 20),
            (student2_name, name_color, start_x, start_y + 50),
            (student2_mssv, mssv_color, start_x, start_y + 70)
        ]
        
        for text, color, x, y in texts:
            text_surface = font.render(text, True, color)
            self.surface.blit(text_surface, (x, y))
