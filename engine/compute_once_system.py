import time
from constants import *
from engine.heuristic import Heuristic

class ComputeOnceSystem:
    def __init__(self, config=None):
        self.master_path = []  # Complete path for entire game
        self.current_index = 0  # Current position in master path
        self.is_computed = False
        self.algorithm_name = ""
        self.config = config
        self.pellet_count_when_computed = 0
        self.curent_level = 0 
        self.last_level = -1 
        
    def get_direction(self, pacman, pelletGroup, pathfinder, pathfinder_name, fruit = None ) :
        pellet_count_now = len([p for p in pelletGroup.pelletList if p.visible])


        pellet_change = abs(pellet_count_now - self.pellet_count_when_computed)
        pellet_change_threshold = min(20, int(self.pellet_count_when_computed * 0.1)) if self.pellet_count_when_computed > 0 else 20
        
        should_compute = (
            not self.is_computed or                 
            self.algorithm_name != pathfinder_name or
            self.curent_level != self.last_level or
            abs(pellet_count_now - self.pellet_count_when_computed) >= 200
        )
        if should_compute:
            success = self._compute_master_path(pacman, pelletGroup, pathfinder, pathfinder_name)
            if not success:
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
        from constants import UP, DOWN, LEFT, RIGHT, PORTAL, PACMAN, STOP
        
        if not pelletGroup or not pelletGroup.pelletList:
            return STOP
        
        # Find nearest pellet
        pellet_nodes = [p.node for p in pelletGroup.pelletList if p.node and p.visible]
        if not pellet_nodes:
            return STOP
        
        # Use simple greedy - very fast, no lag
        nearest_pellet = min(pellet_nodes, 
                           key=lambda p: self._calculate_distance(pacman.node, p))
        
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
                    distance = self._calculate_distance(neighbor, nearest_pellet)
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
    
    def _calculate_distance(self, node1, node2):
        config = self.config
        if config is None and hasattr(self.pacman, 'config'):
            config = self.pacman.config
        
        # Check if nodes are valid
        if not hasattr(node1, 'position') or not hasattr(node2, 'position'):
            return float('inf')
            
        func = Heuristic.get_heuristic_function(config)
        return func(node1, node2)

# Global compute-once system
compute_once = ComputeOnceSystem()

