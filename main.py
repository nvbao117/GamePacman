import pygame 
from statemachine import StateMachine
from states.menu_state import MenuState
import sys

class App: 
    def __init__(self):
        pygame.init()
        info = pygame.display.Info()   # gọi ở đây, sau init
        self.WIDTH, self.HEIGHT = info.current_w, info.current_h

        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.FULLSCREEN)
        pygame.display.set_caption("Pac-Man Arcade")
        self.clock = pygame.time.Clock()
        self.running = True

        self.state_machine = StateMachine(MenuState,self)

    def run(self): 
        while self.running:
            dt = self.clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                if self.state_machine.current_state:
                    self.state_machine.current_state.handle_events(event)

            # Cập nhật state machine
            self.state_machine.update()
            
            if self.state_machine.current_state:
                self.state_machine.current_state.logic()
                self.state_machine.current_state.draw(self.screen)
            else:
                # Fallback: fill screen with black if no state
                self.screen.fill((0, 0, 0))

            pygame.display.flip()
            
            # Remove debug timeout

        pygame.quit()
        sys.exit()
if __name__ == "__main__":
    app = App()
    app.run()