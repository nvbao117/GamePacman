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
        self.locked_target_node = None
        
        
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
        self.locked_target_node = None
    
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
        if direction == STOP:
            # Path invalid (neighbor mapping missing); drop and force replanning
            self.path = []
            return STOP
        if self.overshotTarget() and self.node == next_node:
            self.path.pop(0)
        return direction
    
    # cập nhật trạng thái pacman 
    def update(self, dt, pelletGroup=None, auto=False):
        self.sprites.update(dt) 
        self.position += self.directions[self.direction] * self.speed * dt
        
        # Default: keep current direction until we reach the next node
        direction = self.direction if auto else self.getValidKey()

        if self.overshotTarget():
            self.node = self.target
            
            if self.node.neighbors[PORTAL] is not None: 
                self.node = self.node.neighbors[PORTAL] 
            # At node: decide next direction
            if auto and pelletGroup is not None and pelletGroup.pelletList:
                # Maintain a locked pellet target until it's eaten or missing
                if self.locked_target_node is None or not any(p.node == self.locked_target_node for p in pelletGroup.pelletList):
                    self.locked_target_node = None
                    path = bfs(self.node, self.node, pelletGroup)
                    if path and len(path) > 0:
                        self.locked_target_node = path[-1]
                if not self.path:
                    path = bfs(self.node, self.locked_target_node, pelletGroup)
                    if path:
                        self.set_path(path)
                # Choose next step from the path
                direction = self.move_along_path()
                if direction == STOP or self.getNewTarget(direction) is self.node:
                    # Replan if needed
                    self.path = []
                    path = bfs(self.node, self.locked_target_node, pelletGroup)
                    if path:
                        self.set_path(path)
                        direction = self.move_along_path()
            else:
                direction = self.getValidKey()

            self.target = self.getNewTarget(direction) 
            if self.target is not self.node: 
                self.direction = direction
            else: 
                self.target = self.getNewTarget(self.direction)
            if self.target is self.node: 
                self.direction = STOP             
            self.setPosition()
        else:
            # Avoid oscillation in auto mode by not reversing mid-edge
            if not auto and self.oppositeDirection(direction):
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