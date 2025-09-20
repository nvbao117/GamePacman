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
class GameState(State):   # kế thừa từ State
    HOME = 'home'
    OPTIONS = 'option'

    def __init__(self, app, machine,algorithm = "BFS"):
        super().__init__(app, machine)  
        self.algorithm = algorithm 
        self.is_pause = False
        self.game_running = True
        
        self.layout = GameLayout(app)
        self.game = Game(algorithm)
        if hasattr(self.game, 'initialize_game'):
            self.game.initialize_game()
        
        self.score = getattr(self.game,'score',0)
        self.lives = getattr(self.game,'lives',5)  # Game starts with 5 lives
        self.level = getattr(self.game,'level',0)  # Game starts with level 0

        self.layout.set_game_info(self.score, self.lives, self.level, self.algorithm)
        
    def _render_scaled_game(self, game_surface, game_rect):
        """Render game content scaled to fit the game area properly with correct aspect ratio"""
        # Get the original game dimensions from constants
        from constants import SCREENSIZE
        original_width, original_height = SCREENSIZE
        
        # Calculate scaling factors to maintain aspect ratio
        scale_x = game_rect.width / original_width
        scale_y = game_rect.height / original_height
        
        # Use the smaller scale to maintain aspect ratio and fit properly
        scale = min(scale_x, scale_y)
        
        # Calculate scaled dimensions
        scaled_width = int(original_width * scale)
        scaled_height = int(original_height * scale)
        
        # Create a temporary surface for the scaled game
        temp_surface = pygame.Surface((original_width, original_height))
        
        # Very subtle background
        for y in range(original_height):
            intensity = int(2 + (y / original_height) * 3)  # Very subtle
            color = (intensity, intensity + 2, intensity + 8)
            pygame.draw.line(temp_surface, color, (0, y), (original_width, y))
        
        # Render game to temporary surface at original size
        self.game.render(temp_surface)
        
        # Scale the temporary surface to fit the game area with smooth scaling
        scaled_surface = pygame.transform.smoothscale(temp_surface, (scaled_width, scaled_height))
        
        # Center the scaled game in the game area
        x_offset = (game_rect.width - scaled_width) // 2
        y_offset = (game_rect.height - scaled_height) // 2
        
        # Clear the game surface first
        game_surface.fill((0, 0, 0, 0))
        
        # Blit the scaled game directly to the game surface
        game_surface.blit(scaled_surface, (x_offset, y_offset))
        
    def draw(self, _screen=None):
        self.layout.render()
        
        # Render game lên subsurface của khu vực game
        game_rect = self.layout.get_game_area_rect()
        game_surface = self.layout.surface.subsurface(game_rect)
        
        # Scale game content to fit the game area properly
        self._render_scaled_game(game_surface, game_rect)
        
    def logic(self):
        # Always update layout animations
        self.layout.update()
        
        # Sync play state between layout and game state
        self.layout.is_playing = not self.is_pause
        
        if not self.is_pause and self.game_running:
            if hasattr(self.game,'update'):
                self.game.update()
            
            # Update game values from the actual game
            self.score = getattr(self.game, 'score', self.score)
            self.lives = getattr(self.game, 'lives', self.lives)
            self.level = getattr(self.game, 'level', self.level)
            
            # Update layout with current game values
            self.layout.set_game_info(self.score, self.lives, self.level, self.algorithm)
        else:
            # Even when paused, update layout with current values
            self.layout.set_game_info(self.score, self.lives, self.level, self.algorithm)

        if self.lives <= 0:
            self.game_over()
    
    def handle_events(self, event):
        # Handle play button click first
        if self.layout.handle_play_button_click(event):
            # Play state changed, update game pause state
            self.is_pause = not self.layout.is_playing
            if hasattr(self.game, 'pause'):
                if self.layout.is_playing:
                    self.game.pause.setPause(pauseTime=0)  # Resume game
                else:
                    self.game.pause.setPause(playerPaused=True)  # Pause game
        
        # Handle selectbox events
        if self.layout.handle_selectbox_event(event):
            # Algorithm changed, update the game
            self.algorithm = self.layout.algorithm
            self.game = Game(self.algorithm)
            if hasattr(self.game, 'initialize_game'):
                self.game.initialize_game()
            # Reset game values when algorithm changes
            self.score = getattr(self.game, 'score', 0)
            self.lives = getattr(self.game, 'lives', 5)
            self.level = getattr(self.game, 'level', 0)
            self.layout.set_game_info(self.score, self.lives, self.level, self.algorithm)
            # Reset play state when algorithm changes
            self.layout.is_playing = False
            self.is_pause = True
        
        # Handle game events
        if hasattr(self.game, 'handle_event'):
            self.game.handle_event(event)
        
        # Handle keyboard events
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                self.toggle_pause()
            elif event.key == pygame.K_ESCAPE:
                self.pause_game()
            elif event.key == pygame.K_r:
                self.restart_game()
    def toggle_pause(self):
        """Toggle pause state"""
        self.is_pause = not self.is_pause
    
    def pause_game(self):
        """Pause the game"""
        self.is_pause = True
    
    def restart_game(self):
        """Restart the game with current algorithm"""
        self.game = Game(self.algorithm)
        if hasattr(self.game, 'initialize_game'):
            self.game.initialize_game()
        self.score = getattr(self.game, 'score', 0)
        self.lives = getattr(self.game, 'lives', 5)  # Game starts with 5 lives
        self.level = getattr(self.game, 'level', 0)  # Game starts with level 0
        self.game_running = True
        self.is_pause = True  # Start paused
        self.layout.is_playing = False  # Reset play state
        self.layout.set_game_info(self.score, self.lives, self.level, self.algorithm)
    
    def game_over(self):
        """Handle game over"""
        self.game_running = False
        # You can add game over logic here
    
    def on_resume(self):
        pass
    
    def on_exit(self):
        pass

