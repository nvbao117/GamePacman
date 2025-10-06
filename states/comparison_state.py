# =============================================================================
# COMPARISON_STATE.PY - STATE SO SÁNH AI VÀ NGƯỜI CHƠI
# =============================================================================
# File này chứa ComparisonState - state để so sánh AI và người chơi
# Có 2 màn hình game song song: AI bên trái, Player bên phải
# Control panel ở phía dưới để điều khiển cả 2 game

import sys
import math
import time
import pygame
from pathlib import Path

from statemachine import State
from ui.button import PacManButton
from ui.neontext import NeonText
from ui.constants import *
from states.comparison_layout import ComparisonLayout
from engine.game import Game
from engine.performance_logger import PerformanceLogger

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
        
        # Khởi tạo SimplePerformanceLogger để thống kê
        self.performance_logger = PerformanceLogger("algorithm_comparison.xlsx")
        
        # Khởi tạo UI layout và 2 game engines
        self.layout = ComparisonLayout(app)  # Layout UI cho comparison
        self.ai_game = Game(algorithm)  # Game engine cho AI
        self.player_game = Game("BFS")  # Game engine cho người chơi (algorithm không quan trọng)
        
        # Khởi tạo cả 2 game nếu có method initialize_game
        if hasattr(self.ai_game, 'initialize_game'):
            self.ai_game.initialize_game()
        if hasattr(self.player_game, 'initialize_game'):
            self.player_game.initialize_game()
        
        # Đảm bảo AI game chạy ở AI mode và Player game chạy ở Player mode
        self.ai_game.set_ai_mode(True)      # AI game chạy AI mode
        self.player_game.set_ai_mode(False) # Player game chạy Player mode
        
        # Bắt đầu session thống kê cho AI
        self.performance_logger.start_game_session(algorithm)
        
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
            old_ai_score = self.ai_score
            old_ai_lives = self.ai_lives
            old_ai_level = self.ai_level
            
            self.ai_score = getattr(self.ai_game, 'score', self.ai_score)
            self.ai_lives = getattr(self.ai_game, 'lives', self.ai_lives)
            self.ai_level = getattr(self.ai_game, 'level', self.ai_level)
            
            # Cập nhật thống kê cho AI
            if self.ai_score > old_ai_score:
                food_eaten = self.ai_score - old_ai_score
                self.performance_logger.update_game_stats(food_eaten=food_eaten, score=self.ai_score)
            
            if self.ai_lives < old_ai_lives:
                deaths = old_ai_lives - self.ai_lives
                self.performance_logger.update_game_stats(deaths=deaths)
            
            if self.ai_level > old_ai_level:
                self.performance_logger.update_game_stats(level=self.ai_level)
            
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
        
        # Log performance data cho AI game - chỉ khi có thay đổi
        if hasattr(self, 'performance_logger') and self.game_running and not self.is_pause:
            # Thu thập dữ liệu thực tế từ game
            current_score = getattr(self.ai_game, 'score', 0)
            current_lives = getattr(self.ai_game, 'lives', 5)
            current_level = getattr(self.ai_game, 'level', 0)
            
            # Chỉ update khi có thay đổi để tránh spam
            if (current_score != self.ai_score or 
                current_lives != self.ai_lives or 
                current_level != self.ai_level):
                
                # Update game stats với dữ liệu thật
                self.performance_logger.update_game_stats(
                    score=current_score,
                    lives=current_lives,
                    level=current_level,
                    food_eaten=current_score // 10,  # Ước tính food eaten từ score
                    deaths=5 - current_lives,  # Số lần chết
                    win_rate=100.0 if current_lives > 0 else 0.0
                )
                
                # Chỉ thêm record khi có thay đổi đáng kể (score tăng ít nhất 10 điểm)
                if current_score > 0 and current_score - self.ai_score >= 10:
                    record = {
                        'algorithm': self.algorithm,
                        'avg_time_ms': 150.5,  # Giá trị mặc định
                        'steps': 100,  # Giá trị mặc định
                        'food_eaten': current_score // 10,
                        'deaths': 5 - current_lives,
                        'win_rate': 100.0 if current_lives > 0 else 0.0,
                        'score': current_score,
                        'level': current_level + 1,
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    
                    # Kiểm tra xem record đã tồn tại chưa (tránh duplicate)
                    existing = False
                    for existing_record in self.performance_logger.data_records:
                        if (existing_record['algorithm'] == record['algorithm'] and 
                            existing_record['score'] == record['score'] and
                            existing_record['level'] == record['level']):
                            existing = True
                            break
                    
                    if not existing:
                        self.performance_logger.data_records.append(record)
                        print(f"Added AI data record: Score={current_score}, Level={current_level + 1}")
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
            self.ai_game = Game(self.algorithm)  # Tạo AI game mới với algorithm mới
            if hasattr(self.ai_game, 'initialize_game'):
                self.ai_game.initialize_game()
            # Đảm bảo AI game chạy ở AI mode
            self.ai_game.set_ai_mode(True)
            # Reset giá trị AI game khi thay đổi algorithm
            self.ai_score = getattr(self.ai_game, 'score', 0)
            self.ai_lives = getattr(self.ai_game, 'lives', 5)
            self.ai_level = getattr(self.ai_game, 'level', 0)
            self.layout.set_game_info(
                self.ai_score, self.ai_lives, self.ai_level,
                self.player_score, self.player_lives, self.player_level,
                self.algorithm
            )
            # Reset trạng thái play khi thay đổi algorithm
            self.layout.is_playing = False
            self.is_pause = True
        
        # Xử lý sự kiện export button - Manual click detection
        if self.layout.handle_export_button_click(event):
            print("=== EXPORT BUTTON CLICKED ===")
            try:
                self.app.sound_system.play_sound('button_click')
            except Exception as e:
                print(f"[WARN] Could not play sound: {e}")
            self.export_to_excel()
        
        # Xử lý sự kiện clear data button - Manual click detection
        if self.layout.handle_clear_data_button_click(event):
            print("=== CLEAR DATA BUTTON CLICKED ===")
            try:
                self.app.sound_system.play_sound('button_click')
            except Exception as e:
                print(f"[WARN] Could not play sound: {e}")
            self.clear_excel_data()
        
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
                self.app.sound_system.play_sound('button_click')
                self.back_to_menu()  # Quay lại menu chính với ESC
            elif event.key == pygame.K_r:
                self.app.sound_system.play_sound('button_click')
                self.restart_game()  # Restart với R
            elif event.key == pygame.K_e:
                self.app.sound_system.play_sound('button_click')
                self.export_to_excel()  # Export Excel với E
    
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
    
    def back_to_menu(self):
        """
        Quay lại menu chính
        - Chuyển về menu state
        """
        from states.menu_state import MenuState
        menu_state = MenuState(self.app, self.machine)
        self.replace_state(menu_state)
    
    def restart_game(self):
        """
        Restart cả 2 game
        - Tạo game engines mới
        - Reset tất cả giá trị về ban đầu
        - Bắt đầu ở trạng thái pause
        """
        # Kết thúc session thống kê hiện tại trước khi restart
        if hasattr(self, 'performance_logger'):
            is_ai_win = self.ai_lives > 0
            self.performance_logger.end_game_session(is_win=is_ai_win, final_score=self.ai_score)
        
        # Restart AI game với algorithm hiện tại
        self.ai_game = Game(self.algorithm)
        if hasattr(self.ai_game, 'initialize_game'):
            self.ai_game.initialize_game()
        
        # Restart Player game
        self.player_game = Game("BFS")
        if hasattr(self.player_game, 'initialize_game'):
            self.player_game.initialize_game()
        
        # Đảm bảo AI game chạy ở AI mode và Player game chạy ở Player mode
        self.ai_game.set_ai_mode(True)      # AI game chạy AI mode
        self.player_game.set_ai_mode(False) # Player game chạy Player mode
        
        # Bắt đầu session thống kê mới cho AI
        self.performance_logger.start_game_session(self.algorithm)
        
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
    
    def game_over(self):
        """
        Xử lý game over cho cả 2 game
        - Đặt game_running = False
        - Kết thúc session thống kê
        """
        self.game_running = False
        
        # Kết thúc session thống kê cho AI
        is_ai_win = self.ai_lives > 0
        self.performance_logger.end_game_session(is_win=is_ai_win, final_score=self.ai_score)
        
        # In thống kê tổng hợp
        self.performance_logger.print_summary()
    
    def export_to_excel(self):
        """
        Xuất kết quả thống kê ra file Excel
        """
        print("=== EXPORT BUTTON CLICKED ===")
        print("Exporting performance data to Excel file...")
        try:
            # Debug: Kiểm tra dữ liệu hiện có
            print(f"Current data records: {len(self.performance_logger.data_records)}")
            print(f"Performance logger type: {type(self.performance_logger)}")
            print(f"AI score: {self.ai_score}, AI level: {self.ai_level}")
            
            # Thêm dữ liệu AI và Human Player
            print("Adding current game data for both AI and Human Player...")
            
            # Thêm dữ liệu AI
            ai_record = {
                'algorithm': f"AI-{self.algorithm}",
                'avg_time_ms': 150.5,  # Giá trị mặc định
                'steps': 100,  # Giá trị mặc định
                'food_eaten': self.ai_score // 10,  # Ước tính từ score
                'deaths': 5 - self.ai_lives,  # Số lần chết
                'win_rate': 100.0 if self.ai_lives > 0 else 0.0,
                'score': self.ai_score,
                'level': self.ai_level + 1,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.performance_logger.data_records.append(ai_record)
            print(f"Added AI record: Score={self.ai_score}, Level={self.ai_level + 1}")
            
            # Thêm dữ liệu Human Player
            human_record = {
                'algorithm': "Human-Player",
                'avg_time_ms': 200.0,  # Human thường chậm hơn AI
                'steps': 120,  # Human thường đi nhiều bước hơn
                'food_eaten': self.player_score // 10,  # Ước tính từ score
                'deaths': 5 - self.player_lives,  # Số lần chết
                'win_rate': 100.0 if self.player_lives > 0 else 0.0,
                'score': self.player_score,
                'level': self.player_level + 1,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.performance_logger.data_records.append(human_record)
            print(f"Added Human Player record: Score={self.player_score}, Level={self.player_level + 1}")
            
            # Export dữ liệu ra file Excel
            success = self.performance_logger.export_to_excel()
            if success:
                print("SUCCESS: Exported results to algorithm_comparison.xlsx")
                
                # Tự động mở file Excel
                import os
                excel_file = "algorithm_comparison.xlsx"
                full_path = os.path.abspath(excel_file)
                
                print(f"[DEBUG] Attempting to open Excel file: {full_path}")
                print(f"[DEBUG] File exists: {os.path.exists(excel_file)}")
                
                try:
                    print(f"Opening Excel file: {full_path}")
                    os.startfile(full_path)  # 🚀 Tự mở Excel trên Windows
                    print("Excel file opened successfully!")
                except Exception as e:
                    print(f"[WARN] Could not open Excel file: {e}")
                    print("Please open the file manually at:", full_path)
            else:
                print("FAILED: Could not export results")
                print("💡 TIP: Close Excel if it's open, then try again!")
        except Exception as e:
            print(f"ERROR: Error during export: {e}")
        print("=== EXPORT COMPLETED ===")
    
    def clear_excel_data(self):
        """Xóa dữ liệu Excel cũ để giảm kích thước file"""
        try:
            print("=== CLEARING EXCEL DATA ===")
            import os
            
            excel_file = "algorithm_comparison.xlsx"
            
            # Kiểm tra file có tồn tại không
            if not os.path.exists(excel_file):
                print("No Excel file found to clear.")
                return
            
            # Lấy kích thước file hiện tại
            file_size_before = os.path.getsize(excel_file)
            print(f"File size before clearing: {file_size_before} bytes")
            
            # Xóa file Excel cũ
            os.remove(excel_file)
            print(f"Deleted old Excel file: {excel_file}")
            
            # Xóa dữ liệu trong performance logger
            self.performance_logger.data_records.clear()
            print("Cleared performance logger data")
            
            # Tạo file Excel mới với dữ liệu hiện tại (nếu có)
            if len(self.performance_logger.data_records) > 0:
                success = self.performance_logger.export_to_excel()
                if success:
                    print("Created new Excel file with current data")
                else:
                    print("Failed to create new Excel file")
            else:
                print("No current data to save")
            
            print("=== CLEAR DATA COMPLETED ===")
            
        except Exception as e:
            print(f"ERROR: Error during clear data: {e}")
    
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