import pygame 
from pygame.locals import * 
from random import randint
from core.vector import Vector2
from config import *

class Entity(object):
    def __init__(self,node):
        self.name = None
        self.directions = {
            UP:Vector2(0,-1) , 
            DOWN:Vector2(0,1) ,
            LEFT:Vector2(-1,0),
            RIGHT:Vector2(1,0),
            STOP:Vector2()
        }
        self.direction = STOP
        self.setSpeed(100)
        self.radius = 10 
        self.collideRadius = 5 
        self.color = WHITE
        self.visible = True 
        self.disablePortal = False
        self.goal = None 
        self.directionMethod = self.randomDirection 
        self.setStartNode(node) 
        self.image = None 
             
    def setPosition(self) : 
        self.position = self.node.position.copy() 
        
    #cập nhật vị trí entity 
    def update(self,dt) : 
        self.position += self.directions[self.direction]*self.speed*dt
        
        if self.overshotTarget():
            self.node = self.target 
            directions = self.validDirections()
            direction = self.directionMethod(directions)
            if not self.disablePortal:
                if self.node.neighbors[PORTAL] is not None : 
                    self.node = self.node.neighbors[PORTAL] 
            self.target = self.getNewTarget(direction) 
            if self.target is not self.node :
                self.direction = direction
            else:
                self.target = self.getNewTarget(self.direction)
                
            self.setPosition()
    
    #kiểm tra hướng di chuyển hợp lệ     
    def validDirection(self,direction) : 
        if direction is not STOP:
            if self.name in self.node.access[direction]:
                if self.node.neighbors[direction] is not None:
                    return True
        return False
    
    #Lấy nút mục tiêu mới theo direction 
    def getNewTarget(self,direction):
        if self.validDirection(direction) : 
            return self.node.neighbors[direction] 
        return self.node 
    
    #Kiểm tra xem có vượt quá target không 
    def overshotTarget(self):
        if self.target is not None :
            vec1 = self.target.position - self.node.position 
            vec2 = self.position - self.node.position 
            node2Target = vec1.magnitudeSquared()
            node2Self = vec2.magnitudeSquared()
            return node2Self >= node2Target
        return False
    
    #Đảo ngược hướng di chuyển , đổi target
    def reverseDirection(self):
        self.direction *= -1 
        temp = self.node 
        self.node = self.target
        self.target = temp 
    
    # Kiểm tra xem một hướng có ngược hướng với hiện tại không
    def oppositeDirection(self,direction):
        if direction is not STOP : 
            if direction == self.direction * - 1  : 
                return True 
        return False 
    
    # Lấy danh sách các hướng hợp lệ 
    def validDirections(self):
        directions = [] 
        for key in [UP,DOWN,LEFT,RIGHT]  :
            if self.validDirection(key) : 
                if key != self.direction * -1 :
                    directions.append(key)
        if len(directions) == 0 : 
            directions.append(self.direction * -1) 
        return directions
    
    # random hướng 
    def randomDirection(self, directions):
        return directions[randint(0,len(directions) - 1 )]
    
    # Chọn hướng gần nhất với mục tiêu 
    def goalDirection(self,directions) : 
        distances = [] 
        for direction in directions  : 
            vec = self.node.position + self.directions[direction]*TILEWIDTH - self.goal
            distances.append(vec.magnitudeSquared())
        index = distances.index(min(distances)) 
        return directions[index] 
    
    # Đặt nút khởi đầu 
    def setStartNode(self,node) : 
        self.node = node 
        self.startNode = node 
        self.target = node 
        self.setPosition()
    
    # Đặt vị trí giữa 2 nút dựa trên hướng
    def setBetweenNodes(self,direction) : 
        if self.node.neighbors[direction] is not None :
            self.target = self.node.neighbors[direction]
            self.position = (self.node.position + self.target.position) / 2.0 
    
    # khôi phục trạng thái ban đầu 
    def reset(self):
        self.setStartNode(self.startNode)
        self.direction = STOP
        self.speed = 100 
        self.visible = True 
    
    # đặt tốc độ di chuyển 
    def setSpeed(self,speed):
        self.speed = speed * TILEWIDTH/16
     
    # vẽ lên màn hình 
    def render(self,screen) : 
        if self.visible : 
            if self.image is not None : 
                adjust = Vector2(TILEWIDTH,TILEHEIGHT) / 2 
                p = self.position - adjust
                screen.blit(self.image, p.asTuple())
            else : 
                p = self.position.asInt()
                pygame.draw.circle(screen,self.color,p,self.radius)