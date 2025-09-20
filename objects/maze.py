# =============================================================================
# MAZE.PY - HỆ THỐNG QUẢN LÝ MAZE CHO GAME PAC-MAN
# =============================================================================
# File này chứa các class quản lý maze và cấu hình của từng level
# Bao gồm vị trí portal, home của ghost, và các hạn chế di chuyển

from constants import *
from objects.nodes import NodeGroup

class Mazebase(object):
    """
    Base class cho tất cả maze trong game
    - Định nghĩa cấu trúc chung của maze
    - Quản lý portal pairs, home offset, và ghost restrictions
    """
    def __init__(self):
        self.portalPairs = {}  # Dictionary chứa các cặp portal
        self.homeoffset = (0, 0)  # Offset của home area
        # Dictionary chứa các node mà ghost không được truy cập
        self.ghostNodeDeny = {UP: (), DOWN: (), LEFT: (), RIGHT: ()} 
    
    def setPortalPairs(self, nodes: NodeGroup):
        """
        Thiết lập các portal pairs trong node group
        Args:
            nodes: NodeGroup cần thiết lập portal
        """
        for pair in list(self.portalPairs.values()): 
            nodes.setPortalPair(*pair)
    
    def connectHomeNodes(self, nodes: NodeGroup):
        """
        Kết nối home nodes với maze chính
        Args:
            nodes: NodeGroup cần kết nối
        """
        key = nodes.createHomeNodes(*self.homeoffset) 
        nodes.connectHomeNodes(key, self.homenodeconnectLeft, LEFT) 
        nodes.connectHomeNodes(key, self.homenodeconnectRight, RIGHT)
    
    def addOffset(self, x, y):
        """
        Thêm offset vào tọa độ
        Args:
            x, y: Tọa độ gốc
        Returns:
            Tuple (x + offset_x, y + offset_y)
        """
        return x + self.homeoffset[0], y + self.homeoffset[1]
    
    def denyGhostsAccess(self, ghosts, nodes: NodeGroup):
        """
        Cấm ghost truy cập vào các node nhất định
        Args:
            ghosts: Danh sách ghost cần cấm
            nodes: NodeGroup cần áp dụng hạn chế
        """
        # Cấm truy cập vào home area
        nodes.denyAccessList(*(self.addOffset(2, 3) + (LEFT, ghosts)))
        nodes.denyAccessList(*(self.addOffset(2, 3) + (LEFT, ghosts)))
        
        for direction in list(self.ghostNodeDeny.keys()) : 
            for values in self.ghostNodeDeny[direction] : 
                nodes.denyAccessList(*(values + (direction,ghosts)))

class Maze1(Mazebase):
    """
    Maze level 1 - Maze cơ bản
    - 1 portal pair ở giữa màn hình
    - Home area ở vị trí (11.5, 14)
    - Pac-Man bắt đầu ở (15, 26)
    """
    def __init__(self):
        Mazebase.__init__(self) 
        self.name = "maze1"
        # Portal pair: trái phải ở giữa màn hình
        self.portalPairs = {0: ((0, 17), (27, 17))}
        self.homeoffset = (11.5, 14)  # Vị trí home area
        self.homenodeconnectLeft = (12, 14)   # Node kết nối trái
        self.homenodeconnectRight = (15, 14)  # Node kết nối phải
        self.pacmanStart = (15, 26)  # Vị trí bắt đầu của Pac-Man
        self.fruitStart = (9, 20)    # Vị trí xuất hiện fruit
        
        # Các node mà ghost không được truy cập
        self.ghostNodeDeny = {
            UP: ((12, 14), (15, 14), (12, 26), (15, 26)),
            LEFT: (self.addOffset(2, 3),),
            RIGHT: (self.addOffset(2, 3),)
        }

class Maze2(Mazebase):
    """
    Maze level 2 - Maze phức tạp hơn
    - 2 portal pairs: trên và dưới
    - Home area rộng hơn
    - Pac-Man bắt đầu ở vị trí khác
    """
    def __init__(self):
        Mazebase.__init__(self) 
        self.name = "maze2"
        # 2 portal pairs: trên và dưới màn hình
        self.portalPairs = {
            0: ((0, 4), (27, 4)),    # Portal trên
            1: ((0, 26), (27, 26))   # Portal dưới
        }
        self.homeoffset = (11.5, 14)  # Vị trí home area
        self.homenodeconnectLeft = (9, 14)   # Node kết nối trái
        self.homenodeconnectRight = (18, 14) # Node kết nối phải
        self.pacmanStart = (16, 26)  # Vị trí bắt đầu của Pac-Man
        self.fruitStart = (11, 20)   # Vị trí xuất hiện fruit
        
        # Các node mà ghost không được truy cập
        self.ghostNodeDeny = {
            UP: ((9, 14), (18, 24), (11, 23), (16, 23)),
            LEFT: (self.addOffset(2, 3),),
            RIGHT: (self.addOffset(2, 3),)
        }
    
class MazeData(object):
    """
    Class quản lý dữ liệu maze cho toàn bộ game
    - Chứa dictionary các maze khác nhau
    - Load maze theo level
    - Hỗ trợ cycle qua các maze
    """
    def __init__(self):
        self.obj = None  # Maze object hiện tại
        # Dictionary chứa các maze class
        self.mazedict = {0: Maze1, 1: Maze2}
    
    def loadMaze(self, level):
        """
        Load maze theo level
        Args:
            level: Level cần load (0, 1, 2, ...)
        """
        # Cycle qua các maze có sẵn
        self.obj = self.mazedict[level % len(self.mazedict)]()
    