# =============================================================================
# ANIMATION.PY - HỆ THỐNG ANIMATION CHO GAME PAC-MAN
# =============================================================================
# File này chứa class Animator để quản lý animation
# Hỗ trợ frame-based animation với tốc độ và loop control

from constants import *

class Animator(object):
    """
    Class Animator quản lý animation dựa trên frames
    - Chuyển đổi giữa các frames theo tốc độ đã định
    - Hỗ trợ loop animation hoặc chạy một lần
    - Có thể reset và kiểm tra trạng thái hoàn thành
    """
    def __init__(self,frames=[],speed = 20 , loop=True):
        """
        Khởi tạo Animator
        Args:
            frames: List các frames (images) cho animation
            speed: Tốc độ animation (frames per second)
            loop: Có lặp lại animation không
        """
        self.frames = frames
        self.current_frame = 0 
        self.speed = speed
        self.loop = loop
        self.dt = 0 
        self.finished = False
    
    def reset(self):
        """
        Reset animation về frame đầu tiên
        """
        self.current_frame = 0 
        self.finished = False
    
    def update(self,dt):
        """
        Cập nhật animation
        Args:
            dt: Delta time (thời gian giữa 2 frame)
        Returns:
            Frame hiện tại của animation
        """
        if not self.finished:
            self.nextFrame(dt)
        if self.current_frame == len(self.frames):
            if self.loop:
                self.current_frame = 0 
            else:
                self.finished = True
                self.current_frame -= 1 
        
        return self.frames[self.current_frame]
    
    def nextFrame(self,dt):
        """
        Chuyển sang frame tiếp theo dựa trên tốc độ
        Args:
            dt: Delta time
        """
        self.dt += dt 
        if self.dt >= (1.0/self.speed):
            self.current_frame += 1
            self.dt = 0 