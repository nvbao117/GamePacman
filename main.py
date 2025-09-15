import sys 
import pygame 
from config import *
from game.game import Game
from ui.button import Button
from ui.menu import Menu


class App : 
    def __init__(self):
        pygame.init()
        info = pygame.display.Info()
        self.WIDTH, self.HEIGHT = info.current_w, info.current_h
        print(self.WIDTH,self.HEIGHT)
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT), pygame.FULLSCREEN)
        self.user_input = None 
        self.mouse_input = None 
        self.bg = pygame.transform.scale(pygame.image.load(BG_MENU).convert_alpha(),(self.WIDTH,self.HEIGHT))        
        self.menu = Menu(self)
        
    def draw(self):
        self.screen.blit(self.bg,(0,0))
        self.menu.render()
        
    def update(self):
        self.menu.update()
    def run(self):
        while True:
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.menu.eventHandling(e)
            self.user_input = pygame.key.get_pressed()
            self.mouse_input = pygame.mouse.get_pressed()
            
            self.update()
            self.draw()
            pygame.display.flip()

if __name__ =='__main__':
    game = Game()
    game.startGame()
    while True:
        game.update()