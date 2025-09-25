# =============================================================================
# NODES.PY - HỆ THỐNG NODE CHO GAME PAC-MAN
# =============================================================================
# File này chứa class Node và NodeGroup để quản lý hệ thống node
# Node đại diện cho các điểm có thể di chuyển trong maze
# NodeGroup quản lý tất cả nodes và kết nối giữa chúng

import pygame
import numpy as np
from constants import *
from objects.vector import Vector2

class Node(object) : 
    """
    Class Node đại diện cho một điểm trong maze
    - Có vị trí (x, y) trong không gian 2D
    - Có neighbors (hàng xóm) ở 4 hướng + portal
    - Có access control (ai được phép đi qua)
    - Là đơn vị cơ bản cho pathfinding
    """
    def __init__(self,x,y):
        """
        Khởi tạo node với tọa độ x, y
        Args:
            x: Tọa độ x (pixel)
            y: Tọa độ y (pixel)
        """
        self.position = Vector2(x,y)
        
        # Dictionary lưu neighbors ở 4 hướng + portal
        self.neighbors = {
            UP:None,      # Node phía trên
            DOWN:None,    # Node phía dưới
            LEFT:None,    # Node bên trái
            RIGHT:None,   # Node bên phải
            PORTAL:None   # Node portal (teleport)
        }        
        
        # Dictionary lưu danh sách entity được phép đi qua mỗi hướng
        self.access = {
            UP:[PACMAN,BLINKY,PINKY,INKY,CLYDE,FRUIT],
            DOWN:[PACMAN,BLINKY,PINKY,INKY,CLYDE,FRUIT],
            LEFT:[PACMAN,BLINKY,PINKY,INKY,CLYDE,FRUIT],
            RIGHT:[PACMAN,BLINKY,PINKY,INKY,CLYDE,FRUIT]
        }
    def __eq__(self, other):
        return isinstance(other, Node) and self.position == other.position

    def __hash__(self):
        return hash((self.position.x, self.position.y))
    
    def __lt__(self, other):
        return self.position.x ,self.position.y < other.position.x, self.position.y
    
    def denyAccess(self,direction,entity) : 
        """
        Từ chối quyền truy cập của entity theo hướng direction
        Args:
            direction: Hướng di chuyển (UP, DOWN, LEFT, RIGHT)
            entity: Entity cần từ chối quyền truy cập
        """
        if entity.name in self.access[direction] :
            self.access[direction].remove(entity.name)
    
    def allowAccess(self, direction,entity) : 
        """
        Cho phép quyền truy cập của entity theo hướng direction
        Args:
            direction: Hướng di chuyển (UP, DOWN, LEFT, RIGHT)
            entity: Entity cần cho phép quyền truy cập
        """
        if entity.name not in self.access[direction]:
            self.access[direction].append(entity.name)
    
    def positions(self):
        """
        In vị trí của node (để debug)
        """
        print(f"{self.position.x,self.position.y}")
    
    def render(self,screen):
        """
        Vẽ node lên màn hình (hiện tại không vẽ gì)
        Args:
            screen: Surface để vẽ
        """
        pass
    
