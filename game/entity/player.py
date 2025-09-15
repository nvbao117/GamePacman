import pygame
from pygame.locals import * 
from config import *
from core.vector import Vector2
from game.entity.entity import Entity
from ui.sprites import PacmanScriptes
from game.entity.pellets import PelletGroup
from core.nodes import Node
from collections import deque
from ai.bfs import bfs
import sys
class Pacman(Entity):
    def __init__(self,node):
        Entity.__init__(self,node) 
        self.name = PACMAN
        self.color = YELLOW
        self.direction = LEFT 
        self.setBetweenNodes(LEFT) 
        self.alive = True
        self.sprites = PacmanScriptes(self)
        self.path = []
        
        
    # Khôi phục pacman về trạng thái ban đầu 
    def reset(self):
        Entity.reset(self) 
        self.direction = LEFT
        self.setBetweenNodes(LEFT)
        self.alive = True
        self.image = self.sprites.getStartImage()
        self.sprites.reset()
        self.target_pellet = None
        self.path = []
    
    def set_path(self,path):
        self.path = path[1:] 
    
    def get_direction(self,from_node, to_node):
        for direction, neighbor in from_node.neighbors.items():
            if neighbor == to_node:
                return direction
        return STOP
    
    # pacman bị tiêu diệt
    def die(self):
        self.alive = False
        self.direction = STOP 

    def move_along_path(self):
        if not self.path:
            return STOP
        next_node = self.path[0]        
        direction = self.get_direction(self.node, next_node)
        if self.overshotTarget() and self.node == next_node:
            self.path.pop(0)
        return direction
    
    # cập nhật trạng thái pacman 
    def update(self, dt, pelletGroup=None, auto=False):
        self.sprites.update(dt) 
        self.position += self.directions[self.direction] * self.speed * dt
        
        if auto and pelletGroup is not None and pelletGroup.pelletList:
            endNode = Node(80,64)
            path = None
            if any(pellet.node == endNode for pellet in pelletGroup.pelletList):
                path = bfs(self.node, endNode, pelletGroup)
            else :
                print("NGu")
            if path:
                self.set_path(path)
            else:
                print("BFS returned None")
            
            direction = self.move_along_path()
        else:
            direction = self.getValidKey()              

        if self.overshotTarget():
            self.node = self.target
            
            if self.node.neighbors[PORTAL] is not None: 
                self.node = self.node.neighbors[PORTAL] 
            self.target = self.getNewTarget(direction) 
            if self.target is not self.node: 
                self.direction = direction
            else: 
                self.target = self.getNewTarget(self.direction)
            if self.target is self.node: 
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