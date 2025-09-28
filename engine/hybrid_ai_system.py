import time
import math
from collections import deque
from queue import PriorityQueue
from constants import *
from engine.algorithms_practical import *

class HybridAISystem:
    def __init__(self, pacman):
        self.pacman = pacman
        self.game_instance = None
        
        # Offline planning
        self.offline_plan = []           # Kế hoạch dài hạn
        self.offline_plan_index = 0      # Vị trí hiện tại trong plan
        self.offline_plan_valid = False  # Plan có còn hợp lệ không
        
        # Online decision-making
        self.online_target = None        # Mục tiêu tức thì
        self.online_priority = 0         # Độ ưu tiên (0-10)
        self.last_online_decision = 0    # Thời gian quyết định cuối
        
        # Hybrid control
        self.current_mode = "HYBRID"     # OFFLINE, ONLINE, HYBRID
        self.mode_switch_threshold = 0.7 # Ngưỡng chuyển đổi mode
        self.planning_interval = 60.0    # Khoảng thời gian lập kế hoạch lại (tối ưu cho 1 phút game)
        self.last_planning_time = 0      # Thời gian lập kế hoạch cuối
        
        # Performance tracking
        self.offline_success_rate = 0.0
        self.online_success_rate = 0.0
        self.mode_switch_count = 0
        
    def get_direction(self, pellet_group, ghost_group=None):
        """
        Main decision function - chọn direction dựa trên mode hiện tại
        
        Args:
            pellet_group: Nhóm pellets cần ăn
            ghost_group: Nhóm ghosts (để tránh)
            
        Returns:
            direction: Hướng di chuyển được chọn
        """
        current_time = time.time()
        
        # 1. Kiểm tra và cập nhật mode
        self._update_mode(current_time, pellet_group, ghost_group)
        
        # 2. Lấy direction dựa trên mode
        if self.current_mode == "OFFLINE":
            direction = self._get_offline_direction(pellet_group)
        elif self.current_mode == "ONLINE":
            direction = self._get_online_direction(pellet_group, ghost_group)
        else:  # HYBRID
            direction = self._get_hybrid_direction(pellet_group, ghost_group)
        
        # 3. Cập nhật tracking
        self._update_performance_tracking(direction, pellet_group)
        
        return direction
    
    def _update_mode(self, current_time, pellet_group, ghost_group):
        """Cập nhật mode dựa trên tình huống hiện tại"""
        
        # Kiểm tra điều kiện chuyển sang ONLINE
        if self._should_switch_to_online(ghost_group):
            if self.current_mode != "ONLINE":
                self.current_mode = "ONLINE"
                self.mode_switch_count += 1
        
        # Kiểm tra điều kiện chuyển sang OFFLINE
        elif self._should_switch_to_offline(current_time, pellet_group):
            if self.current_mode != "OFFLINE":
                self.current_mode = "OFFLINE"
                self.mode_switch_count += 1
        
        # Kiểm tra điều kiện chuyển sang HYBRID
        elif self._should_switch_to_hybrid(current_time, pellet_group, ghost_group):
            if self.current_mode != "HYBRID":
                self.current_mode = "HYBRID"
                self.mode_switch_count += 1
    
    def _should_switch_to_online(self, ghost_group):
        """Kiểm tra có nên chuyển sang ONLINE mode không"""
        if not ghost_group:
            return False
        
        # Kiểm tra có ghost gần không (trong vòng 5 tiles)
        for ghost in ghost_group.ghosts:
            if ghost.mode != FREIGHT:  # Ghost không ở chế độ sợ hãi
                distance = self._calculate_distance(self.pacman.node, ghost.node)
                if distance <= 5:
                    return True
        
        return False
    
    def _should_switch_to_offline(self, current_time, pellet_group):
        """Kiểm tra có nên chuyển sang OFFLINE mode không"""
        
        # Plan hiện tại không còn hợp lệ (ưu tiên cao nhất)
        if not self.offline_plan_valid:
            return True
        
        # Kiểm tra progress của plan hiện tại
        if hasattr(self, 'offline_plan') and self.offline_plan:
            progress_ratio = self.offline_plan_index / len(self.offline_plan)
            
            # Nếu đã đi được 80% plan và còn nhiều pellets → lập kế hoạch mới
            if progress_ratio > 0.8:
                remaining_pellets = len([p for p in pellet_group.pelletList if p.visible])
                if remaining_pellets > 10:  # Giảm threshold xuống 10
                    return True
        
        # Đã đủ thời gian để lập kế hoạch lại (15 giây)
        if current_time - self.last_planning_time > self.planning_interval:
            remaining_pellets = len([p for p in pellet_group.pelletList if p.visible])
            if remaining_pellets > 5:  # Chỉ lập kế hoạch nếu còn ít nhất 5 pellets
                return True
        
        return False
    
    def _should_switch_to_hybrid(self, current_time, pellet_group, ghost_group):
        """Kiểm tra có nên chuyển sang HYBRID mode không"""
        
        # Không có ghost gần nhưng cũng không an toàn hoàn toàn
        ghost_nearby = False
        if ghost_group:
            for ghost in ghost_group.ghosts:
                if ghost.mode != FREIGHT:
                    distance = self._calculate_distance(self.pacman.node, ghost.node)
                    if distance <= 8:  # Ghost ở khoảng cách trung bình
                        ghost_nearby = True
                        break
        
        # Có một số pellets nhưng không quá nhiều
        remaining_pellets = len([p for p in pellet_group.pelletList if p.visible])
        
        return (not ghost_nearby and 
                5 < remaining_pellets < 20 and 
                current_time - self.last_planning_time > 1.0)
    
    def _get_offline_direction(self, pellet_group):
        """Lấy direction từ offline planning"""
        
        # Lập kế hoạch mới nếu cần
        if not self.offline_plan_valid or not self.offline_plan:
            self._create_offline_plan(pellet_group)
        
        # Lấy direction từ plan hiện tại
        if (self.offline_plan and 
            self.offline_plan_index < len(self.offline_plan) - 1):
            
            current_node = self.offline_plan[self.offline_plan_index]
            next_node = self.offline_plan[self.offline_plan_index + 1]
            
            # Tìm direction từ current_node đến next_node
            direction = self._get_direction_between_nodes(current_node, next_node)
            
            # Cập nhật index
            self.offline_plan_index += 1
            
            return direction
        
        # Fallback to online nếu plan hết
        return self._get_online_direction(pellet_group, None)
    
    def _get_online_direction(self, pellet_group, ghost_group):
        """Lấy direction từ online decision-making"""
        
        current_node = self.pacman.node
        
        # 1. Kiểm tra ghost threat (ưu tiên cao nhất)
        if ghost_group:
            safe_direction = self._avoid_ghosts(ghost_group)
            if safe_direction is not None:
                return safe_direction
        
        # 2. Tìm pellet gần nhất
        nearest_pellet = self._find_nearest_pellet(current_node, pellet_group)
        if nearest_pellet:
            return self._get_direction_to_target(nearest_pellet)
        
        # 3. Fallback: di chuyển random
        return self._get_random_safe_direction()
    
    def _get_hybrid_direction(self, pellet_group, ghost_group):
        """Lấy direction từ hybrid approach"""
        
        # 1. Kiểm tra immediate threats (online)
        if ghost_group:
            safe_direction = self._avoid_ghosts(ghost_group)
            if safe_direction is not None:
                return safe_direction
        
        # 2. Sử dụng offline plan nếu có và hợp lệ
        if (self.offline_plan_valid and 
            self.offline_plan and 
            self.offline_plan_index < len(self.offline_plan) - 1):
            
            # Kiểm tra plan có còn hợp lệ không
            if self._is_plan_still_valid(pellet_group):
                return self._get_offline_direction(pellet_group)
        
        # 3. Fallback to online
        return self._get_online_direction(pellet_group, ghost_group)
    
    def _create_offline_plan(self, pellet_group):
        """Tạo offline plan sử dụng BFS hoặc A*"""
        
        if not pellet_group or not pellet_group.pelletList:
            self.offline_plan = []
            self.offline_plan_valid = False
            return
        
        # Chọn thuật toán offline dựa trên số lượng pellets
        remaining_pellets = len([p for p in pellet_group.pelletList if p.visible])
        
        if remaining_pellets > 50:
            # Nhiều pellets: dùng BFS (nhanh hơn)
            self.offline_plan = bfs_practical(self.pacman.node, pellet_group)
        else:
            # Ít pellets: dùng A* (tối ưu hơn)
            self.offline_plan = astar_practical(self.pacman.node, pellet_group)
        
        self.offline_plan_index = 0
        self.offline_plan_valid = True
        self.last_planning_time = time.time()
        
    
    def _avoid_ghosts(self, ghost_group):
        """Tránh ghosts (online decision)"""
        
        if not ghost_group:
            return None
        
        current_node = self.pacman.node
        safe_directions = []
        
        # Kiểm tra tất cả hướng có thể di chuyển
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            if self._can_move_in_direction(current_node, direction):
                next_node = current_node.neighbors[direction]
                
                # Kiểm tra có ghost nào ở hướng này không
                ghost_in_direction = False
                for ghost in ghost_group.ghosts:
                    if ghost.mode != FREIGHT:  # Chỉ tránh ghost không sợ hãi
                        distance = self._calculate_distance(next_node, ghost.node)
                        if distance <= 3:  # Ghost quá gần
                            ghost_in_direction = True
                            break
                
                if not ghost_in_direction:
                    safe_directions.append(direction)
        
        # Chọn hướng an toàn nhất (xa ghost nhất)
        if safe_directions:
            best_direction = None
            max_safe_distance = 0
            
            for direction in safe_directions:
                next_node = current_node.neighbors[direction]
                min_ghost_distance = float('inf')
                
                for ghost in ghost_group.ghosts:
                    if ghost.mode != FREIGHT:
                        distance = self._calculate_distance(next_node, ghost.node)
                        min_ghost_distance = min(min_ghost_distance, distance)
                
                if min_ghost_distance > max_safe_distance:
                    max_safe_distance = min_ghost_distance
                    best_direction = direction
            
            return best_direction
        
        return None
    
    def _find_nearest_pellet(self, current_node, pellet_group):
        """Tìm pellet gần nhất (online decision)"""
        
        if not pellet_group or not pellet_group.pelletList:
            return None
        
        nearest_pellet = None
        min_distance = float('inf')
        
        for pellet in pellet_group.pelletList:
            if pellet.visible and pellet.node:
                distance = self._calculate_distance(current_node, pellet.node)
                if distance < min_distance:
                    min_distance = distance
                    nearest_pellet = pellet.node
        
        return nearest_pellet
    
    def _get_direction_to_target(self, target_node):
        """Lấy direction đến target node"""
        
        current_node = self.pacman.node
        
        # Tìm hướng đưa đến gần target nhất
        best_direction = None
        min_distance = float('inf')
        
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            if self._can_move_in_direction(current_node, direction):
                next_node = current_node.neighbors[direction]
                distance = self._calculate_distance(next_node, target_node)
                
                if distance < min_distance:
                    min_distance = distance
                    best_direction = direction
        
        return best_direction
    
    def _get_random_safe_direction(self):
        """Lấy direction ngẫu nhiên an toàn"""
        
        current_node = self.pacman.node
        safe_directions = []
        
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            if self._can_move_in_direction(current_node, direction):
                safe_directions.append(direction)
        
        if safe_directions:
            import random
            return random.choice(safe_directions)
        
        return STOP
    
    def _is_plan_still_valid(self, pellet_group):
        """Kiểm tra plan có còn hợp lệ không"""
        
        if not self.offline_plan or self.offline_plan_index >= len(self.offline_plan):
            return False
        
        # Kiểm tra pellets trong plan có còn tồn tại không
        remaining_pellets = {p.node for p in pellet_group.pelletList if p.visible}
        
        for i in range(self.offline_plan_index, len(self.offline_plan)):
            if self.offline_plan[i] in remaining_pellets:
                return True
        
        return False
    
    def _can_move_in_direction(self, current_node, direction):
        """Kiểm tra có thể di chuyển theo hướng không"""
        
        if direction == PORTAL:
            return current_node.neighbors[PORTAL] is not None
        else:
            return (current_node.neighbors[direction] is not None and 
                    PACMAN in current_node.access[direction])
    
    def _get_direction_between_nodes(self, from_node, to_node):
        """Lấy direction giữa hai nodes"""
        
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            if from_node.neighbors[direction] == to_node:
                return direction
        
        return STOP
    
    def _calculate_distance(self, node1, node2):
        """Tính khoảng cách Manhattan giữa hai nodes"""
        
        if node1 is None or node2 is None:
            return float('inf')
        
        dx = abs(node1.position.x - node2.position.x)
        dy = abs(node1.position.y - node2.position.y)
        return dx + dy
    
    def _update_performance_tracking(self, direction, pellet_group):
        """Cập nhật tracking hiệu suất"""
        
        # Đơn giản: track số lần chuyển mode
        pass
    
    def get_status_info(self):
        """Lấy thông tin trạng thái cho debug"""
        
        progress_ratio = 0
        if self.offline_plan and len(self.offline_plan) > 0:
            progress_ratio = self.offline_plan_index / len(self.offline_plan)
        
        return {
            "current_mode": self.current_mode,
            "offline_plan_length": len(self.offline_plan) if self.offline_plan else 0,
            "offline_plan_index": self.offline_plan_index,
            "offline_plan_valid": self.offline_plan_valid,
            "offline_plan_progress": f"{progress_ratio:.1%}",
            "mode_switch_count": self.mode_switch_count,
            "online_target": self.online_target is not None,
            "planning_interval": self.planning_interval
        }
