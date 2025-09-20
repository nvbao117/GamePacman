import pygame 

from pygame.locals import * 
from constants import *
from objects.vector import Vector2
from objects.entity import Entity
from objects.modes import ModeController
from ui.sprites import FruitSprites

class Fruit(Entity):
    def __init__(self,node,level= 0 ):
        Entity.__init__(self,node) 
        self.name = FRUIT 
        self.color = GREEN 
        self.lifespan = 5 
        self.timer = 0 
        self.destroy = False
        self.points = 100 + level*20 
        self.setBetweenNodes(RIGHT)
        self.sprites = FruitSprites(self,level)
    
    def update(self,dt):
        self.timer += dt 
        if self.timer >= self.lifespan:
            self.destroy = True