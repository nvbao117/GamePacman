import pygame
import numpy as np 
from constants import *
from objects.vector import Vector2
from objects.nodes import NodeGroup

class Pellet(object):
    def __init__(self,row,column,node=None):
        self.name = PELLET
        self.position = Vector2(column*TILEWIDTH,row*TILEHEIGHT)
        self.node = node 
        self.color = WHITE
        self.radius = int(2*TILEWIDTH/16)
        self.collideRadius = 10
        self.points = 10 
        self.visible = True 
        
    
    def render (self,screen) : 
        if self.visible:
            adjust = Vector2(TILEWIDTH,TILEHEIGHT)/2
            p = self.position + adjust
            pygame.draw.circle(screen,self.color,p.asInt(),self.radius)

class PowerPellet(Pellet):
    def __init__(self,row,column,node=None):
        super().__init__(row,column,node)
        self.name = POWERPELLET
        self.radius = int(8*TILEWIDTH/16)
        self.points = 50
        self.flashTime = 0.2
        self.timer = 0
        
    def update(self, dt):
        pass
        # self.timer += dt
        # if self.timer >= self.flashTime:
        #     self.visible = not self.visible
        #     self.timer = 0
            
class PelletGroup(object):
    def __init__(self, pelletfile, nodes: NodeGroup, few_pellets_mode=False, few_pellets_count=20):
        self.pelletList = []
        self.powerpellets = []
        self.numEaten = 0
        self.few_pellets_mode = few_pellets_mode
        self.few_pellets_count = few_pellets_count
        self.total_pellets = 0
        self.createPelletList(pelletfile, nodes)
    
    def update(self, dt):
        for powerpellet in self.powerpellets:
            powerpellet.update(dt)
            
    def createPelletList(self, pelletfile, nodes: NodeGroup):
        data = self.readPelletfile(pelletfile)
        all_pellets = []  # Tạm thời lưu tất cả pellets
        
        for row in range(data.shape[0]):
            for col in range(data.shape[1]):
                if data[row][col] in ['.', '+']:
                    node = nodes.getNodeForPellet(col, row)
                    pellet = Pellet(row, col, node)
                    all_pellets.append(pellet)

                elif data[row][col] in ['P', 'p']:
                    node = nodes.getNodeForPellet(col, row)
                    pp = PowerPellet(row, col, node)
                    all_pellets.append(pp)
                    self.powerpellets.append(pp)
        
        # Nếu chế độ few pellets được bật, chỉ chọn một số pellets ngẫu nhiên
        if self.few_pellets_mode:
            import random
            # Đảm bảo giữ lại tất cả power pellets
            regular_pellets = [p for p in all_pellets if p.name == PELLET]
            
            # Tính số pellets thường cần chọn
            if len(regular_pellets) > self.few_pellets_count:
                # fixed_indices = [0, 10, 20, 30, 100, 150, 200]  # Vị trí cố định
                # selected_regular = [regular_pellets[i] for i in fixed_indices if i < len(regular_pellets)]
                selected_regular = random.sample(regular_pellets, self.few_pellets_count)
            else:
                selected_regular = regular_pellets
            
            self.pelletList = selected_regular
        else:
            self.pelletList = all_pellets
        
        self.total_pellets = len(self.pelletList)
        
    def readPelletfile(self, textfile):
        return np.loadtxt(textfile, dtype='<U1')
    
    def isEmpty(self):
        return len(self.pelletList) == 0

    def render(self, screen):
        for pellet in self.pelletList:
            pellet.render(screen)