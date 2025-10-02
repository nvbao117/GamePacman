# =============================================================================
# MODES.PY - HỆ THỐNG QUẢN LÝ CHẾ ĐỘ CỦA GHOST
# =============================================================================
# File này chứa hệ thống quản lý các chế độ khác nhau của ghost
# bao gồm Scatter, Chase, Freight, và Spawn modes

from constants import *

class MainMode(object):
    """
    Class quản lý chế độ chính của ghost (Scatter và Chase)
    - Tự động chuyển đổi giữa Scatter và Chase theo thời gian
    - Scatter: Ghost chạy về góc (7 giây)
    - Chase: Ghost đuổi theo Pac-Man (20 giây)
    """
    def __init__(self):
        self.timer = 0 
        self.scatter()  # Bắt đầu với chế độ Scatter
    
    def update(self, dt):
        """
        Cập nhật chế độ chính mỗi frame
        Args:
            dt: Delta time
        """
        self.timer += dt
        if self.timer >= self.time: 
            if self.mode is SCATTER: 
                # Chuyển từ Scatter sang Chase
                self.chase()
            elif self.mode is CHASE: 
                # Chuyển từ Chase sang Scatter
                self.scatter()
    
    def scatter(self):
        """
        Chuyển sang chế độ Scatter (ghost chạy về góc)
        - Thời gian: 7 giây
        """
        self.mode = SCATTER
        self.time = 7 
        self.timer = 0 
    
    def chase(self):
        """
        Chuyển sang chế độ Chase (ghost đuổi theo Pac-Man)
        - Thời gian: 20 giây
        """
        self.mode = CHASE
        self.time = 15
        self.timer = 0 
    
class ModeController(object):
    """
    Controller quản lý tất cả chế độ của ghost
    - Quản lý chế độ chính (Scatter/Chase)
    - Quản lý chế độ đặc biệt (Freight/Spawn)
    - Tự động chuyển đổi giữa các chế độ
    """
    def __init__(self, entity):
        """
        Khởi tạo mode controller cho entity
        Args:
            entity: Entity cần quản lý chế độ (thường là Ghost)
        """
        self.timer = 0 
        self.time = None
        self.mainmode = MainMode()  # Chế độ chính
        self.current = self.mainmode.mode  # Chế độ hiện tại
        self.entity = entity
    
    def update(self, dt):
        """
        Cập nhật mode controller mỗi frame
        Args:
            dt: Delta time
        """
        # Cập nhật chế độ chính
        self.mainmode.update(dt) 
        
        if self.current is FREIGHT:
            # Xử lý chế độ Freight (ghost bị ăn được)
            self.timer += dt
            if self.timer >= self.time: 
                self.time = None 
                self.entity.normalMode()  # Quay về chế độ bình thường
                self.current = self.mainmode.mode
        elif self.current in [SCATTER, CHASE]:
            # Đồng bộ với chế độ chính
            self.current = self.mainmode.mode
            
        if self.current is SPAWN: 
            # Xử lý chế độ Spawn (ghost quay về nhà)
            if self.entity.node == self.entity.spawnNode: 
                self.entity.normalMode()
                self.current = self.mainmode.mode 
                
    def setFreightMode(self):
        """
        Chuyển sang chế độ Freight (ghost bị ăn được)
        - Được gọi khi Pac-Man ăn power pellet
        - Thời gian: 7 giây
        """
        if self.current in [SCATTER, CHASE]: 
            self.timer = 0 
            self.time = 7 
            self.current = FREIGHT
        elif self.current is FREIGHT: 
            # Nếu đã ở chế độ Freight, reset timer
            self.timer = 0 
            
    def setSpawnMode(self):
        """
        Chuyển sang chế độ Spawn (ghost quay về nhà)
        - Được gọi khi ghost bị ăn
        - Chỉ chuyển được từ chế độ Freight
        """
        if self.current is FREIGHT:
            self.current = SPAWN 