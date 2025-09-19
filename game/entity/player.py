import pygame
from pygame.locals import * 
from config import *
from core.vector import Vector2
from game.entity.entity import Entity
from ui.sprites import PacmanScriptes
from game.entity.pellets import PelletGroup
from core.nodes import Node
from collections import deque
from ai.a_star import a_star
import sys
class Pacman(Entity):
    def __init__(self,node):
        Entity.__init__(self,node) 
        self.name = PACMAN
        self.color = YELLOW
        self.direction =  LEFT
        self.setBetweenNodes(LEFT) 
        self.alive = True
        self.sprites = PacmanScriptes(self)
        self.path = []
        self.locked_target_node = None
        self.previous_node = None

        
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
        self.previous_node = None
    
    def set_path(self,path):
        self.path = path[1:] 
    
    def get_direction(self,from_node, to_node):
        for direction, neighbor in from_node.neighbors.items():
            if neighbor == to_node:
                return direction
        return STOP
    
    def die(self):
        self.alive = False
        self.direction = STOP 

    def move_along_path(self):
        if not self.path:
            return STOP
        # Avoid immediate backtracking ping-pong: if first step is previous_node
        if self.previous_node is not None and len(self.path) >= 1 and self.path[0] == self.previous_node:
            if len(self.path) > 1:
                # Prefer skipping the back step if there are other planned steps
                self.path.pop(0)
            else:
                # Dead-end: allow a single reverse step to get out instead of STOP
                direction_back = self.get_direction(self.node, self.previous_node)
                return direction_back if direction_back != STOP else STOP
        next_node = self.path[0]
        direction = self.get_direction(self.node, next_node)
        if direction == STOP:
            self.path = []
            return STOP
        # Do not allow reversing direction mid-edge when auto
        opposite = self.oppositeDirection(direction)
        if opposite and self.direction == opposite:
            return self.direction
        if self.overshotTarget() and self.node == next_node:
            self.path.pop(0)
        return direction
    
    def update_ai(self,dt,pelletGroup=None , auto = False):
        self.sprites.update(dt) 
        self.position += self.directions[self.direction] * self.speed * dt
        direction = self.direction if auto else self.getValidKey()

        if self.overshotTarget():
            # arrived at target node
            self.previous_node = self.node
            self.node = self.target
            
            if self.node.neighbors[PORTAL] is not None: 
                self.node = self.node.neighbors[PORTAL] 
            if auto and pelletGroup is not None and pelletGroup.pelletList:
                # Sử dụng BFS cải tiến với ưu tiên hướng hiện tại
                priority_direction = self.direction if self.direction != STOP else None
                
                if self.locked_target_node is None or not any(p.node == self.locked_target_node for p in pelletGroup.pelletList):
                    self.locked_target_node = None
                    path = a_star(self.node, None, pelletGroup)  # Tìm pellet gần nhất
                    if path and len(path) > 0:
                        self.locked_target_node = path[-1]
                
                if not self.path:
                    path = a_star(self.node, self.locked_target_node, pelletGroup)
                    if path:
                        self.set_path(path)
                
                # Choose next step from the path
                direction = self.move_along_path()
                # If next step blocked or invalid, try to consume more of the path before replanning
                attempts = 0
                while (direction == STOP or self.getNewTarget(direction) is self.node) and attempts < 2:
                    if self.path:
                        # drop this step and try next
                        self.path.pop(0)
                        direction = self.move_along_path()
                    else:
                        break
                    attempts += 1
                if direction == STOP or self.getNewTarget(direction) is self.node:
                    # Replan if needed
                    self.path = []
                    path = a_star(self.node, self.locked_target_node, pelletGroup)
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
            if not auto and self.oppositeDirection(direction):
                self.reverseDirection()
    # cập nhật trạng thái pacman 
    def update(self, dt):
        self.sprites.update(dt) 
        self.position += self.directions[self.direction] * self.speed * dt
        direction =  self.getValidKey()

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