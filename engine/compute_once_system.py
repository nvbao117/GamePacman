# =============================================================================
# COMPUTE_ONCE_SYSTEM.PY - TÍNH TOÁN PATH CHỈ 1 LẦN DUY NHẤT
# =============================================================================

import time
from constants import *

class ComputeOnceSystem:
    def __init__(self):
        self.master_path = []  # Complete path for entire game
        self.current_index = 0  # Current position in master path
        self.is_computed = False
        self.algorithm_name = ""
        self.pellet_count_when_computed = 0
        self.curent_level = 0 
        self.last_level = -1 
        
    def get_direction(self, pacman, pelletGroup, pathfinder, pathfinder_name):
        """
        Lấy hướng di chuyển từ master path đã tính sẵn
        
        Args:
            pacman: Đối tượng Pacman
            pelletGroup: Nhóm các pellet cần ăn
            pathfinder: Hàm thuật toán AI (BFS, DFS, A*, etc.)
            pathfinder_name: Tên thuật toán để hiển thị
            
        Returns:
            direction: Hướng di chuyển (UP, DOWN, LEFT, RIGHT, STOP)
        """
        # Điều kiện để tính toán lại master path:
        # 1. Chưa từng tính toán lần nào
        # 2. Thuật toán AI đã thay đổi
        # 3. Số lượng pellets thay đổi (lên level mới)
        print("---------------------")
        print("self.curent_level", self.curent_level)
        print("self.last_level", self.last_level)
        print("---------------------")
        pellet_count_now = len([p for p in pelletGroup.pelletList if p.visible])

        should_compute = (
            not self.is_computed or                 
            self.algorithm_name != pathfinder_name or
            self.curent_level != self.last_level or
            abs(pellet_count_now - self.pellet_count_when_computed) >= 200
        )
        print("should_compute", should_compute)
        if should_compute:
            success = self._compute_master_path(pacman, pelletGroup, pathfinder, pathfinder_name)
            if not success:
                # Nếu tính toán thất bại, dùng greedy backup
                return self._emergency_greedy(pacman, pelletGroup)

        return self._follow_master_path(pacman, pelletGroup)
    
    def _compute_master_path(self, pacman, pelletGroup, pathfinder, pathfinder_name):
        start_time = time.time()
        
        try:
            # Gọi thuật toán AI thuần túy để tính đường đi hoàn chỉnh
            # Không giới hạn thời gian hoặc số bước
            path = pathfinder(pacman.node, pelletGroup)
            
            if path and len(path) > 1:
                if path[0] == pacman.node:
                    self.master_path = path[1:]  # Bỏ qua vị trí hiện tại
                else:
                    self.master_path = path
                    
                self.current_index = 0
                self.is_computed = True
                self.algorithm_name = pathfinder_name
                self.pellet_count_when_computed = len([p for p in pelletGroup.pelletList if p.visible])
                self.last_level = self.curent_level
                for node in self.master_path:
                    print(f"{node.position.x//16, node.position.y//16}",end = " ")
                print()
                print(f"Total steps: {len(self.master_path)}")
                print("--------------------------------")

                return True
            else:
                return False
            
        except Exception as e:
            return False
    
    def _follow_master_path(self, pacman, pelletGroup):
        """
        Đi theo master path KHÔNG GIỚI HẠN từng bước một
        
        Sử dụng thuật toán AI thuần túy, không có giới hạn path
        """
        # Kiểm tra xem đã hoàn thành path chưa
        if self.current_index >= len(self.master_path):
            return self._emergency_greedy(pacman, pelletGroup)
        
        # Lấy node tiếp theo từ master path
        target_node = self.master_path[self.current_index]
        
        # Tìm hướng đi tới target node
        direction = self._get_direction_to_node(pacman.node, target_node)
        
        # Tiến tới bước tiếp theo khi đã đến target
        if pacman.node == target_node:
            self.current_index += 1
            if self.current_index < len(self.master_path):
                target_node = self.master_path[self.current_index]
                direction = self._get_direction_to_node(pacman.node, target_node)
            else:
                # Đã hoàn thành master path
                return self._emergency_greedy(pacman, pelletGroup)
        
        # Xử lý khi path bị chặn
        if direction == STOP:
            # Thử skip ahead một vài bước
            for skip in range(1, min(5, len(self.master_path) - self.current_index)):
                if self.current_index + skip < len(self.master_path):
                    next_target = self.master_path[self.current_index + skip]
                    skip_direction = self._get_direction_to_node(pacman.node, next_target)
                    if skip_direction != STOP:
                        self.current_index += skip
                        return skip_direction
            
            return self._emergency_greedy(pacman, pelletGroup)
        
        return direction
    
    def _get_direction_to_node(self, from_node, to_node):
        """
        Tìm hướng di chuyển từ from_node đến to_node
        Args:
            from_node: Node xuất phát
            to_node: Node đích
        """
        from constants import STOP, PORTAL, PACMAN
        
        if not from_node or not to_node:
            return STOP
        
        # Kiểm tra các neighbor và tính hợp lệ của move
        for direction, neighbor in from_node.neighbors.items():
            if neighbor == to_node:
                # Kiểm tra xem có thể di chuyển không
                if direction == PORTAL:
                    return direction
                else:
                    # Kiểm tra access permission cho Pacman
                    if PACMAN in from_node.access[direction]:
                        return direction
        
        # Không tìm thấy đường đi hợp lệ
        return STOP
    
    def _emergency_greedy(self, pacman, pelletGroup):
        """
        Chế độ greedy khẩn cấp khi master path không khả dụng
        
        Args:
            pacman: Đối tượng Pacman
            pelletGroup: Nhóm pellet còn lại
            
        Returns:
            direction: Hướng di chuyển greedy tới pellet gần nhất
        """
        from constants import UP, DOWN, LEFT, RIGHT, PORTAL, PACMAN, STOP
        
        if not pelletGroup or not pelletGroup.pelletList:
            return STOP
        
        # Find nearest pellet
        pellet_nodes = [p.node for p in pelletGroup.pelletList if p.node and p.visible]
        if not pellet_nodes:
            return STOP
        
        # Use simple greedy - very fast, no lag
        nearest_pellet = min(pellet_nodes, 
                           key=lambda p: self._manhattan_distance(pacman.node, p))
        
        # Move toward nearest pellet
        best_direction = STOP
        min_distance = float('inf')
        
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = pacman.node.neighbors.get(direction)
            if neighbor:
                # Check if valid move
                can_move = (direction == PORTAL or 
                           PACMAN in pacman.node.access[direction])
                
                if can_move:
                    distance = self._manhattan_distance(neighbor, nearest_pellet)
                    if distance < min_distance:
                        min_distance = distance
                        best_direction = direction
        
        # Only print occasionally to avoid spam
        if not hasattr(self, '_greedy_print_counter'):
            self._greedy_print_counter = 0
        self._greedy_print_counter += 1
        
        if self._greedy_print_counter % 100 == 0:
            pass
        
        return best_direction
    
    def _manhattan_distance(self, node1, node2):
        """Manhattan distance"""
        if not node1 or not node2:
            return float('inf')
        
        dx = abs(node1.position.x - node2.position.x)
        dy = abs(node1.position.y - node2.position.y)
        return dx + dy
    
    def _can_move_between(self, from_node, to_node):
        """
        Kiểm tra xem có thể di chuyển từ from_node đến to_node không
        """
        if not from_node or not to_node:
            return False
        
        # Kiểm tra xem to_node có phải là neighbor của from_node không
        for direction, neighbor in from_node.neighbors.items():
            if neighbor == to_node:
                # Kiểm tra access permission
                if direction == "PORTAL":
                    return True
                else:
                    from constants import PACMAN
                    return PACMAN in from_node.access[direction]
        
        return False
    
    def reset(self):
        """Reset system - force recompute next time"""
        self.master_path = []
        self.current_index = 0
        self.is_computed = False
        self.last_level = -1
        self.curent_level = 0
        self.algorithm_name = ""
        self.pellet_count_when_computed = 0
        # System reset - sẽ tính lại path ở lần gọi tiếp theo
    
    def get_progress_info(self):
        """Get current progress information"""
        if not self.is_computed:
            return "Not computed yet"
        
        total_steps = len(self.master_path)
        current_step = self.current_index
        remaining_steps = total_steps - current_step
        progress_percent = (current_step / total_steps) * 100 if total_steps > 0 else 0
        
        return {
            'algorithm': self.algorithm_name,
            'total_steps': total_steps,
            'current_step': current_step,
            'remaining_steps': remaining_steps,
            'progress_percent': progress_percent,
            'is_completed': current_step >= total_steps
        }
# Global compute-once system
compute_once = ComputeOnceSystem()

