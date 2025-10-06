# =============================================================================
# STATS_STATE.PY - STATE THỐNG KÊ RIÊNG BIỆT
# =============================================================================
# File này chứa StatsState - màn hình thống kê độc lập
# Quản lý hiển thị thống kê với nhiều views và biểu đồ

import pygame
import sys
from pathlib import Path

from statemachine import State
from ui.button import PacManButton
from ui.neontext import NeonText
from ui.constants import *
from engine.stats_logger import StatsLogger


class StatsState(State):
    """
    StatsState - Màn hình thống kê độc lập
    
    Chức năng:
    - Hiển thị thống kê game với 5 views khác nhau
    - Biểu đồ và bảng dữ liệu chi tiết
    - Filter và sort options
    - Navigation về menu chính
    """
    
    def __init__(self, app, machine, game=None):
        super().__init__(app, machine)
        self.game = game  # Lưu reference đến game object
        
        # View management
        self._current_view = "overview"  # overview, algorithms, heuristics, trends, efficiency
        self._sort_by = "score"  # score, steps, time, algorithm
        self._filter_algorithm = "ALL"
        self._filter_heuristic = "ALL"
        
        # Stats data
        self._stats_rows = []
        self._stats_summary = {}
        
        # UI components
        self._init_ui_components()
        
        # Load stats data
        self._load_stats_data()
    
    def _get_current_game_info(self):
        """Lấy thông tin few_mode và ghost_mode từ game object hiện tại"""
        if self.game and hasattr(self.game, 'few_pellets_mode') and hasattr(self.game, 'ghost_mode'):
            return {
                'few_pellets_mode': getattr(self.game, 'few_pellets_mode', False),
                'few_pellets_count': getattr(self.game, 'few_pellets_count', 7),
                'ghost_mode': getattr(self.game, 'ghost_mode', True)
            }
        return {
            'few_pellets_mode': False,
            'few_pellets_count': 7,
            'ghost_mode': True
        }
    
    def _init_ui_components(self):
        """Khởi tạo các UI components"""
        center_x = self.app.WIDTH // 2
        
        # Main title
        self.title = NeonText(
            self.app, "GAME STATISTICS", GHOST_BLUE, 
            center_x, 30, 50, glow=True, outline=True
        )
        
        # View selector buttons - only essential ones
        self.view_buttons = []
        view_configs = [
            ("📊 OVERVIEW", "overview"),
            ("🔧 ALGORITHMS", "algorithms"), 
            ("📈 TRENDS", "trends"),
        ]
        
        # Calculate buttons with proper spacing for 1920x1080
        button_height = 35
        screen_width = self.app.WIDTH
        num_buttons = len(view_configs)
        
        # Fixed button width for 1920px screen
        button_width = 250  # Fixed width for each button
        gap_between_buttons = 100  # Gap between buttons
        
        # Calculate total width needed
        total_width_needed = num_buttons * button_width + (num_buttons - 1) * gap_between_buttons
        start_x = (screen_width - total_width_needed) // 2  - 300
        
        for i, (text, view_name) in enumerate(view_configs):
            x = start_x + i * (button_width + gap_between_buttons)
            button = PacManButton(self.app, pos=(x, 100), text=text, 
                                 onclick=[lambda v=view_name: self._set_view(v)])
            # Make buttons uniform size
            button.w = button_width
            button.h = button_height
            button.rect = pygame.Rect(button.x, button.y, button.w, button.h)
            self.view_buttons.append(button)
        
        # Control buttons - only essential ones
        # Đặt các nút REFRESH và EXPORT CSV ở góc phải phía dưới
        control_configs = [
            ("🔄 REFRESH", self._refresh_stats),
            ("📊 EXPORT CSV", self._export_csv),
        ]
        
        control_height = 40
        num_control_buttons = len(control_configs)
        
        # Fixed control button width
        control_width = 200  # Fixed width for control buttons
        control_gap = 200  # Gap between control buttons

        # Vị trí các nút control ở góc phải phía dưới
        margin_bottom = 40
        margin_right = 50
        total_controls_width = num_control_buttons * control_width + (num_control_buttons - 1) * control_gap
        control_start_x = self.app.WIDTH - margin_right - total_controls_width
        control_y = self.app.HEIGHT - margin_bottom - control_height - 300

        self.control_buttons = []
        for i, (text, callback) in enumerate(control_configs):
            x = control_start_x + i * (control_width + control_gap)
            button = PacManButton(self.app, pos=(x, control_y), text=text, onclick=[callback])
            button.w = control_width
            button.h = control_height
            button.rect = pygame.Rect(button.x, button.y, button.w, button.h)
            self.control_buttons.append(button)
        
        # Keep individual references for backward compatibility
        self.refresh_button = self.control_buttons[0]
        # Back button
        self.back_button = PacManButton(
            self.app, pos=(center_x, self.app.HEIGHT - 60), text="❮ BACK TO MENU", 
            onclick=[self.back_to_menu]
        )
        
    
    def _load_stats_data(self):
        """Load dữ liệu thống kê từ CSV"""
        try:
            self._stats_rows = StatsLogger.load_recent(max_rows=50)
            self._stats_summary = StatsLogger.get_stats_summary()
            
            # Nếu không có dữ liệu thực, hiển thị thông báo
            if not self._stats_rows:
                print("No game data found. Play some games to see statistics!")
                self._stats_rows = []
                self._stats_summary = {}
                
        except Exception as e:
            print(f"Warning: Failed to load stats: {e}")
            self._stats_rows = []
            self._stats_summary = {}
    
    
    def _set_view(self, view_name):
        """Chuyển đổi view thống kê"""
        self.app.sound_system.play_sound('button_click')
        self._current_view = view_name
        print(f"Switched to view: {view_name}")
    
    def _toggle_filters(self):
        """Toggle filter options"""
        self.app.sound_system.play_sound('button_click')
        print("Filter options - TODO")
        # TODO: Implement filter UI
    
    def _toggle_sort(self):
        """Toggle sort options"""
        self.app.sound_system.play_sound('button_click')
        print("Sort options - TODO")
        # TODO: Implement sort UI
    
    def _refresh_stats(self):
        """Refresh thống kê"""
        self.app.sound_system.play_sound('button_click')
        self._load_stats_data()
        print("Stats refreshed")
    
    def _export_csv(self):
        """Export dữ liệu ra file CSV"""
        self.app.sound_system.play_sound('button_click')
        try:
            import csv
            import os
            from datetime import datetime
            
            # Tạo thư mục exports nếu chưa có
            export_dir = "exports"
            os.makedirs(export_dir, exist_ok=True)
            
            # Tạo tên file với timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"game_stats_export_{timestamp}.csv"
            filepath = os.path.join(export_dir, filename)
            
            # Headers cho CSV
            headers = [
                "timestamp", "time_formatted", "duration_sec",
                "algorithm", "heuristic", "ai_mode",
                "score", "total_steps", "ai_steps", "player_steps",
                "pellets_total", "pellets_eaten", "pellets_remaining",
                "level_reached", "few_pellets_mode", "few_pellets_count", 
                "ghost_mode", "result"
            ]
            
            # Ghi dữ liệu ra CSV
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()
                
                for row in self._stats_rows:
                    # Chỉ lấy các field cần thiết
                    export_row = {header: row.get(header, "") for header in headers}
                    writer.writerow(export_row)
            
            print(f"✅ Exported {len(self._stats_rows)} records to {filepath}")
            
        except Exception as e:
            print(f"❌ Export failed: {e}")
    
    def back_to_menu(self):
        """Quay về menu chính"""
        self.app.sound_system.play_sound('button_click')
        # Sử dụng replace_state thay vì change_state
        from states.menu_state import MenuState
        menu_state = MenuState(self.app, self.machine)
        self.replace_state(menu_state)
    
    def handle_events(self, event):
        """Xử lý events"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.sound_system.play_sound('button_click')
                self.back_to_menu()
            elif event.key == pygame.K_1:
                self.app.sound_system.play_sound('button_click')
                self._set_view("overview")
            elif event.key == pygame.K_2:
                self.app.sound_system.play_sound('button_click')
                self._set_view("algorithms")
            elif event.key == pygame.K_3:
                self.app.sound_system.play_sound('button_click')
                self._set_view("trends")
            elif event.key == pygame.K_r:
                self.app.sound_system.play_sound('button_click')
                self._refresh_stats()
            return  # Don't process mouse events for keyboard
        
        # Handle mouse events for buttons
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_button_clicks(event)
        
        # Handle button hover and other events
        all_buttons = self.view_buttons + self.control_buttons + [self.back_button]
        for button in all_buttons:
            if hasattr(button, 'handle_event'):
                button.handle_event(event)
    
    def _handle_button_clicks(self, event):
        """Xử lý click events cho buttons"""
        all_buttons = self.view_buttons + self.control_buttons + [self.back_button]
        
        for button in all_buttons:
            if hasattr(button, 'rect') and button.rect.collidepoint(event.pos):
                # Play click sound
                self.app.sound_system.play_sound('button_click')
                
                # Execute button callbacks
                if hasattr(button, 'onclick') and button.onclick:
                    for callback in button.onclick:
                        try:
                            callback()
                        except Exception as e:
                            print(f"Error executing button callback: {e}")
                
                # Break to prevent multiple button clicks
                break
    
    def logic(self):
        """Logic update"""
        # Update button states
        for i, button in enumerate(self.view_buttons):
            view_names = ["overview", "algorithms", "trends"]
            if i < len(view_names):
                button.set_active(self._current_view == view_names[i])
    
    def draw(self, screen=None):
        """Vẽ màn hình thống kê"""
        if screen is None:
            screen = self.app.screen
        
        # Clear screen
        screen.fill((0, 0, 0))
        
        # Draw background
        self._draw_background(screen)
        
        # Draw title
        self.title.render()
        
        # Draw buttons
        all_buttons = self.view_buttons + self.control_buttons + [self.back_button]
        for button in all_buttons:
            if hasattr(button, 'render'):
                button.render()
        
        # Draw current view content
        self._draw_current_view(screen)
        
        # Draw instructions
        self._draw_instructions(screen)
    
    def _draw_background(self, screen):
        """Vẽ background"""
        # Simple gradient background
        for y in range(self.app.HEIGHT):
            color_value = int(20 + (y / self.app.HEIGHT) * 30)
            pygame.draw.line(screen, (color_value, color_value, color_value + 20), 
                           (0, y), (self.app.WIDTH, y))
    
    def _draw_current_view(self, screen):
        """Vẽ content theo view hiện tại"""
        try:
            font_title = pygame.font.Font(FONT_PATH, 20)
            font_normal = pygame.font.Font(FONT_PATH, 13)
            font_small = pygame.font.Font(FONT_PATH, 13)
        except:
            font_title = pygame.font.Font(None, 20)
            font_normal = pygame.font.Font(None, 16)
            font_small = pygame.font.Font(None, 14)
        
        if self._current_view == "overview":
            self._draw_overview_view(screen, font_title, font_normal, font_small)
        elif self._current_view == "algorithms":
            self._draw_algorithms_view(screen, font_title, font_normal, font_small)
        elif self._current_view == "trends":
            self._draw_trends_view(screen, font_title, font_normal, font_small)
    
    def _draw_overview_view(self, screen, font_title, font_normal, font_small):
        """Vẽ view tổng quan"""
        start_y = 150
        
        # Summary cards
        self._draw_summary_cards(screen, font_title, font_normal, start_y)
        
        # All games table
        start_y += 100
        self._draw_all_games_table(screen, font_title, font_small, start_y)
    
    def _draw_algorithms_view(self, screen, font_title, font_normal, font_small):
        """Vẽ view so sánh algorithms"""
        start_y = 180
        
        # Algorithm performance table
        self._draw_algorithm_performance_table(screen, font_title, font_small, start_y)
    
    def _draw_heuristics_view(self, screen, font_title, font_normal, font_small):
        """Vẽ view phân tích heuristics"""
        start_y = 180
        
        # Heuristic performance table
        self._draw_heuristic_performance_table(screen, font_title, font_small, start_y)
        
        # Heuristic effectiveness charts
        start_y += 200
        self._draw_heuristic_effectiveness_charts(screen, font_normal, start_y)
    
    def _draw_trends_view(self, screen, font_title, font_normal, font_small):
        """Vẽ view xu hướng thời gian"""
        start_y = 180
        
        # Performance trends table
        self._draw_performance_trends_table(screen, font_title, font_small, start_y)
    
    def _draw_efficiency_view(self, screen, font_title, font_normal, font_small):
        """Vẽ view hiệu quả"""
        start_y = 180
        
        # Efficiency metrics
        self._draw_efficiency_metrics(screen, font_title, font_normal, start_y)
        
        # Score distribution
        start_y += 150
        self._draw_score_distribution(screen, font_normal, start_y)
        
        # Best/Worst games
        start_y += 200
        self._draw_best_worst_games(screen, font_normal, start_y)
    
    def _draw_summary_cards(self, screen, font_title, font_normal, start_y):
        """Vẽ các card tóm tắt"""
        summary = self._stats_summary
        
        # Tính toán dữ liệu thực từ stats_rows
        total_games = len(self._stats_rows)
        avg_score = sum(int(r.get("score", 0) or 0) for r in self._stats_rows) // max(1, total_games)
        avg_steps = sum(int(r.get("total_steps", 0) or 0) for r in self._stats_rows) // max(1, total_games)
        best_score = max([int(r.get("score", 0) or 0) for r in self._stats_rows], default=0)
        
        cards = [
            ("Total Games", str(total_games), GHOST_BLUE),
            ("Avg Score", str(avg_score), GHOST_ORANGE),
            ("Avg Steps", str(avg_steps), GHOST_PINK),
            ("Best Score", str(best_score), PAC_YELLOW),
        ]
        
        card_width = 200
        card_height = 80
        
        for i, (title, value, color) in enumerate(cards):
            x = 50 + i * (card_width + 20)
            y = start_y
            
            # Card background
            card_rect = pygame.Rect(x, y, card_width, card_height)
            pygame.draw.rect(screen, (30, 30, 50), card_rect)
            pygame.draw.rect(screen, color, card_rect, 2)
            
            # Title
            title_txt = font_normal.render(title, True, DOT_WHITE)
            screen.blit(title_txt, (x + 10, y + 10))
            
            # Value
            value_txt = font_title.render(value, True, color)
            screen.blit(value_txt, (x + 10, y + 35))
    
    def _draw_all_games_table(self, screen, font_title, font_small, start_y):
        """Vẽ bảng tất cả games"""
        # Background
        table_rect = pygame.Rect(50, start_y, self.app.WIDTH - 100, 400)
        pygame.draw.rect(screen, (25, 25, 45), table_rect)
        pygame.draw.rect(screen, GHOST_ORANGE, table_rect, 2)
        
        # Title
        title = font_title.render("ALL GAMES", True, PAC_YELLOW)
        screen.blit(title, (60, start_y + 10))
        
        # Headers - hiển thị đầy đủ features với khoảng cách lớn hơn

        headers = ["Time", "Algorithm", "Heuristic", "AI Mode", "Score", "Steps", "Pellets", "Power Pellets", "Lives Lost", "Mode", "Level", "Few Mode", "Ghost Mode", "Result"]
        col_widths = [130, 150, 150, 180, 130, 130, 150, 200, 180, 100, 120, 130, 180, 250]
        
        x = 60
        for i, header in enumerate(headers):
            txt = font_small.render(header, True, GHOST_PINK)
            screen.blit(txt, (x, start_y + 35))
            x += col_widths[i]
        
        # Rows - hiển thị tất cả games
        rows = self._stats_rows
        row_y = start_y + 65
        
        if not rows:
            # Hiển thị thông báo nếu không có dữ liệu
            no_data = font_small.render("No game data available. Play some games first!", True, DOT_WHITE)
            screen.blit(no_data, (60, row_y))
        else:
            # Hiển thị tối đa 12 games để vừa màn hình với nhiều columns
            display_rows = rows[-12:] if len(rows) > 12 else rows
            for row in reversed(display_rows):
                x = 60
                pellets_eaten = row.get("pellets_eaten", 0)
                pellets_total = row.get("pellets_total", 0)
                pellets_str = f"{pellets_eaten}/{pellets_total}"
                
                power_pellets_eaten = row.get("power_pellets_eaten", 0)
                power_pellets_total = row.get("power_pellets_total", 0)
                power_pellets_str = f"{power_pellets_eaten}/{power_pellets_total}"
                
                # Format few mode and ghost mode - lấy từ game object nếu có
                current_game_info = self._get_current_game_info()
                few_mode = "ON" if current_game_info['few_pellets_mode'] else "OFF"
                ghost_mode = "ON" if current_game_info['ghost_mode'] else "OFF"
                
                values = [
                    row.get("time_formatted", "00:00")[:5],
                    row.get("algorithm", "UNKNOWN")[:8],
                    row.get("heuristic", "UNKNOWN")[:8],
                    row.get("ai_mode", "AI")[:6],
                    str(row.get("score", 0))[:6],
                    str(row.get("total_steps", 0))[:6],
                    pellets_str[:8],
                    power_pellets_str[:8],
                    str(row.get("lives_lost", 0))[:3],
                    row.get("current_mode", "AI")[:6],
                    str(row.get("level_reached", 0))[:3],
                    few_mode[:6],
                    ghost_mode[:6],
                    row.get("result", "UNKNOWN")[:8],
                ]
                
                for i, val in enumerate(values):
                    if i == 13:  # Result column
                        color = GHOST_PINK if "COMPLETE" in val else GHOST_RED
                    elif i == 3:  # AI Mode column
                        color = GHOST_BLUE if "AI" in val else GHOST_ORANGE
                    elif i == 9:  # Mode column
                        color = GHOST_BLUE if "AI" in val else GHOST_ORANGE
                    elif i == 11:  # Few Mode column
                        color = GHOST_ORANGE if "ON" in val else DOT_WHITE
                    elif i == 12:  # Ghost Mode column
                        color = GHOST_BLUE if "ON" in val else DOT_WHITE
                    else:
                        color = DOT_WHITE
                    txt = font_small.render(val, True, color)
                    screen.blit(txt, (x, row_y))
                    x += col_widths[i]
                
                row_y += 25
                
                # Dừng nếu hết chỗ
                if row_y > start_y + 350:
                    break
    
    def _draw_algorithm_performance_table(self, screen, font_title, font_small, start_y):
        """Vẽ bảng performance của algorithms"""
        # Background
        table_rect = pygame.Rect(50, start_y, self.app.WIDTH - 100, 200)
        pygame.draw.rect(screen, (25, 25, 45), table_rect)
        pygame.draw.rect(screen, GHOST_BLUE, table_rect, 2)
        
        # Title
        title = font_title.render("ALGORITHM PERFORMANCE", True, PAC_YELLOW)
        screen.blit(title, (60, start_y + 10))
        
        # Headers
        headers = ["Algorithm", "Games", "Avg Score", "Win Rate", "Efficiency"]
        col_widths = [180, 130, 150, 150, 150]
        
        x = 60
        for i, header in enumerate(headers):
            txt = font_small.render(header, True, GHOST_PINK)
            screen.blit(txt, (x, start_y + 35))
            x += col_widths[i]
        
        # Rows
        algo_perf = self._stats_summary.get("algorithm_performance", {})
        row_y = start_y + 55
        for algo, stats in algo_perf.items():
            x = 60
            values = [
                algo[:12],
                str(stats.get("count", 0)),
                str(stats.get("avg_score", 0)),
                f"{stats.get('win_rate', 0):.1f}%",
                f"{stats.get('efficiency', 0):.2f}",
            ]
            
            for i, val in enumerate(values):
                txt = font_small.render(val, True, DOT_WHITE)
                screen.blit(txt, (x, row_y))
                x += col_widths[i]
            
            row_y += 20
    
    def _draw_performance_trends_table(self, screen, font_title, font_small, start_y):
        """Vẽ bảng xu hướng performance"""
        # Background
        table_rect = pygame.Rect(50, start_y, self.app.WIDTH - 100, 400)
        pygame.draw.rect(screen, (25, 25, 45), table_rect)
        pygame.draw.rect(screen, GHOST_BLUE, table_rect, 2)
        
        # Title
        title = font_title.render("PERFORMANCE TRENDS", True, PAC_YELLOW)
        screen.blit(title, (60, start_y + 10))
        
        # Headers - hiển thị đầy đủ features với khoảng cách lớn hơn
        headers = ["Game #", "Algorithm", "Heuristic", "AI Mode", "Score", "Steps", "Efficiency", "Pellets", "Power Pellets", "Lives Lost", "Mode", "Few Mode", "Ghost Mode", "Result"]
        col_widths = [110, 140, 140, 180, 120, 120, 130, 150, 200, 180, 100, 120, 180, 140]
        
        x = 60
        for i, header in enumerate(headers):
            txt = font_small.render(header, True, GHOST_PINK)
            screen.blit(txt, (x, start_y + 35))
            x += col_widths[i]
        
        # Rows - hiển thị games với efficiency
        rows = self._stats_rows
        row_y = start_y + 65
        
        if not rows:
            no_data = font_small.render("No game data available. Play some games first!", True, DOT_WHITE)
            screen.blit(no_data, (60, row_y))
        else:
            # Hiển thị tối đa 12 games để vừa màn hình với nhiều columns
            display_rows = rows[-12:] if len(rows) > 12 else rows
            for i, row in enumerate(reversed(display_rows)):
                x = 60
                score = int(row.get("score", 0))
                steps = int(row.get("total_steps", 1))
                efficiency = score / steps if steps > 0 else 0
                pellets_eaten = row.get("pellets_eaten", 0)
                pellets_total = row.get("pellets_total", 0)
                pellets_str = f"{pellets_eaten}/{pellets_total}"
                
                power_pellets_eaten = row.get("power_pellets_eaten", 0)
                power_pellets_total = row.get("power_pellets_total", 0)
                power_pellets_str = f"{power_pellets_eaten}/{power_pellets_total}"
                
                # Format few mode and ghost mode - lấy từ game object nếu có
                current_game_info = self._get_current_game_info()
                few_mode = "ON" if current_game_info['few_pellets_mode'] else "OFF"
                ghost_mode = "ON" if current_game_info['ghost_mode'] else "OFF"
                
                values = [
                    f"#{len(rows) - i}",
                    row.get("algorithm", "UNKNOWN")[:8],
                    row.get("heuristic", "UNKNOWN")[:8],
                    row.get("ai_mode", "AI")[:6],
                    str(score)[:6],
                    str(steps)[:6],
                    f"{efficiency:.2f}",
                    pellets_str[:8],
                    power_pellets_str[:8],
                    str(row.get("lives_lost", 0))[:3],
                    row.get("current_mode", "AI")[:6],
                    few_mode[:6],
                    ghost_mode[:6],
                    row.get("result", "UNKNOWN")[:8],
                ]
                
                for j, val in enumerate(values):
                    if j == 13:  # Result column
                        color = GHOST_PINK if "COMPLETE" in val else GHOST_RED
                    elif j == 3:  # AI Mode column
                        color = GHOST_BLUE if "AI" in val else GHOST_ORANGE
                    elif j == 10:  # Mode column
                        color = GHOST_BLUE if "AI" in val else GHOST_ORANGE
                    elif j == 11:  # Few Mode column
                        color = GHOST_ORANGE if "ON" in val else DOT_WHITE
                    elif j == 12:  # Ghost Mode column
                        color = GHOST_BLUE if "ON" in val else DOT_WHITE
                    else:
                        color = DOT_WHITE
                    txt = font_small.render(val, True, color)
                    screen.blit(txt, (x, row_y))
                    x += col_widths[j]
                
                row_y += 25
                
                # Dừng nếu hết chỗ
                if row_y > start_y + 350:
                    break
    
    def _draw_instructions(self, screen):
        """Vẽ hướng dẫn sử dụng"""
        try:
            font = pygame.font.Font(None, 12)
        except:
            font = pygame.font.Font(None, 12)
        
        instructions = [
            "ESC: Back to Menu | 1-3: Switch Views | R: Refresh Data | Export CSV available",
            "Click buttons to navigate | Use mouse to interact | Data exported to exports/ folder"
        ]
        
        y = self.app.HEIGHT - 100
        for instruction in instructions:
            txt = font.render(instruction, True, DOT_WHITE)
            screen.blit(txt, (50, y))
            y += 20
