import sys
import math
import pygame
from pathlib import Path

from statemachine import State
from ui.button import PacManButton
from ui.neontext import NeonText
from ui.constants import *
from states.game_state import GameState

class MenuState(State):   # kế thừa từ State
    HOME = 'home'
    OPTIONS = 'option'
    GAME_MODES = 'game_modes'
    SCORES = 'scores'
    STATES = 'states'

    def __init__(self, app, machine):
        super().__init__(app, machine)   # truyền app + machine cho State
        self.scene = MenuState.HOME
        self.animation_time = 0
        self.selected_algorithm = 'BFS'
        self._algorithms = ['BFS', 'DFS', 'IDS', 'UCS']
        self.current_button_index = 0

        self._load_background()

        self._init_ui_components()

    def _load_background(self):
        IMG_PATH = Path("assets/images/pm.jpg")
        if not IMG_PATH.exists():
            raise FileNotFoundError(f"Background image not found at {IMG_PATH}")
        
        bg = pygame.image.load(str(IMG_PATH)).convert()
        self.background = pygame.transform.scale(bg, (self.app.WIDTH, self.app.HEIGHT))

    def _init_ui_components(self):
        center_x = self.app.WIDTH // 2
        center_y = self.app.HEIGHT // 2
        
        self.UIComponents = {
            MenuState.HOME: self._create_home_components(center_x, center_y),
            MenuState.OPTIONS: self._create_options_components(center_x, center_y),
            MenuState.GAME_MODES: self._create_game_modes_components(center_x, center_y),
            MenuState.SCORES: self._create_scores_components(center_x, center_y),
            MenuState.STATES: self._create_states_components(center_x, center_y)
        }
        
        self.algo_button = self.UIComponents[MenuState.OPTIONS][2]

    def _create_home_components(self, center_x, center_y):
        # Better spacing and alignment for buttons
        button_spacing = 80  # Increased spacing between buttons
        start_y = center_y - 100  # Start position for first button
        
        return [
            NeonText(self.app, "PAC-MAN", PAC_YELLOW, center_x, center_y - 220, 80, 
                     glow=True, rainbow=True, outline=True),
            NeonText(self.app, "ARCADE ADVENTURE", GHOST_PINK, center_x, center_y - 160, 22, 
                     glow=True, outline=True),
            
            # Main menu buttons with better spacing
            PacManButton(self.app, pos=(center_x, start_y), text="🎮 GAME MODES", 
                         onclick=[self.show_game_modes], primary=True),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing), text="📊 HIGH SCORES", 
                         onclick=[self.show_scores]),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing * 2), text="🔧 SETTINGS", 
                         onclick=[self.show_options]),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing * 3), text="ℹ️ STATES", 
                         onclick=[self.show_states]),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing * 4), text="X EXIT", 
                         onclick=[self.quit]),
        
        ]

    def _create_options_components(self, center_x, center_y):
        return [
            NeonText(self.app, "SETTINGS", GHOST_PINK, center_x, center_y - 120, 60, 
                     glow=True, outline=True),
            NeonText(self.app, "Choose AI Algorithm:", DOT_WHITE, center_x, center_y - 60, 18, outline=True),
            
            # Algorithm selection button
            PacManButton(self.app, pos=(center_x, center_y - 10), text=f"AI: {self.selected_algorithm}", 
                         onclick=[self.cycle_algorithm], primary=True),
                       
            # Algorithm description
            NeonText(self.app, lambda: self.get_algo_description(), (255, 255, 255), 
                     center_x, center_y + 40, 14, outline=True),
            
            # Back button - moved further down
            PacManButton(self.app, pos=(center_x, center_y + 120), text="❮ BACK", 
                         onclick=[self.back_to_home]),
        ]

    def _create_game_modes_components(self, center_x, center_y):
        button_spacing = 80
        start_y = center_y - 80
        
        return [
            NeonText(self.app, "GAME MODES", PAC_YELLOW, center_x, center_y - 140, 50, 
                     glow=True, outline=True),
            
            # Game mode buttons with better spacing
            PacManButton(self.app, pos=(center_x, start_y), text="🤖 AI MODE", 
                         onclick=[self.start_ai_game], primary=True),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing), text="👤 PLAYER MODE", 
                         onclick=[self.start_player_game], primary=True),
            PacManButton(self.app, pos=(center_x, start_y + button_spacing * 2), text="⚔️ COMPARISON", 
                         onclick=[self.start_comparison_game], primary=True),
            
            # Back button - moved further down
            PacManButton(self.app, pos=(center_x, center_y + 180), text="❮ BACK", 
                         onclick=[self.back_to_home]),
        ]

    def _create_scores_components(self, center_x, center_y):
        return [
            NeonText(self.app, "HIGH SCORES", GHOST_ORANGE, center_x, center_y - 140, 50, 
                     glow=True, outline=True),
            
            # Placeholder scores with better spacing
            NeonText(self.app, "1. AI Master - 9999", DOT_WHITE, center_x, center_y - 80, 20, outline=True),
            NeonText(self.app, "2. Player Pro - 8500", DOT_WHITE, center_x, center_y - 50, 20, outline=True),
            NeonText(self.app, "3. Ghost Hunter - 7200", DOT_WHITE, center_x, center_y - 20, 20, outline=True),
            NeonText(self.app, "4. Dot Collector - 6800", DOT_WHITE, center_x, center_y + 10, 20, outline=True),
            NeonText(self.app, "5. Pac Champion - 5500", DOT_WHITE, center_x, center_y + 40, 20, outline=True),
            
            # Back button - moved further down
            PacManButton(self.app, pos=(center_x, center_y + 140), text="❮ BACK", 
                         onclick=[self.back_to_home]),
        ]

    def _create_states_components(self, center_x, center_y):
        return [
            NeonText(self.app, "GAME STATES", GHOST_BLUE, center_x, center_y - 140, 50, 
                     glow=True, outline=True),
            
            # State information with better spacing
            NeonText(self.app, "Current State: Menu", DOT_WHITE, center_x, center_y - 80, 18, outline=True),
            NeonText(self.app, "Available States:", DOT_WHITE, center_x, center_y - 50, 16, outline=True),
            NeonText(self.app, "• Menu State", GHOST_PINK, center_x, center_y - 20, 14, outline=True),
            NeonText(self.app, "• Game State", GHOST_PINK, center_x, center_y + 5, 14, outline=True),
            NeonText(self.app, "• Pause State", GHOST_PINK, center_x, center_y + 30, 14, outline=True),
            NeonText(self.app, "• Game Over State", GHOST_PINK, center_x, center_y + 55, 14, outline=True),
            
            # Back button - moved further down
            PacManButton(self.app, pos=(center_x, center_y + 140), text="❮ BACK", 
                         onclick=[self.back_to_home]),
        ]

    def get_algo_description(self):
        descriptions = {
            'BFS': "● Breadth-First: Explores level by level ●",
            'DFS': "● Depth-First: Goes deep first ●", 
            'IDS': "● Iterative Deepening: Best of both worlds ●",
            'UCS': "● Uniform Cost: Finds optimal path ●"
        }
        return descriptions.get(self.selected_algorithm, "")

    def start_game(self):
        game_state = GameState(self.app,self.machine,algorithm=self.selected_algorithm)
        self.replace_state(game_state)

    def start_ai_game(self):
        game_state = GameState(self.app,self.machine,algorithm=self.selected_algorithm)
        self.replace_state(game_state)

    def start_player_game(self):
        game_state = GameState(self.app,self.machine,algorithm=None)  # Player mode
        self.replace_state(game_state)

    def start_comparison_game(self):
        game_state = GameState(self.app,self.machine,algorithm=self.selected_algorithm, comparison_mode=True)
        self.replace_state(game_state)

    def cycle_algorithm(self):
        idx = self._algorithms.index(self.selected_algorithm)
        self.selected_algorithm = self._algorithms[(idx + 1) % len(self._algorithms)]
        
        if self.algo_button is not None:
            self.algo_button.text = f"AI: {self.selected_algorithm}"

    def show_game_modes(self):
        self.scene = MenuState.GAME_MODES
        self.current_button_index = 0
        self._update_scene_focus()

    def show_scores(self):
        self.scene = MenuState.SCORES
        self.current_button_index = 0
        self._update_scene_focus()

    def show_states(self):
        self.scene = MenuState.STATES
        self.current_button_index = 0
        self._update_scene_focus()

    def show_options(self):
        self.scene = MenuState.OPTIONS
        self.current_button_index = 0
        self._update_scene_focus()

    def back_to_home(self):
        self.scene = MenuState.HOME
        self.current_button_index = 0
        self._update_scene_focus()
    
    def _update_scene_focus(self):
        buttons = [comp for comp in self.UIComponents[self.scene] if isinstance(comp, PacManButton)]
        self._update_button_focus(buttons)

    def draw(self, _screen=None):
        """Vẽ menu lên app.screen (bỏ qua screen truyền vào để thống nhất)"""
        screen = self.app.screen
        
        screen.fill((0, 0, 0))
        
        if hasattr(self, 'background') and self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((20, 20, 40))
        
        self.animation_time += 0.02
        self._draw_pac_dots(screen)
        
        for comp in self.UIComponents[self.scene]:
            if hasattr(comp, 'render'):
                comp.render()   # các component tự vẽ vào app.screen

    def _draw_pac_dots(self, screen):
        dot_colors = [DOT_WHITE, PAC_YELLOW, GHOST_PINK, GHOST_RED]
        
        for i in range(15):
            x = (self.animation_time * 50 + i * 200) % (self.app.WIDTH + 100) - 50
            y = 150 + (i * 67) % 400 + 10 * math.sin(self.animation_time * 3 + i * 0.8)
            
            base_size = 4 if i % 4 == 0 else 3
            size = base_size + int(1 * math.sin(self.animation_time * 4 + i))
            color = dot_colors[i % len(dot_colors)]
            
            if 0 <= x <= self.app.WIDTH and 0 <= y <= self.app.HEIGHT:
                glow_surf = pygame.Surface((size*4, size*4), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (*color, 80), (size*2, size*2), size*2)
                screen.blit(glow_surf, (int(x-size*2), int(y-size*2)))
                
                pygame.draw.circle(screen, color, (int(x), int(y)), size)

    def logic(self):
        for comp in self.UIComponents[self.scene]:
            if hasattr(comp, 'update'):
                comp.update()

    def handle_events(self, event):
        if event.type == pygame.KEYDOWN:
            self._handle_keyboard_navigation(event)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for comp in self.UIComponents[self.scene]:
                if hasattr(comp, "handle_event"):
                    comp.handle_event(event)
        for comp in self.UIComponents[self.scene]:
            if hasattr(comp, "handle_event"):
                comp.handle_event(event)
    
    def _handle_keyboard_navigation(self, event):
        buttons = [comp for comp in self.UIComponents[self.scene] if isinstance(comp, PacManButton)]        
        if event.key == pygame.K_TAB:
            self.current_button_index = (self.current_button_index + 1) % len(buttons)
            self._update_button_focus(buttons)
        elif event.key in (pygame.K_UP, pygame.K_DOWN):
            if event.key == pygame.K_UP:
                self.current_button_index = (self.current_button_index - 1) % len(buttons)
            else:
                self.current_button_index = (self.current_button_index + 1) % len(buttons)
            self._update_button_focus(buttons)
        elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
            if buttons:
                buttons[self.current_button_index]._trigger_click()
        elif event.key == pygame.K_ESCAPE:
            if self.scene == MenuState.HOME:
                self.quit()
            else:
                self.back_to_home()
    
    def _update_button_focus(self, buttons):
        for i, button in enumerate(buttons):
            button.set_focus(False)  # Xóa tiêu điểm của tất cả nút
        buttons[self.current_button_index].set_focus(True)
            
    @classmethod
    def quit(cls):
        pygame.quit()
        sys.exit(0)