class NodeGroup(object):
    """
    Class NodeGroup quản lý tất cả nodes trong maze
    - Đọc maze từ file text
    - Tạo nodes dựa trên symbols trong file
    - Kết nối nodes theo chiều ngang và dọc
    - Quản lý portal pairs và home nodes
    - Cung cấp các method để truy cập nodes
    """
    def __init__(self,level) : 
        """
        Khởi tạo NodeGroup từ file maze
        Args:
            level: Đường dẫn đến file maze (.txt)
        """
        self.level = level
        self.nodesLUT = {}  # Look-up table: (x,y) -> Node
        
        # Các symbols đại diện cho nodes trong file maze
        self.nodeSymbols = ['+','P','n','.','p','-','|'] 
        self.pathSymbols = ['.','-','|','p']  # Symbols cho đường đi
        
        # Đọc và xử lý file maze
        data = self.readMazeFile(level)
        self.createNodeTable(data)      # Tạo nodes từ symbols
        self.connectHorizontally(data)  # Kết nối theo chiều ngang
        self.connectVertically(data)    # Kết nối theo chiều dọc
        self.homekey=None               # Key của home node
            
    def readMazeFile(self,textfile) : 
        """
        Đọc file maze từ text file
        Args:
            textfile: Đường dẫn đến file maze
        Returns:
            Numpy array chứa maze data
        """
        return np.loadtxt(textfile,dtype='<U1')
    
    def createNodeTable(self,data,xoffset=0,yoffset=0) : 
        """
        Tạo nodes từ maze data
        Args:
            data: Numpy array chứa maze data
            xoffset, yoffset: Offset để dịch chuyển vị trí
        """
        for row in list(range(data.shape[0])):
            for col in list(range(data.shape[1])):
                if data[row][col] in self.nodeSymbols:
                    x,y = self.constructKey(col+xoffset,row+yoffset)
                    self.nodesLUT[(x,y)] = Node(x,y)
     
    def constructKey(self,x,y):
        """
        Tạo key cho node từ tọa độ tile
        Args:
            x, y: Tọa độ tile (không phải pixel)
        Returns:
            Tuple (x_pixel, y_pixel) làm key
        """
        return x * TILEWIDTH,y*TILEHEIGHT
    
    def connectHorizontally(self,data,xoffset=0,yoffset=0):
        for row in list(range(data.shape[0])): 
            key = None 
            for col in list(range(data.shape[1])): 
                if data[row][col] in self.nodeSymbols:
                    if key is None: 
                        key = self.constructKey(col+xoffset,row + yoffset)
                    else:
                        otherkey = self.constructKey(col+xoffset,row+yoffset) 
                        self.nodesLUT[key].neighbors[RIGHT] = self.nodesLUT[otherkey] 
                        self.nodesLUT[otherkey].neighbors[LEFT] = self.nodesLUT[key]
                        key = otherkey
                elif data[row][col] not in self.pathSymbols:
                    key = None 
    
    def connectVertically(self,data,xoffset=0,yoffset=0):
        dataT = data.transpose()
        for col in list(range(dataT.shape[0])):
            key = None
            for row in list(range(dataT.shape[1])):
                if dataT[col][row] in self.nodeSymbols:
                    if key is None:
                        key = self.constructKey(col+xoffset, row+yoffset)
                    else:
                        otherkey = self.constructKey(col+xoffset, row+yoffset)
                        self.nodesLUT[key].neighbors[DOWN] = self.nodesLUT[otherkey]
                        self.nodesLUT[otherkey].neighbors[UP] = self.nodesLUT[key]
                        key = otherkey
                elif dataT[col][row] not in self.pathSymbols:
                    key = None
                        
    def getStartTempNode(self):
        nodes = list(self.nodesLUT.values())
        return nodes[0]
    
    def setPortalPair(self,pair1,pair2) : 
        key1 = self.constructKey(*pair1)
        key2 = self.constructKey(*pair2) 
        
        if key1 in self.nodesLUT.keys() and key2 in self.nodesLUT.keys():
            self.nodesLUT[key1].neighbors[PORTAL] = self.nodesLUT[key2]
            self.nodesLUT[key2].neighbors[PORTAL] = self.nodesLUT[key1]
    
    def createHomeNodes(self,xoffset,yoffset):
        homedata = np.array([['X','X','+','X','X'],
                             ['X','X','.','X','X'],
                             ['+','X','.','X','+'],
                             ['+','.','+','.','+'],
                             ['+','X','X','X','+']])

        self.createNodeTable(homedata, xoffset, yoffset)
        self.connectHorizontally(homedata, xoffset, yoffset)
        self.connectVertically(homedata, xoffset, yoffset)
        self.homekey = self.constructKey(xoffset+2, yoffset)
        return self.homekey
    
    def connectHomeNodes(self,homekey,otherkey,direction):
        key = self.constructKey(*otherkey)
        self.nodesLUT[homekey].neighbors[direction] = self.nodesLUT[key]
        self.nodesLUT[key].neighbors[direction*-1] = self.nodesLUT[homekey]
    
    def getNodeFromPixels(self,xpixel,ypixel) : 
        if (xpixel, ypixel) in self.nodesLUT.keys():
            return self.nodesLUT[(xpixel, ypixel)]
        return None
    
    def getNodeFromTiles(self,col,row) : 
        x, y = self.constructKey(col, row)
        if (x, y) in self.nodesLUT.keys():
            return self.nodesLUT[(x, y)]
        return None
    
    def getNodeForPellet(self, col, row):
        x, y = self.constructKey(col, row)
        if (x, y) not in self.nodesLUT:
            self.nodesLUT[(x, y)] = Node(x, y)   # tạo node mới cho pellet
        return self.nodesLUT[(x, y)]
    
    def denyAccess(self,col,row,direction,entity):
        node = self.getNodeFromTiles(col, row)
        if node is not None:
            node.denyAccess(direction, entity)
    
    def allowAccess(self,col,row,direction,entity):
        node = self.getNodeFromTiles(col, row)
        if node is not None:
            node.allowAccess(direction, entity)
    
    def denyAccessList(self,col,row,direction,entities):
        for entity in entities:
            self.denyAccess(col, row, direction, entity)
    
    def allowAccessList(self,col,row,direction,entities) : 
        for entity in entities:
            self.allowAccess(col, row, direction, entity)
    
    def denyHomeAccess(self,entity):
        self.nodesLUT[self.homekey].denyAccess(DOWN, entity)
    
    def allowHomeAccess(self,entity):
        self.nodesLUT[self.homekey].allowAccess(DOWN, entity)
    
    def denyHomeAccessList(self,entities):
        for entity in entities:
            self.denyHomeAccess(entity)
    
    def allowHomeAccessList(self,entities):
        for entity in entities:
            self.allowHomeAccess(entity)
    
    def render(self,screen):
        for node in self.nodesLUT.values():
            node.render(screen)
            
            