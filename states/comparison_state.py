# =============================================================================
# COMPARISON_STATE.PY - STATE SO SÁNH AI VÀ NGƯỜI CHƠI
# =============================================================================
# File này chứa ComparisonState - state để so sánh AI và người chơi
# Có 2 màn hình game song song: AI bên trái, Player bên phải
# Control panel ở phía dưới để điều khiển cả 2 game

import sys
import math
import pygame
import time
from pathlib import Path

from statemachine import State
from ui.button import PacManButton
from ui.neontext import NeonText
from ui.constants import *
from states.menu_state import MenuState
from states.comparison_layout import ComparisonLayout
from engine.game import Game

class ComparisonState(State):
    """
    ComparisonState - State so sánh AI và người chơi
    - Quản lý 2 game instances: AI game và Player game
    - Layout với 2 màn hình song song và control panel ở dưới
    - Đồng bộ hóa trạng thái giữa 2 game
    - Hiển thị thống kê so sánh
    """
    HOME = 'home'
    OPTIONS = 'option'

    def __init__(self, app, machine, algorithm="BFS"):
        """
        Khởi tạo ComparisonState
        Args:
            app: Tham chiếu đến App chính
            machine: StateMachine quản lý states
            algorithm: Thuật toán AI sử dụng (BFS, DFS, A*, UCS, IDS)
        """
        super().__init__(app, machine)  
        self.algorithm = algorithm  # Thuật toán AI được chọn
        self.is_pause = False  # Trạng thái pause cho cả 2 game
        self.game_running = True  # Game có đang chạy không
        
        # Khởi tạo UI layout và 2 game engines
        self.layout = ComparisonLayout(app)  # Layout UI cho comparison
        self.ai_game = Game(algorithm, app.config)  # Game engine cho AI với config
        self.player_game = Game("BFS", app.config)  # Game engine cho người chơi với config
        
        # Khởi tạo cả 2 game nếu có method initialize_game
        if hasattr(self.ai_game, 'initialize_game'):
            self.ai_game.initialize_game()
        if hasattr(self.player_game, 'initialize_game'):
            self.player_game.initialize_game()
        
        # Đảm bảo AI game chạy ở AI mode và Player game chạy ở Player mode
        self.ai_game.set_ai_mode(True)      # AI game chạy AI mode
        self.player_game.set_ai_mode(False) # Player game chạy Player mode
        
        # Set đúng algorithm mode cho AI game
        self._set_ai_algorithm_mode(self.algorithm)
        
        # Lấy thông tin game ban đầu cho AI
        self.ai_score = getattr(self.ai_game, 'score', 0)
        self.ai_lives = getattr(self.ai_game, 'lives', 5)
        self.ai_level = getattr(self.ai_game, 'level', 0)
        
        # Lấy thông tin game ban đầu cho Player
        self.player_score = getattr(self.player_game, 'score', 0)
        self.player_lives = getattr(self.player_game, 'lives', 5)
        self.player_level = getattr(self.player_game, 'level', 0)

        # Cập nhật thông tin lên layout
        self.layout.set_game_info(
            self.ai_score, self.ai_lives, self.ai_level,
            self.player_score, self.player_lives, self.player_level,
            self.algorithm
        )
        
        # Khởi tạo win notification
        self.win_notification = None
        
        # Hiệu ứng visual cho game over/win
        self.game_over_effect = None
        self.win_effect = None
        self.effect_timer = 0
        self.effect_duration = 3.0  # 3 giây hiệu ứng
        
    def _render_scaled_game(self, game_surface, game_rect, game_instance):
        """
        Render game content với scaling phù hợp để giữ tỷ lệ khung hình
        - Tính toán scale factor để fit vào game area
        - Giữ nguyên aspect ratio của game gốc
        - Render game lên surface tạm rồi scale xuống
        
        Args:
            game_surface: Surface để vẽ game đã scale
            game_rect: Rectangle của khu vực game
            game_instance: Game instance cần render (AI hoặc Player)
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
        game_instance.render(temp_surface)
        
        # Scale surface tạm để fit vào game area với smooth scaling
        scaled_surface = pygame.transform.smoothscale(temp_surface, (scaled_width, scaled_height))
        
        # Căn giữa game đã scale trong game area
        x_offset = (game_rect.width - scaled_width) // 2
        y_offset = (game_rect.height - scaled_height) // 2
        
        # Xóa game surface trước
        game_surface.fill((0, 0, 0, 0))
        
        # Vẽ game đã scale lên game surface
        game_surface.blit(scaled_surface, (x_offset, y_offset))
        
    def draw(self, _screen=None):
        """
        Vẽ ComparisonState lên màn hình
        - Render UI layout trước
        - Render cả 2 game với scaling phù hợp
        - Không sử dụng _screen parameter để thống nhất
        """
        # Render UI layout (control panel, buttons, v.v.)
        self.layout.render()
        
        # Render AI game lên subsurface của khu vực AI game
        ai_game_rect = self.layout.get_ai_game_area_rect()
        ai_game_surface = self.layout.surface.subsurface(ai_game_rect)
        self._render_scaled_game(ai_game_surface, ai_game_rect, self.ai_game)
        
        # Render Player game lên subsurface của khu vực Player game
        player_game_rect = self.layout.get_player_game_area_rect()
        player_game_surface = self.layout.surface.subsurface(player_game_rect)
        self._render_scaled_game(player_game_surface, player_game_rect, self.player_game)
        
        # Render win notification nếu có
        if self.win_notification:
            self._render_win_notification()
        
        # Render visual effects
        self._render_visual_effects()
    
    def _render_win_notification(self):
        """
        Render thông báo thắng cuộc lên màn hình
        """
        if not self.win_notification:
            return
        
        # Kiểm tra thời gian hiển thị
        current_time = time.time()
        elapsed_time = current_time - self.win_notification['start_time']
        
        if elapsed_time >= self.win_notification['show_time']:
            self.win_notification = None
            return
        
        # Tạo overlay mờ
        overlay = pygame.Surface((self.app.WIDTH, self.app.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Nền đen trong suốt
        self.layout.surface.blit(overlay, (0, 0))
        
        # Font cho notification
        try:
            title_font = pygame.font.Font(FONT_PATH, 48)
            message_font = pygame.font.Font(FONT_PATH, 24)
        except:
            title_font = pygame.font.Font(None, 48)
            message_font = pygame.font.Font(None, 24)
        
        # Render title
        title_text = title_font.render(self.win_notification['title'], True, PAC_YELLOW)
        title_rect = title_text.get_rect(center=(self.app.WIDTH // 2, self.app.HEIGHT // 2 - 50))
        
        # Render message
        message_text = message_font.render(self.win_notification['message'], True, DOT_WHITE)
        message_rect = message_text.get_rect(center=(self.app.WIDTH // 2, self.app.HEIGHT // 2 + 20))
        
        # Vẽ background cho notification
        notification_rect = pygame.Rect(
            title_rect.x - 20, title_rect.y - 20,
            max(title_rect.width, message_rect.width) + 40,
            title_rect.height + message_rect.height + 60
        )
        pygame.draw.rect(self.layout.surface, (50, 50, 80), notification_rect)
        pygame.draw.rect(self.layout.surface, PAC_YELLOW, notification_rect, 4)
        
        # Vẽ text
        self.layout.surface.blit(title_text, title_rect)
        self.layout.surface.blit(message_text, message_rect)
    
    def _render_visual_effects(self):
        """
        Render các hiệu ứng visual (win/game over effects)
        """
        current_time = time.time()
        
        # Render win effect
        if self.win_effect and current_time - self.win_effect['start_time'] < self.win_effect['duration']:
            self._render_particle_effect(self.win_effect, current_time)
        
        # Render game over effect
        if self.game_over_effect and current_time - self.game_over_effect['start_time'] < self.game_over_effect['duration']:
            self._render_particle_effect(self.game_over_effect, current_time)
    
    def _render_particle_effect(self, effect, current_time):
        """
        Render particle effect
        """
        dt = current_time - effect['start_time']
        
        for particle in effect['particles']:
            # Cập nhật vị trí particle
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            
            # Cập nhật life
            particle['life'] -= dt
            
            if particle['life'] > 0:
                # Tính alpha dựa trên life
                alpha = int(255 * (particle['life'] / particle['max_life']))
                alpha = max(0, min(255, alpha))
                
                # Vẽ particle
                color = (*particle['color'][:3], alpha)
                size = int(3 * (particle['life'] / particle['max_life']))
                size = max(1, size)
                
                # Vẽ circle với alpha
                if size > 0:
                    pygame.draw.circle(self.layout.surface, particle['color'], 
                                     (int(particle['x']), int(particle['y'])), size)
        
    def logic(self):
        """
        Cập nhật logic của ComparisonState mỗi frame
        - Cập nhật layout animations
        - Đồng bộ trạng thái play/pause cho cả 2 game
        - Cập nhật cả 2 game engines nếu không pause
        - Kiểm tra game over cho cả 2 game
        """
        # Luôn cập nhật layout animations
        self.layout.update()
        
        # Đồng bộ trạng thái play giữa layout và game state
        self.layout.is_playing = not self.is_pause
        
        if not self.is_pause and self.game_running:
            # Cập nhật AI game engine nếu có
            if hasattr(self.ai_game, 'update'):
                self.ai_game.update()
            
            # Cập nhật Player game engine nếu có
            if hasattr(self.player_game, 'update'):
                self.player_game.update()
            
            # Cập nhật giá trị game từ AI game engine thực tế
            self.ai_score = getattr(self.ai_game, 'score', self.ai_score)
            self.ai_lives = getattr(self.ai_game, 'lives', self.ai_lives)
            self.ai_level = getattr(self.ai_game, 'level', self.ai_level)
            
            # Cập nhật giá trị game từ Player game engine thực tế
            self.player_score = getattr(self.player_game, 'score', self.player_score)
            self.player_lives = getattr(self.player_game, 'lives', self.player_lives)
            self.player_level = getattr(self.player_game, 'level', self.player_level)
            
            # Cập nhật layout với giá trị game hiện tại
            self.layout.set_game_info(
                self.ai_score, self.ai_lives, self.ai_level,
                self.player_score, self.player_lives, self.player_level,
                self.algorithm
            )
        else:
            # Ngay cả khi pause, vẫn cập nhật layout với giá trị hiện tại
            self.layout.set_game_info(
                self.ai_score, self.ai_lives, self.ai_level,
                self.player_score, self.player_lives, self.player_level,
                self.algorithm
            )

        # Kiểm tra game over cho cả 2 game
        if self.ai_lives <= 0 or self.player_lives <= 0:
            self.game_over()
        
        # Kiểm tra điều kiện thắng cho comparison mode
        self.check_win_conditions()
    
    def handle_events(self, event):
        """
        Xử lý sự kiện input cho ComparisonState
        - Xử lý click play/pause button
        - Xử lý thay đổi algorithm
        - Xử lý keyboard shortcuts
        - Chuyển tiếp events cho cả 2 game engines
        
        Args:
            event: Pygame event cần xử lý
        """
        # Xử lý click play button trước
        if self.layout.handle_play_button_click(event):
            # Phát âm thanh khi click play/pause
            self.app.sound_system.play_sound('button_click')
            # Trạng thái play đã thay đổi, cập nhật game pause state
            self.is_pause = not self.layout.is_playing
            if hasattr(self.ai_game, 'pause'):
                if self.layout.is_playing:
                    self.ai_game.pause.setPause(pauseTime=0)  # Resume AI game
                else:
                    self.ai_game.pause.setPause(playerPaused=True)  # Pause AI game
            if hasattr(self.player_game, 'pause'):
                if self.layout.is_playing:
                    self.player_game.pause.setPause(pauseTime=0)  # Resume Player game
                else:
                    self.player_game.pause.setPause(playerPaused=True)  # Pause Player game
        
        # Xử lý sự kiện selectbox (thay đổi algorithm)
        if self.layout.handle_selectbox_event(event):
            # Phát âm thanh khi thay đổi algorithm
            self.app.sound_system.play_sound('button_click')
            # Algorithm đã thay đổi, cập nhật AI game
            self.algorithm = self.layout.algorithm
            self.ai_game = Game(self.algorithm, self.app.config)  # Tạo AI game mới với algorithm mới và config
            if hasattr(self.ai_game, 'initialize_game'):
                self.ai_game.initialize_game()
            # Đảm bảo AI game chạy ở AI mode
            self.ai_game.set_ai_mode(True)
            # Load heuristic từ config
            if hasattr(self.ai_game, 'load_heuristic_from_config'):
                self.ai_game.load_heuristic_from_config(self.app.config)
            
            # Set đúng algorithm mode cho thuật toán mới
            self._set_ai_algorithm_mode(self.algorithm)
            
            # Reset giá trị AI game khi thay đổi algorithm
            self.ai_score = getattr(self.ai_game, 'score', 0)
            self.ai_lives = getattr(self.ai_game, 'lives', 5)
            self.ai_level = getattr(self.ai_game, 'level', 0)
            self.layout.set_game_info(
                self.ai_score, self.ai_lives, self.ai_level,
                self.player_score, self.player_lives, self.player_level,
                self.algorithm
            )
        
        # Xử lý sự kiện heuristic selectbox (thay đổi heuristic)
        if self.layout.handle_heuristic_selectbox_event(event):
            # Phát âm thanh khi thay đổi heuristic
            self.app.sound_system.play_sound('button_click')
            # Heuristic đã thay đổi, cập nhật config và AI game
            self._update_heuristic_config()
            # Restart AI game với heuristic mới
            self._restart_ai_game_with_new_heuristic()
            # Reset trạng thái play khi thay đổi algorithm
            self.layout.is_playing = False
            self.is_pause = True
        
        # Chuyển tiếp events cho AI game engine
        if hasattr(self.ai_game, 'handle_event'):
            self.ai_game.handle_event(event)
        
        # Chuyển tiếp events cho Player game engine
        if hasattr(self.player_game, 'handle_event'):
            self.player_game.handle_event(event)
        
        # Xử lý keyboard events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.app.sound_system.play_sound('button_click')
                self.toggle_pause()  # Toggle pause với SPACE
            elif event.key == pygame.K_ESCAPE:
                self.return_to_menu()

            elif event.key == pygame.K_r:
                self.app.sound_system.play_sound('button_click')
                self.restart_game()  # Restart với R
    
    def toggle_pause(self):
        """
        Chuyển đổi trạng thái pause cho cả 2 game
        - Toggle giữa pause và resume
        """
        self.is_pause = not self.is_pause
    
    def pause_game(self):
        """
        Pause cả 2 game
        - Đặt trạng thái pause = True
        """
        self.is_pause = True
    
    def restart_game(self):
        """
        Restart cả 2 game
        - Tạo game engines mới
        - Reset tất cả giá trị về ban đầu
        - Bắt đầu ở trạng thái pause
        """
        # Restart AI game với algorithm hiện tại
        self.ai_game = Game(self.algorithm, self.app.config)
        if hasattr(self.ai_game, 'initialize_game'):
            self.ai_game.initialize_game()
        
        # Restart Player game
        self.player_game = Game("BFS", self.app.config)
        if hasattr(self.player_game, 'initialize_game'):
            self.player_game.initialize_game()
        
        # Đảm bảo AI game chạy ở AI mode và Player game chạy ở Player mode
        self.ai_game.set_ai_mode(True)      # AI game chạy AI mode
        self.player_game.set_ai_mode(False) # Player game chạy Player mode
        
        # Set đúng algorithm cho AI game dựa trên thuật toán được chọn
        self._set_ai_algorithm_mode(self.algorithm)
        
        # Reset tất cả giá trị game về ban đầu
        self.ai_score = getattr(self.ai_game, 'score', 0)
        self.ai_lives = getattr(self.ai_game, 'lives', 5)
        self.ai_level = getattr(self.ai_game, 'level', 0)
        
        self.player_score = getattr(self.player_game, 'score', 0)
        self.player_lives = getattr(self.player_game, 'lives', 5)
        self.player_level = getattr(self.player_game, 'level', 0)
        
        self.game_running = True
        self.is_pause = True  # Bắt đầu ở trạng thái pause
        self.layout.is_playing = False  # Reset trạng thái play
        self.layout.set_game_info(
            self.ai_score, self.ai_lives, self.ai_level,
            self.player_score, self.player_lives, self.player_level,
            self.algorithm
        )
    def return_to_menu(self):
        """Quay trở lại menu chính và dừng cả hai game."""
        self.game_running = False
        self.is_pause = False
        self.layout.is_playing = True
        self.win_notification = None

        for game_instance in (self.ai_game, self.player_game):
            if hasattr(game_instance, 'pause'):
                game_instance.pause.setPause(playerPaused=True)
            if hasattr(game_instance, 'running'):
                game_instance.running = False
            if hasattr(game_instance, 'stop_timer'):
                game_instance.stop_timer()

        if hasattr(self.app, 'sound_system'):
            self.app.sound_system.stop_music()

        self.replace_state(MenuState(self.app, self.machine))
    def check_win_conditions(self):
        """
        Kiểm tra điều kiện thắng trong comparison mode
        - AI thắng: AI hoàn thành level trước hoặc có điểm cao hơn khi game kết thúc
        - Human thắng: Human hoàn thành level trước hoặc có điểm cao hơn khi game kết thúc
        """
        # Kiểm tra nếu một trong hai bên đã thắng (hoàn thành level)
        ai_won = hasattr(self.ai_game, 'level_complete') and getattr(self.ai_game, 'level_complete', False)
        player_won = hasattr(self.player_game, 'level_complete') and getattr(self.player_game, 'level_complete', False)
        
        if ai_won and not player_won:
            self.show_win_notification("AI WINS!", "AI completed the level first!")
            self.game_running = False
        elif player_won and not ai_won:
            self.show_win_notification("HUMAN WINS!", "Human player completed the level first!")
            self.game_running = False
        elif ai_won and player_won:
            # Cả hai cùng hoàn thành, so sánh điểm
            if self.ai_score > self.player_score:
                self.show_win_notification("AI WINS!", f"AI scored higher: {self.ai_score} vs {self.player_score}")
            elif self.player_score > self.ai_score:
                self.show_win_notification("HUMAN WINS!", f"Human scored higher: {self.player_score} vs {self.ai_score}")
            else:
                self.show_win_notification("TIE!", "Both players scored the same!")
            self.game_running = False
    
    def show_win_notification(self, title, message):
        """
        Hiển thị thông báo thắng cuộc
        Args:
            title: Tiêu đề thông báo
            message: Nội dung thông báo
        """
        # Phát âm thanh thắng cuộc
        if hasattr(self.app, 'sound_system'):
            self.app.sound_system.play_sound('level_complete')
        
        # Lưu thông báo để hiển thị
        self.win_notification = {
            'title': title,
            'message': message,
            'show_time': 5.0,  # Hiển thị trong 5 giây
            'start_time': time.time()
        }
        
        # Tạo hiệu ứng win
        self._create_win_effect()
    
    def _create_win_effect(self):
        """
        Tạo hiệu ứng visual khi thắng game
        """
        self.win_effect = {
            'type': 'win',
            'start_time': time.time(),
            'duration': self.effect_duration,
            'particles': []
        }
        
        # Tạo particles cho hiệu ứng
        import random
        for i in range(50):
            particle = {
                'x': random.randint(0, self.app.WIDTH),
                'y': random.randint(0, self.app.HEIGHT),
                'vx': random.uniform(-200, 200),
                'vy': random.uniform(-200, 200),
                'life': random.uniform(0.5, 2.0),
                'max_life': random.uniform(0.5, 2.0),
                'color': random.choice([(255, 255, 0), (255, 165, 0), (255, 255, 255), (0, 255, 0)])
            }
            self.win_effect['particles'].append(particle)
    
    def _create_game_over_effect(self):
        """
        Tạo hiệu ứng visual khi game over
        """
        self.game_over_effect = {
            'type': 'game_over',
            'start_time': time.time(),
            'duration': self.effect_duration,
            'particles': []
        }
        
        # Tạo particles cho hiệu ứng
        import random
        for i in range(30):
            particle = {
                'x': random.randint(0, self.app.WIDTH),
                'y': random.randint(0, self.app.HEIGHT),
                'vx': random.uniform(-100, 100),
                'vy': random.uniform(-100, 100),
                'life': random.uniform(1.0, 3.0),
                'max_life': random.uniform(1.0, 3.0),
                'color': random.choice([(255, 0, 0), (255, 100, 100), (255, 255, 255), (200, 0, 0)])
            }
            self.game_over_effect['particles'].append(particle)
    
    def _set_ai_algorithm_mode(self, algorithm):
        """
        Set đúng mode cho AI algorithm trong comparison mode
        Args:
            algorithm: Tên thuật toán được chọn
        """
        # Các thuật toán offline sử dụng compute_once_system
        offline_algorithms = ['BFS', 'DFS', 'A*', 'UCS', 'IDS', 'Greedy']
        
        # Các thuật toán online sử dụng hybrid_ai_system
        online_algorithms = ['Minimax', 'Alpha-Beta', 'Hill Climbing', 'Genetic Algorithm', 'GBFS', 'A* Online']
        
        if algorithm in offline_algorithms:
            # Set offline mode cho các thuật toán offline
            if hasattr(self.ai_game, 'pacman') and self.ai_game.pacman:
                self.ai_game.pacman.disable_hybrid_ai()
                # Set algorithm với heuristic
                if hasattr(self.ai_game, 'set_algorithm'):
                    self.ai_game.set_algorithm(algorithm)
        elif algorithm in online_algorithms:
            # Set online mode cho các thuật toán online
            if hasattr(self.ai_game, 'pacman') and self.ai_game.pacman:
                self.ai_game.pacman.enable_hybrid_ai()
            # Set algorithm
            if hasattr(self.ai_game, 'set_algorithm'):
                self.ai_game.set_algorithm(algorithm)
    
    def _update_heuristic_config(self):
        """
        Cập nhật config với heuristic mới được chọn
        """
        heuristic_name = self.layout.current_heuristic.upper()
        # Cập nhật config sử dụng method set
        if hasattr(self.app, 'config') and self.app.config:
            if hasattr(self.app.config, 'set'):
                self.app.config.set("algorithm_heuristic", heuristic_name)
            else:
                # Fallback nếu config là dict
                self.app.config["algorithm_heuristic"] = heuristic_name
        
        # Cập nhật AI game config
        if hasattr(self.ai_game, 'config') and self.ai_game.config:
            if hasattr(self.ai_game.config, 'set'):
                self.ai_game.config.set("algorithm_heuristic", heuristic_name)
            else:
                # Fallback nếu config là dict
                self.ai_game.config["algorithm_heuristic"] = heuristic_name
        
        # Cập nhật compute_once config
        from engine.compute_once_system import compute_once
        if hasattr(compute_once, 'config'):
            compute_once.config = self.app.config
    
    def _restart_ai_game_with_new_heuristic(self):
        """
        Restart AI game với heuristic mới
        """
        # Lưu trạng thái hiện tại
        current_score = getattr(self.ai_game, 'score', 0)
        current_lives = getattr(self.ai_game, 'lives', 5)
        current_level = getattr(self.ai_game, 'level', 0)
        
        # Tạo AI game mới với heuristic mới
        self.ai_game = Game(self.algorithm, self.app.config)
        if hasattr(self.ai_game, 'initialize_game'):
            self.ai_game.initialize_game()
        
        # Đảm bảo AI game chạy ở AI mode
        self.ai_game.set_ai_mode(True)
        
        # Load heuristic từ config
        if hasattr(self.ai_game, 'load_heuristic_from_config'):
            self.ai_game.load_heuristic_from_config(self.app.config)
        
        # Set đúng algorithm mode
        self._set_ai_algorithm_mode(self.algorithm)
        
        # Restore trạng thái game
        self.ai_score = current_score
        self.ai_lives = current_lives
        self.ai_level = current_level
        
        # Cập nhật layout
        self.layout.set_game_info(
            self.ai_score, self.ai_lives, self.ai_level,
            self.player_score, self.player_lives, self.player_level,
            self.algorithm
        )
    
    def game_over(self):
        """
        Xử lý game over cho cả 2 game
        - Đặt game_running = False
        - Hiển thị thông báo game over
        - Phát âm thanh game over
        - Tạo hiệu ứng visual
        """
        self.game_running = False
        
        # Phát âm thanh game over
        if hasattr(self.app, 'sound_system'):
            self.app.sound_system.play_sound('game_over')
        
        # Tạo hiệu ứng game over
        self._create_game_over_effect()
        
        # Hiển thị thông báo game over
        self.show_win_notification("GAME OVER!", "Both players have lost!")
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
        - Hiện tại không có logic đặc biệt
        """
        pass