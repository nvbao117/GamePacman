import pygame
from pygame.locals import * 
from config import *
from core.vector import Vector2
from game.entity.entity import Entity
from ui.sprites import PacmanScriptes

class Pacman(Entity):
    def __init__(self,node):
        Entity.__init__(self,node) 
        self.name = PACMAN
        self.color = YELLOW
        self.direction = LEFT 
        self.setBetweenNodes(LEFT) 
        self.alive = True
        self.sprites = PacmanScriptes(self)
            
    # Khôi phục pacman về trạng thái ban đầu 
    def reset(self):
        Entity.reset(self) 
        self.direction = LEFT
        self.setBetweenNodes = LEFT
        self.alive = True
        self.image = self.sprites.getStartImage()
        self.sprites.reset()
    
    # pacman bị tiêu diệt
    def die(self):
        self.alive = False
        self.direction = STOP 
        
    # cập nhật trạng thái pacman 
    def update(self,dt):
        self.sprites.update(dt) 
        self.position += self.directions[self.direction]*self.speed*dt
        direction = self.getValidKey()
        if self.overshotTarget():
            self.node = self.target
            if self.node.neighbors[PORTAL] is not None : 
                self.node = self.node.neighbors[PORTAL] 
            self.target = self.getNewTarget(direction) 
            if self.target is not self.node : 
                self.direction = direction
            else : 
                self.target = self.getNewTarget(self.direction)
            
            if self.target is self.node : 
                self.direction = STOP 
            self.setPosition()
        else:
            if self.oppositeDirection(direction):
                self.reverseDirection() 
          
    #xác định hướng di chuyển   
    def getValidKey(self):
        key_pressed = pygame.key.get_pressed()
        if key_pressed[K_UP] : 
            return UP 
        if key_pressed[K_DOWN] : 
            return DOWN
        if key_pressed[K_LEFT]:
            return LEFT
        if key_pressed[K_RIGHT]:
            return RIGHT
        return STOP
    
    # kiểm tra ăn pellet 
    def eatPellets(self,pelletList):
        for pellet in pelletList : 
            if self.collideCheck(pellet) : 
                return pellet
        return None 
    
    #Kiểm tra va chạm với ghost
    def collideGhost(self,ghost):
        return self.collideCheck(ghost) 

    # kiểm tra va chạm 
    def collideCheck(self,other):
        d = self.position - other.position 
        dSquared = d.magnitudeSquared()
        rSquared = (self.collideRadius + other.collideRadius)**2
        if dSquared <= rSquared:
            return True
        return False