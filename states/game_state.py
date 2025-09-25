# =============================================================================
# GAME_STATE.PY - STATE CHÍNH CỦA GAME PAC-MAN
# =============================================================================
# File này chứa GameState - state chính khi chơi game
# Quản lý game logic, UI layout, và tương tác người dùng

import sys
import math
import pygame
from pathlib import Path

from statemachine import State
from ui.button import PacManButton
from ui.neontext import NeonText
from ui.constants import *
from states.gamelayout import GameLayout
from engine.game import Game

class GameState(State):
    """
    GameState - State chính khi chơi game Pac-Man
    - Quản lý game engine và UI layout
    - Xử lý pause/resume, restart, algorithm switching
    - Render game với scaling phù hợp
    - Đồng bộ hóa giữa game logic và UI
    """
    HOME = 'home'
    OPTIONS = 'option'

    def __init__(self, app, machine, algorithm="BFS"):
        """
        Khởi tạo GameState
        Args:
            app: Tham chiếu đến App chính
            machine: StateMachine quản lý states
            algorithm: Thuật toán AI sử dụng (BFS, DFS, A*, UCS, IDS)
        """
        super().__init__(app, machine)  
        self.algorithm = algorithm  # Thuật toán AI được chọn
        self.is_pause = False  # Trạng thái pause
        self.game_running = True  # Game có đang chạy không
        
        # Khởi tạo UI layout và game engine
        self.layout = GameLayout(app)  # Layout UI cho game
        self.game = Game(algorithm)  # Game engine chính
        
        # Khởi tạo game nếu có method initialize_game
        if hasattr(self.game, 'initialize_game'):
            self.game.initialize_game()
        
        # Lấy thông tin game ban đầu
        self.score = getattr(self.game, 'score', 0)  # Điểm số
        self.lives = getattr(self.game, 'lives', 5)  # Số mạng (bắt đầu với 5)
        self.level = getattr(self.game, 'level', 0)  # Level hiện tại (bắt đầu với 0)

        # Cập nhật thông tin lên layout
        self.layout.set_game_info(self.score, self.lives, self.level, self.algorithm)
        
        # Khởi tạo mode mặc định
        self.game.set_ai_mode(True)  # Bắt đầu với AI mode
        
    def _render_scaled_game(self, game_surface, game_rect):
        """
        Render game content với scaling phù hợp để giữ tỷ lệ khung hình
        - Tính toán scale factor để fit vào game area
        - Giữ nguyên aspect ratio của game gốc
        - Render game lên surface tạm rồi scale xuống
        
        Args:
            game_surface: Surface để vẽ game đã scale
            game_rect: Rectangle của khu vực game
        """
        # Lấy kích thước game gốc từ constants
        from constants import SCREENSIZE
        original_width, original_height = SCREENSIZE
        
        # Tính toán scale factors để giữ aspect ratio
        scale_x = game_rect.width / original_width
        scale_y = game_rect.height / original_height
        
        # Sử dụng scale nhỏ hơn để giữ aspect ratio và fit đúng
        scale = min(scale_x, scale_y)
        
        # Tính toán kích thước sau khi scale
        scaled_width = int(original_width * scale)
        scaled_height = int(original_height * scale)
        
        # Tạo surface tạm để render game ở kích thước gốc
        temp_surface = pygame.Surface((original_width, original_height))
        
        # Vẽ background rất nhẹ
        for y in range(original_height):
            intensity = int(2 + (y / original_height) * 3)  # Rất nhẹ
            color = (intensity, intensity + 2, intensity + 8)
            pygame.draw.line(temp_surface, color, (0, y), (original_width, y))
        
        # Render game lên surface tạm ở kích thước gốc
        self.game.render(temp_surface)
        
        # Scale surface tạm để fit vào game area với smooth scaling
        scaled_surface = pygame.transform.smoothscale(temp_surface, (scaled_width, scaled_height))
        
        # Căn giữa game đã scale trong game area
        x_offset = (game_rect.width - scaled_width) // 2
        y_offset = (game_rect.height - scaled_height) // 2
        
        game_surface.fill((0, 0, 0, 0))
        
        # Vẽ game đã scale lên game surface
        game_surface.blit(scaled_surface, (x_offset, y_offset))
        
    def draw(self, _screen=None):
        """
        Vẽ GameState lên màn hình
        - Render UI layout trước
        - Render game với scaling phù hợp
        - Không sử dụng _screen parameter để thống nhất
        """
        # Render UI layout (control panel, buttons, v.v.)
        self.layout.render()
        
        # Render game lên subsurface của khu vực game
        game_rect = self.layout.get_game_area_rect()
        game_surface = self.layout.surface.subsurface(game_rect)
        
        # Scale game content để fit vào game area đúng cách
        self._render_scaled_game(game_surface, game_rect)
        
    def logic(self):
        """
        Cập nhật logic của GameState mỗi frame
        - Cập nhật layout animations
        - Đồng bộ trạng thái play/pause
        - Cập nhật game engine nếu không pause
        - Kiểm tra game over
        - Xử lý âm thanh
        """
        # Luôn cập nhật layout animations
        self.layout.update()
        
        # Đồng bộ trạng thái play giữa layout và game state
        self.layout.is_playing = not self.is_pause
        
        if not self.is_pause and self.game_running:
            # Lưu score cũ để phát hiện thay đổi
            old_score = self.score
            
            # Cập nhật game engine nếu có
            if hasattr(self.game, 'update'):
                self.game.update()
            
            # Cập nhật giá trị game từ game engine thực tế
            self.score = getattr(self.game, 'score', self.score)
            self.lives = getattr(self.game, 'lives', self.lives)
            self.level = getattr(self.game, 'level', self.level)
            
            # Phát âm thanh khi score thay đổi (ăn pellet)
            if self.score > old_score:
                score_diff = self.score - old_score
                if score_diff == 10:  # Ăn pellet thường
                    self.app.sound_system.play_sound('pellet')
                elif score_diff == 50:  # Ăn power pellet
                    self.app.sound_system.play_sound('power_pellet')
                elif score_diff >= 100:  # Ăn fruit
                    self.app.sound_system.play_sound('fruit')
            
            # Kiểm tra game over hoặc level complete
            if hasattr(self.game, 'game_over') and self.game.game_over:
                self.app.sound_system.play_sound('game_over')
                self.app.sound_system.stop_music()
            elif hasattr(self.game, 'level_complete') and self.game.level_complete:
                self.app.sound_system.play_sound('level_complete')
            
            # Cập nhật layout với giá trị game hiện tại
            self.layout.set_game_info(self.score, self.lives, self.level, self.algorithm)
        else:
            # Ngay cả khi pause, vẫn cập nhật layout với giá trị hiện tại
            self.layout.set_game_info(self.score, self.lives, self.level, self.algorithm)

        # Kiểm tra game over
        if self.lives <= 0:
            self.game_over()
    
    def handle_events(self, event):
        """
        Xử lý sự kiện input cho GameState
        - Xử lý click play/pause button
        - Xử lý thay đổi algorithm
        - Xử lý keyboard shortcuts
        - Chuyển tiếp events cho game engine
        
        Args:
            event: Pygame event cần xử lý
        """
        # Xử lý click play button trước
        if self.layout.handle_play_button_click(event):
            # Trạng thái play đã thay đổi, cập nhật game pause state
            self.is_pause = not self.layout.is_playing
            if hasattr(self.game, 'pause'):
                if self.layout.is_playing:
                    self.game.pause.setPause(pauseTime=0)  # Resume game
                else:
                    self.game.pause.setPause(playerPaused=True)  # Pause game
        
        # Xử lý sự kiện selectbox (thay đổi algorithm)
        if self.layout.handle_selectbox_event(event):
            # Phát âm thanh khi thay đổi algorithm
            self.app.sound_system.play_sound('button_click')
            # Algorithm đã thay đổi, cập nhật game
            self.algorithm = self.layout.algorithm
            # Chỉ thay đổi algorithm, không tạo game mới
            self.game.set_algorithm(self.algorithm)
            # Cập nhật thông tin lên layout
            self.layout.set_game_info(self.score, self.lives, self.level, self.algorithm)
        
        # Chuyển tiếp events cho game engine
        if hasattr(self.game, 'handle_event'):
            self.game.handle_event(event)
        
        # Xử lý keyboard events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.toggle_pause()  # Toggle pause với SPACE
            elif event.key == pygame.K_ESCAPE:
                self.pause_game()  # Pause với ESC
            elif event.key == pygame.K_r:
                self.restart_game()  # Restart với R
            elif event.key == pygame.K_m:
                # Chỉ cho phép toggle mode khi ở AI mode
                if hasattr(self.game, 'ai_mode') and self.game.ai_mode:
                    self.toggle_ai_mode()  # Toggle AI/Player mode với M
    def toggle_pause(self):
        """
        Chuyển đổi trạng thái pause
        - Toggle giữa pause và resume
        """
        self.is_pause = not self.is_pause
    
    def pause_game(self):
        """
        Pause game
        - Đặt trạng thái pause = True
        """
        self.is_pause = True
    
    def restart_game(self):
        """
        Restart game với algorithm hiện tại
        - Tạo game engine mới
        - Reset tất cả giá trị về ban đầu
        - Bắt đầu ở trạng thái pause
        """
        self.game = Game(self.algorithm)  # Tạo game mới với algorithm hiện tại
        if hasattr(self.game, 'initialize_game'):
            self.game.initialize_game()
        # Reset tất cả giá trị game về ban đầu
        self.score = getattr(self.game, 'score', 0)
        self.lives = getattr(self.game, 'lives', 5)  # Game bắt đầu với 5 mạng
        self.level = getattr(self.game, 'level', 0)  # Game bắt đầu với level 0
        self.game_running = True
        self.is_pause = True  # Bắt đầu ở trạng thái pause
        self.layout.is_playing = False  # Reset trạng thái play
        self.layout.set_game_info(self.score, self.lives, self.level, self.algorithm)
    
    def game_over(self):
        """
        Xử lý game over
        - Đặt game_running = False
        - Có thể thêm logic game over ở đây
        """
        self.game_running = False
        # Có thể thêm logic game over ở đây
    
    def on_resume(self):
        """
        Được gọi khi state được resume
        - Hiện tại không có logic đặc biệt
        """
        pass
    
    def on_exit(self):
        """
        Được gọi khi state bị exit
        """
        pass
    
    def on_settings_changed(self, settings):
        """
        Được gọi khi settings thay đổi
        """
        # Cập nhật volume cho game state
        if hasattr(self.app, 'sfx_volume'):
            self.app.sfx_volume = settings.get('sfx_volume', 0.8)
        
        # Cập nhật music volume nếu có
        if 'music_volume' in settings:
            pygame.mixer.music.set_volume(settings['music_volume'])
        
        # Cập nhật fullscreen nếu cần
        if 'fullscreen' in settings and settings['fullscreen']:
            self.app.screen = pygame.display.set_mode((self.app.WIDTH, self.app.HEIGHT), pygame.FULLSCREEN)
        else:
            self.app.screen = pygame.display.set_mode((self.app.WIDTH, self.app.HEIGHT))
    
    def toggle_ai_mode(self):
        """
        Chuyển đổi giữa AI mode và Player mode
        - Toggle giữa AI tự động và điều khiển thủ công
        """
        if hasattr(self.game, 'ai_mode'):
            self.game.set_ai_mode(not self.game.ai_mode)
            # Cập nhật thông tin hiển thị
            mode_text = "AI" if self.game.ai_mode else "Player"
            print(f"Switched to {mode_text} mode")
        
        print("Game state: Settings updated")

