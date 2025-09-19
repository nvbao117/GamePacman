import sys 
import pygame 
from config import *
from game.game import Game
from ui.button import Button
from ui.menu import Menu


class App:
    def __init__(self):
        pygame.init()
        info = pygame.display.Info()
        self.WIDTH, self.HEIGHT = info.current_w, info.current_h
        print(f"Screen resolution: {self.WIDTH}x{self.HEIGHT}")
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Pac-Man Arcade")
        
        self.user_input = None 
        self.mouse_input = None 
        self.clock = pygame.time.Clock()
        
        # Game states
        self.current_state = "MENU"  # MENU, GAME, PAUSED
        self.running = True
        
        # Load background
        try:
            self.bg = pygame.transform.scale(pygame.image.load(BG_MENU).convert_alpha(), (self.WIDTH, self.HEIGHT))
        except:
            # Fallback if image not found
            self.bg = pygame.Surface((self.WIDTH, self.HEIGHT))
            self.bg.fill((0, 0, 50))
            
        # Initialize menu
        self.menu = Menu(self)
        self.game = None
        
        # Bind menu callbacks
        self.bind_menu_callbacks()
        
    def bind_menu_callbacks(self):
        """Bind menu button callbacks to app methods"""
        # Override menu's start_game method
        self.menu.start_game = self.start_game
        
        # Update button callbacks in menu
        for scene_components in self.menu.UIComponents.values():
            for component in scene_components:
                if hasattr(component, 'onclick') and component.onclick:
                    # Check if it's the start game button
                    if hasattr(component, 'text') and "START" in str(component.text).upper():
                        component.onclick = [self.start_game]
                    elif hasattr(component, 'text') and "EXIT" in str(component.text).upper():
                        component.onclick = [self.quit_game]
        
    def start_game(self):
        """Start the game with selected algorithm"""
        try:
            print(f"Starting game with algorithm: {self.menu.selected_algorithm}")
            self.game = Game(self.menu.selected_algorithm)
            self.game.app = self  # Pass reference to app
            self.current_state = "GAME"
            
            # Initialize game without starting its own loop
            self.game.initialize_game()  # This should be a new method in Game class
            
        except Exception as e:
            print(f"Error starting game: {e}")
            self.current_state = "MENU"  # Return to menu on error
    
    def return_to_menu(self):
        """Return to menu from game"""
        self.current_state = "MENU"
        self.game = None
        print("Returned to menu")
    
    def quit_game(self):
        """Quit the entire application"""
        self.running = False
        
    def handle_events(self):
        """Handle all pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
                
            # Global key shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.current_state == "GAME":
                        self.return_to_menu()
                    else:
                        self.running = False
                        return
                elif event.key == pygame.K_F11:
                    # Toggle fullscreen (optional)
                    pass
            
            # Pass events to current state
            if self.current_state == "MENU":
                self.menu.eventHandling(event)
            elif self.current_state == "GAME" and self.game:
                self.game.handle_event(event)  # Game should have this method
    
    def update(self):
        """Update current state"""
        if self.current_state == "MENU":
            self.menu.update()
        elif self.current_state == "GAME" and self.game:
            # Update game and check if it should return to menu
            game_result = self.game.update()
            
            # If game signals it should end, return to menu
            if game_result == "QUIT" or not self.game.running:
                self.return_to_menu()
                
        # Update input states
        self.user_input = pygame.key.get_pressed()
        self.mouse_input = pygame.mouse.get_pressed()
    
    def draw(self):
        """Draw current state"""
        if self.current_state == "MENU":
            self.screen.blit(self.bg, (0, 0))
            self.menu.render()
        elif self.current_state == "GAME" and self.game:
            self.game.draw(self.screen)  # Game should draw to provided screen
            
        # Add FPS display (optional, for debugging)
        if hasattr(self, 'show_fps') and self.show_fps:
            fps = self.clock.get_fps()
            font = pygame.font.Font(None, 36)
            fps_text = font.render(f"FPS: {fps:.1f}", True, (255, 255, 255))
            self.screen.blit(fps_text, (10, 10))
    
    def run(self):
        """Main application loop"""
        print("Starting Pac-Man Arcade...")
        
        while self.running:
            # Handle events
            self.handle_events()
            
            if not self.running:
                break
            
            # Update game state
            self.update()
            
            # Draw everything
            self.draw()
            
            # Update display
            pygame.display.flip()
            
            # Maintain frame rate
            self.clock.tick(60)  # 60 FPS
        
        # Cleanup
        self.cleanup()
    
    def cleanup(self):
        """Clean up resources before quitting"""
        print("Cleaning up...")
        if self.game:
            self.game.cleanup()  # Game should have cleanup method
        pygame.quit()
        sys.exit(0)


if __name__ == '__main__':
    try:
        app = App()
        app.run()
    except KeyboardInterrupt:
        print("\nGame interrupted by user")
        pygame.quit()
        sys.exit(0)
    except Exception as e:
        print(f"Unexpected error: {e}")
        pygame.quit()
        sys.exit(1)