# =============================================================================
# VECTOR.PY - CLASS VECTOR2D CHO GAME PAC-MAN
# =============================================================================
# File này chứa class Vector2 để xử lý toán học vector 2D
# Sử dụng cho vị trí, hướng di chuyển, và tính toán khoảng cách

import math 

class Vector2(object): 
    """
    Class Vector2D đơn giản cho game Pac-Man
    - Hỗ trợ các phép toán vector cơ bản: +, -, *, /
    - Tính toán độ lớn và khoảng cách
    - So sánh vector với độ chính xác floating point
    """
    def __init__(self, x=0, y=0):
        """
        Khởi tạo vector với tọa độ x, y
        Args:
            x: Tọa độ x (mặc định 0)
            y: Tọa độ y (mặc định 0)
        """
        self.x = x 
        self.y = y 
        self.thresh = 0.000001  # Ngưỡng so sánh cho floating point
        
    def __add__(self, other): 
        """
        Phép cộng vector: self + other
        Args:
            other: Vector2 khác
        Returns:
            Vector2 mới là tổng của 2 vector
        """
        return Vector2(self.x + other.x, self.y + other.y) 
    
    def __sub__(self, other): 
        """
        Phép trừ vector: self - other
        Args:
            other: Vector2 khác
        Returns:
            Vector2 mới là hiệu của 2 vector
        """
        return Vector2(self.x - other.x, self.y - other.y) 
    
    def __neg__(self):
        """
        Phép đảo dấu vector: -self
        Returns:
            Vector2 mới với dấu ngược lại
        """
        return Vector2(-self.x, -self.y)
    
    def __mul__(self, scalar):
        """
        Phép nhân vector với scalar: self * scalar
        Args:
            scalar: Số thực để nhân
        Returns:
            Vector2 mới đã được nhân với scalar
        """
        return Vector2(self.x * scalar, self.y * scalar)
     
    def __div__(self, scalar): 
        """
        Phép chia vector cho scalar: self / scalar
        Args:
            scalar: Số thực để chia
        Returns:
            Vector2 mới đã được chia cho scalar, hoặc None nếu scalar = 0
        """
        if scalar != 0:
            return Vector2(self.x / float(scalar), self.y / float(scalar))
        return None
    
    def __truediv__(self, scalar): 
        """
        Phép chia thực (Python 3): self / scalar
        Args:
            scalar: Số thực để chia
        Returns:
            Vector2 mới đã được chia cho scalar
        """
        return self.__div__(scalar)
    
    def __eq__(self, other): 
        """
        So sánh bằng 2 vector với độ chính xác floating point
        Args:
            other: Vector2 khác để so sánh
        Returns:
            True nếu 2 vector gần như bằng nhau (trong ngưỡng thresh)
        """
        if abs(self.x - other.x) < self.thresh: 
            if abs(self.y - other.y) < self.thresh: 
                return True
        return False 
    
    def magnitudeSquared(self):
        """
        Tính bình phương độ lớn vector (tránh tính sqrt)
        Returns:
            x² + y²
        """
        return self.x ** 2 + self.y ** 2 
    
    def magnitude(self): 
        """
        Tính độ lớn vector (độ dài)
        Returns:
            sqrt(x² + y²)
        """
        return math.sqrt(self.magnitudeSquared())
    
    def copy(self): 
        """
        Tạo bản sao của vector
        Returns:
            Vector2 mới có cùng giá trị x, y
        """
        return Vector2(self.x, self.y) 
     
    def asTuple(self):
        """
        Chuyển vector thành tuple (x, y)
        Returns:
            Tuple (x, y)
        """
        return self.x, self.y 
    
    def asInt(self): 
        """
        Chuyển vector thành tuple số nguyên (int(x), int(y))
        Returns:
            Tuple (int(x), int(y))
        """
        return int(self.x), int(self.y) 
    
    def __str__(self):
        """
        Chuyển vector thành string để in
        Returns:
            String dạng "<x,y>"
        """
        return "<" + str(self.x) + "," + str(self.y) + ">"