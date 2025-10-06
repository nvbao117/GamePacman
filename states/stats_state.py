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
    
    def __init__(self, app, machine):
        super().__init__(app, machine)
        
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
        
        # Calculate smaller buttons with tighter spacing
        button_height = 35  # Smaller height
        screen_width = self.app.WIDTH
        num_buttons = len(view_configs)
        
        # Calculate button width to fill screen with equal spacing
        total_gap_width = (num_buttons + 1) * 20 + (num_buttons - 1) * 5  # 20px margin on each side + 5px gaps between buttons
        available_width = screen_width - total_gap_width
        button_width = available_width // num_buttons  - 100
        
        # Calculate positions for perfectly centered buttons
        # Calculate total width needed and center it
        total_width_needed = num_buttons * button_width + (num_buttons - 1) * 5
        start_x = (screen_width - total_width_needed) // 2  # Center the buttons
        
        for i, (text, view_name) in enumerate(view_configs):
            x = start_x + i * (button_width + 5)  # 5px gap between buttons
            button = PacManButton(self.app, pos=(x, 100), text=text, 
                                 onclick=[lambda v=view_name: self._set_view(v)])
            # Make buttons uniform size
            button.w = button_width
            button.h = button_height
            button.rect = pygame.Rect(button.x, button.y, button.w, button.h)
            self.view_buttons.append(button)
        
        # Control buttons - only essential ones
        control_configs = [
            ("🔄 REFRESH", self._refresh_stats),
        ]
        
        # Calculate control buttons to fill remaining space on right
        control_height = 40
        num_control_buttons = len(control_configs)
        
        # Use remaining space after view buttons
        view_buttons_end = start_x + num_buttons * (button_width + 20)
        remaining_width = screen_width - view_buttons_end - 20  # 20px margin from right
        
        # Calculate control button width
        control_gap = 10
        control_total_gap = (num_control_buttons - 1) * control_gap
        control_width = (remaining_width - control_total_gap) // num_control_buttons
        
        # Position control buttons
        control_start_x = view_buttons_end + 20  # 20px gap after view buttons
        
        self.control_buttons = []
        for i, (text, callback) in enumerate(control_configs):
            x = control_start_x + i * (control_width + control_gap)
            button = PacManButton(self.app, pos=(x, 100), text=text, onclick=[callback])
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
            
            # Nếu không có dữ liệu, tạo dữ liệu mẫu để test
            if not self._stats_rows:
                self._create_sample_data()
                
        except Exception as e:
            print(f"Warning: Failed to load stats: {e}")
            self._stats_rows = []
            self._stats_summary = {}
            self._create_sample_data()
    
    def _create_sample_data(self):
        """Tạo dữ liệu mẫu để test"""
        import datetime
        
        sample_data = [
            {
                "timestamp": datetime.datetime.now().isoformat(),
                "time_formatted": "02:15",
                "duration_sec": 135,
                "algorithm": "A*",
                "heuristic": "MANHATTAN",
                "ai_mode": "OFFLINE",
                "score": 920,
                "total_steps": 180,
                "ai_steps": 180,
                "player_steps": 0,
                "pellets_total": 240,
                "pellets_eaten": 240,
                "pellets_remaining": 0,
                "level_reached": 1,
                "few_pellets_mode": False,
                "few_pellets_count": 0,
                "ghost_mode": True,
                "result": "LEVEL_COMPLETE",
            },
            {
                "timestamp": datetime.datetime.now().isoformat(),
                "time_formatted": "01:45",
                "duration_sec": 105,
                "algorithm": "BFS",
                "heuristic": "NONE",
                "ai_mode": "OFFLINE",
                "score": 780,
                "total_steps": 310,
                "ai_steps": 310,
                "player_steps": 0,
                "pellets_total": 240,
                "pellets_eaten": 200,
                "pellets_remaining": 40,
                "level_reached": 0,
                "few_pellets_mode": False,
                "few_pellets_count": 0,
                "ghost_mode": True,
                "result": "GAME_OVER",
            },
            {
                "timestamp": datetime.datetime.now().isoformat(),
                "time_formatted": "03:20",
                "duration_sec": 200,
                "algorithm": "DFS",
                "heuristic": "EUCLIDEAN",
                "ai_mode": "ONLINE",
                "score": 650,
                "total_steps": 450,
                "ai_steps": 450,
                "player_steps": 0,
                "pellets_total": 240,
                "pellets_eaten": 180,
                "pellets_remaining": 60,
                "level_reached": 0,
                "few_pellets_mode": False,
                "few_pellets_count": 0,
                "ghost_mode": True,
                "result": "GAME_OVER",
            }
        ]
        
        self._stats_rows = sample_data
        self._stats_summary = StatsLogger.get_stats_summary()
    
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
            font_title = pygame.font.Font(FONT_PATH, 16)
            font_normal = pygame.font.Font(FONT_PATH, 12)
            font_small = pygame.font.Font(FONT_PATH, 10)
        except:
            font_title = pygame.font.Font(None, 16)
            font_normal = pygame.font.Font(None, 12)
            font_small = pygame.font.Font(None, 10)
        
        if self._current_view == "overview":
            self._draw_overview_view(screen, font_title, font_normal, font_small)
        elif self._current_view == "algorithms":
            self._draw_algorithms_view(screen, font_title, font_normal, font_small)
        elif self._current_view == "heuristics":
            self._draw_heuristics_view(screen, font_title, font_normal, font_small)
        elif self._current_view == "trends":
            self._draw_trends_view(screen, font_title, font_normal, font_small)
        elif self._current_view == "efficiency":
            self._draw_efficiency_view(screen, font_title, font_normal, font_small)
    
    def _draw_overview_view(self, screen, font_title, font_normal, font_small):
        """Vẽ view tổng quan"""
        start_y = 150
        
        # Summary cards - chiếm 1/3 màn hình
        self._draw_summary_cards(screen, font_title, font_normal, start_y)
        
        # Recent games table - chiếm 1/3 màn hình
        start_y += 100
        self._draw_recent_games_table(screen, font_title, font_small, start_y)
        
        # Quick charts - chiếm 1/3 màn hình
        start_y += 180
        self._draw_quick_charts(screen, font_normal, start_y)
    
    def _draw_algorithms_view(self, screen, font_title, font_normal, font_small):
        """Vẽ view so sánh algorithms"""
        start_y = 180
        
        # Algorithm performance table
        self._draw_algorithm_performance_table(screen, font_title, font_small, start_y)
        
        # Algorithm comparison charts
        start_y += 200
        self._draw_algorithm_comparison_charts(screen, font_normal, start_y)
    
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
        
        # Time series charts
        self._draw_time_series_charts(screen, font_normal, start_y)
        
        # Performance trends
        start_y += 300
        self._draw_performance_trends(screen, font_normal, start_y)
    
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
    
    def _draw_recent_games_table(self, screen, font_title, font_small, start_y):
        """Vẽ bảng games gần nhất"""
        # Background
        table_rect = pygame.Rect(50, start_y, self.app.WIDTH - 100, 180)
        pygame.draw.rect(screen, (25, 25, 45), table_rect)
        pygame.draw.rect(screen, GHOST_ORANGE, table_rect, 2)
        
        # Title
        title = font_title.render("RECENT GAMES", True, PAC_YELLOW)
        screen.blit(title, (60, start_y + 10))
        
        # Headers
        headers = ["Time", "Algorithm", "Score", "Steps", "Result"]
        col_widths = [80, 100, 80, 80, 100]
        
        x = 60
        for i, header in enumerate(headers):
            txt = font_small.render(header, True, GHOST_PINK)
            screen.blit(txt, (x, start_y + 35))
            x += col_widths[i]
        
        # Rows
        rows = self._stats_rows[-8:]  # 8 games gần nhất
        row_y = start_y + 55
        
        if not rows:
            # Hiển thị thông báo nếu không có dữ liệu
            no_data = font_small.render("No game data available. Play some games first!", True, DOT_WHITE)
            screen.blit(no_data, (60, row_y))
        else:
            for row in reversed(rows):
                x = 60
                values = [
                    row.get("time_formatted", "00:00")[:5],
                    row.get("algorithm", "UNKNOWN")[:10],
                    str(row.get("score", 0))[:6],
                    str(row.get("total_steps", 0))[:6],
                    row.get("result", "UNKNOWN")[:10],
                ]
                
                for i, val in enumerate(values):
                    color = DOT_WHITE if i < 4 else (GHOST_PINK if "COMPLETE" in val else GHOST_RED)
                    txt = font_small.render(val, True, color)
                    screen.blit(txt, (x, row_y))
                    x += col_widths[i]
                
                row_y += 20
    
    def _draw_quick_charts(self, screen, font_normal, start_y):
        """Vẽ biểu đồ nhanh"""
        # Score trend (left)
        chart1_rect = pygame.Rect(50, start_y, 550, 150)
        pygame.draw.rect(screen, (30, 30, 50), chart1_rect)
        pygame.draw.rect(screen, GHOST_BLUE, chart1_rect, 2)
        
        title1 = font_normal.render("Score Trend", True, PAC_YELLOW)
        screen.blit(title1, (chart1_rect.x + 10, chart1_rect.y + 10))
        
        # Steps trend (right)
        chart2_rect = pygame.Rect(630, start_y, 550, 150)
        pygame.draw.rect(screen, (30, 30, 50), chart2_rect)
        pygame.draw.rect(screen, GHOST_BLUE, chart2_rect, 2)
        
        title2 = font_normal.render("Steps Trend", True, PAC_YELLOW)
        screen.blit(title2, (chart2_rect.x + 10, chart2_rect.y + 10))
        
        # Draw simple line charts
        if self._stats_rows:
            scores = [int(r.get("score", 0) or 0) for r in self._stats_rows[-10:]]
            steps = [int(r.get("total_steps", 0) or 0) for r in self._stats_rows[-10:]]
            self._draw_simple_line_chart(screen, chart1_rect, scores, GHOST_ORANGE)
            self._draw_simple_line_chart(screen, chart2_rect, steps, GHOST_PINK)
        else:
            # Hiển thị thông báo nếu không có dữ liệu
            no_data1 = font_normal.render("No data available", True, DOT_WHITE)
            no_data2 = font_normal.render("No data available", True, DOT_WHITE)
            screen.blit(no_data1, (chart1_rect.x + 20, chart1_rect.y + 50))
            screen.blit(no_data2, (chart2_rect.x + 20, chart2_rect.y + 50))
    
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
        col_widths = [120, 80, 100, 100, 100]
        
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
    
    def _draw_algorithm_comparison_charts(self, screen, font_normal, start_y):
        """Vẽ biểu đồ so sánh algorithms"""
        # Bar chart for algorithm scores
        chart_rect = pygame.Rect(50, start_y, self.app.WIDTH - 100, 200)
        pygame.draw.rect(screen, (30, 30, 50), chart_rect)
        pygame.draw.rect(screen, GHOST_ORANGE, chart_rect, 2)
        
        title = font_normal.render("Algorithm Comparison", True, PAC_YELLOW)
        screen.blit(title, (chart_rect.x + 10, chart_rect.y + 10))
        
        # Draw bar chart
        algo_perf = self._stats_summary.get("algorithm_performance", {})
        if algo_perf:
            self._draw_bar_chart(screen, chart_rect, algo_perf, "avg_score", GHOST_ORANGE)
    
    def _draw_heuristic_performance_table(self, screen, font_title, font_small, start_y):
        """Vẽ bảng performance của heuristics"""
        table_rect = pygame.Rect(50, start_y, self.app.WIDTH - 100, 200)
        pygame.draw.rect(screen, (25, 25, 45), table_rect)
        pygame.draw.rect(screen, GHOST_PINK, table_rect, 2)
        
        title = font_title.render("HEURISTIC PERFORMANCE", True, PAC_YELLOW)
        screen.blit(title, (60, start_y + 10))
        
        # Implementation similar to algorithm table
        heur_perf = self._stats_summary.get("heuristic_performance", {})
        if heur_perf:
            # Headers
            headers = ["Heuristic", "Games", "Avg Score", "Efficiency", "Best Algo"]
            col_widths = [120, 80, 100, 100, 100]
            
            x = 60
            for i, header in enumerate(headers):
                txt = font_small.render(header, True, GHOST_PINK)
                screen.blit(txt, (x, start_y + 35))
                x += col_widths[i]
            
            # Rows
            row_y = start_y + 55
            for heur, stats in heur_perf.items():
                x = 60
                values = [
                    heur[:12],
                    str(stats.get("count", 0)),
                    str(stats.get("avg_score", 0)),
                    f"{stats.get('efficiency', 0):.2f}",
                    "A*",  # TODO: Calculate best algorithm
                ]
                
                for i, val in enumerate(values):
                    txt = font_small.render(val, True, DOT_WHITE)
                    screen.blit(txt, (x, row_y))
                    x += col_widths[i]
                
                row_y += 20
    
    def _draw_heuristic_effectiveness_charts(self, screen, font_normal, start_y):
        """Vẽ biểu đồ hiệu quả của heuristics"""
        # Similar to algorithm charts but for heuristics
        chart_rect = pygame.Rect(50, start_y, self.app.WIDTH - 100, 200)
        pygame.draw.rect(screen, (30, 30, 50), chart_rect)
        pygame.draw.rect(screen, GHOST_PINK, chart_rect, 2)
        
        title = font_normal.render("Heuristic Effectiveness", True, PAC_YELLOW)
        screen.blit(title, (chart_rect.x + 10, chart_rect.y + 10))
        
        # Draw bar chart
        heur_perf = self._stats_summary.get("heuristic_performance", {})
        if heur_perf:
            self._draw_bar_chart(screen, chart_rect, heur_perf, "avg_score", GHOST_PINK)
    
    def _draw_time_series_charts(self, screen, font_normal, start_y):
        """Vẽ biểu đồ time series"""
        # Time series for recent games
        chart_rect = pygame.Rect(50, start_y, self.app.WIDTH - 100, 250)
        pygame.draw.rect(screen, (30, 30, 50), chart_rect)
        pygame.draw.rect(screen, GHOST_BLUE, chart_rect, 2)
        
        title = font_normal.render("Performance Over Time", True, PAC_YELLOW)
        screen.blit(title, (chart_rect.x + 10, chart_rect.y + 10))
        
        # Draw time series
        if self._stats_rows:
            scores = [int(r.get("score", 0) or 0) for r in self._stats_rows[-20:]]
            steps = [int(r.get("total_steps", 0) or 0) for r in self._stats_rows[-20:]]
            
            # Draw score line
            self._draw_simple_line_chart(screen, chart_rect, scores, GHOST_ORANGE)
    
    def _draw_performance_trends(self, screen, font_normal, start_y):
        """Vẽ xu hướng performance"""
        # Performance trends analysis
        chart_rect = pygame.Rect(50, start_y, self.app.WIDTH - 100, 200)
        pygame.draw.rect(screen, (30, 30, 50), chart_rect)
        pygame.draw.rect(screen, GHOST_BLUE, chart_rect, 2)
        
        title = font_normal.render("Performance Trends", True, PAC_YELLOW)
        screen.blit(title, (chart_rect.x + 10, chart_rect.y + 10))
        
        # TODO: Implement trend analysis
        no_data = font_normal.render("Trend analysis coming soon...", True, DOT_WHITE)
        screen.blit(no_data, (chart_rect.x + 20, chart_rect.y + 50))
    
    def _draw_efficiency_metrics(self, screen, font_title, font_normal, start_y):
        """Vẽ metrics hiệu quả"""
        # Efficiency metrics display
        metrics_rect = pygame.Rect(50, start_y, self.app.WIDTH - 100, 120)
        pygame.draw.rect(screen, (25, 25, 45), metrics_rect)
        pygame.draw.rect(screen, PAC_YELLOW, metrics_rect, 2)
        
        title = font_title.render("EFFICIENCY METRICS", True, PAC_YELLOW)
        screen.blit(title, (60, start_y + 10))
        
        # Metrics
        eff_metrics = self._stats_summary.get("efficiency_metrics", {})
        metrics_text = [
            f"Best Score: {eff_metrics.get('best_score', 0)}",
            f"Worst Score: {eff_metrics.get('worst_score', 0)}",
            f"Consistency: {eff_metrics.get('score_consistency', 0):.1f}%",
            f"Avg Efficiency: {eff_metrics.get('avg_efficiency', 0):.2f}",
        ]
        
        y = start_y + 40
        for text in metrics_text:
            txt = font_normal.render(text, True, DOT_WHITE)
            screen.blit(txt, (60, y))
            y += 25
    
    def _draw_score_distribution(self, screen, font_normal, start_y):
        """Vẽ phân phối điểm số"""
        # Score distribution chart
        chart_rect = pygame.Rect(50, start_y, self.app.WIDTH - 100, 150)
        pygame.draw.rect(screen, (30, 30, 50), chart_rect)
        pygame.draw.rect(screen, GHOST_ORANGE, chart_rect, 2)
        
        title = font_normal.render("Score Distribution", True, PAC_YELLOW)
        screen.blit(title, (chart_rect.x + 10, chart_rect.y + 10))
        
        # Draw distribution bars
        distribution = self._stats_summary.get("score_distribution", [])
        if distribution:
            self._draw_distribution_chart(screen, chart_rect, distribution)
    
    def _draw_best_worst_games(self, screen, font_normal, start_y):
        """Vẽ best/worst games"""
        # Best/Worst games display
        games_rect = pygame.Rect(50, start_y, self.app.WIDTH - 100, 120)
        pygame.draw.rect(screen, (25, 25, 45), games_rect)
        pygame.draw.rect(screen, GHOST_BLUE, games_rect, 2)
        
        title = font_normal.render("BEST & WORST GAMES", True, PAC_YELLOW)
        screen.blit(title, (60, start_y + 10))
        
        # Best/Worst game info
        eff_metrics = self._stats_summary.get("efficiency_metrics", {})
        best_game = eff_metrics.get("best_game", {})
        worst_game = eff_metrics.get("worst_game", {})
        
        best_text = f"🏆 Best: {best_game.get('algorithm', 'N/A')} + {best_game.get('heuristic', 'N/A')} = {best_game.get('score', 0)} pts"
        worst_text = f"💀 Worst: {worst_game.get('algorithm', 'N/A')} + {worst_game.get('heuristic', 'N/A')} = {worst_game.get('score', 0)} pts"
        
        best_txt = font_normal.render(best_text, True, GHOST_PINK)
        worst_txt = font_normal.render(worst_text, True, GHOST_RED)
        
        screen.blit(best_txt, (60, start_y + 40))
        screen.blit(worst_txt, (60, start_y + 65))
    
    def _draw_simple_line_chart(self, screen, rect, data, color):
        """Vẽ biểu đồ line đơn giản"""
        if len(data) < 2:
            return
        
        # Calculate points
        max_val = max(data) if data else 1
        points = []
        for i, val in enumerate(data):
            x = rect.x + 20 + int(i * (rect.width - 40) / (len(data) - 1))
            y = rect.bottom - 20 - int((val / max_val) * (rect.height - 40))
            points.append((x, y))
        
        # Draw line
        if len(points) >= 2:
            pygame.draw.lines(screen, color, False, points, 3)
            # Draw dots
            for pt in points:
                pygame.draw.circle(screen, PAC_YELLOW, pt, 3)
    
    def _draw_bar_chart(self, screen, rect, data, field, color):
        """Vẽ biểu đồ bar"""
        if not data:
            return
        
        # Get values
        values = [stats.get(field, 0) for stats in data.values()]
        max_val = max(values) if values else 1
        
        # Draw bars
        bar_width = max(20, (rect.width - 40) // len(data))
        x = rect.x + 20
        
        for i, (algo, stats) in enumerate(data.items()):
            value = stats.get(field, 0)
            height = int((value / max_val) * (rect.height - 60))
            y = rect.bottom - height - 20
            
            # Bar
            bar_rect = pygame.Rect(x, y, bar_width - 4, height)
            pygame.draw.rect(screen, color, bar_rect)
            
            # Label
            label = algo[:8]
            try:
                font = pygame.font.Font(None, 10)
                label_txt = font.render(label, True, DOT_WHITE)
                screen.blit(label_txt, (x, rect.bottom - 15))
            except:
                pass
            
            x += bar_width
    
    def _draw_distribution_chart(self, screen, rect, distribution):
        """Vẽ biểu đồ phân phối"""
        if not distribution:
            return
        
        # Draw bars for each range
        bar_width = (rect.width - 40) // len(distribution)
        x = rect.x + 20
        
        for item in distribution:
            count = item.get("count", 0)
            max_count = max([d.get("count", 0) for d in distribution]) if distribution else 1
            height = int((count / max_count) * (rect.height - 60))
            y = rect.bottom - height - 20
            
            # Bar
            bar_rect = pygame.Rect(x, y, bar_width - 4, height)
            pygame.draw.rect(screen, GHOST_ORANGE, bar_rect)
            
            # Label
            range_label = item.get("range", "")
            try:
                font = pygame.font.Font(None, 10)
                label_txt = font.render(range_label, True, DOT_WHITE)
                screen.blit(label_txt, (x, rect.bottom - 15))
            except:
                pass
            
            x += bar_width
    
    def _draw_instructions(self, screen):
        """Vẽ hướng dẫn sử dụng"""
        try:
            font = pygame.font.Font(None, 12)
        except:
            font = pygame.font.Font(None, 12)
        
        instructions = [
            "ESC: Back to Menu | 1-5: Switch Views | R: Refresh Data",
            "Click buttons to navigate | Use mouse to interact"
        ]
        
        y = self.app.HEIGHT - 100
        for instruction in instructions:
            txt = font.render(instruction, True, DOT_WHITE)
            screen.blit(txt, (50, y))
            y += 20
