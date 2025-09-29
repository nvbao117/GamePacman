import time
import math
from collections import deque
from queue import PriorityQueue
from constants import *
from engine.algorithms_practical import (
    bfs as bfs_practical, 
    astar as astar_practical,
    dfs, ucs, ids, greedy
)

class HybridAISystem:
    def __init__(self, pacman):
        self.pacman = pacman
        self.game_instance = None
        self.last_online_decision = 0    # Thời gian quyết định cuối

        self.current_mode = "OFFLINE"    # OFFLINE, ONLINE
        self.planning_interval = 60.0    # Khoảng thời gian lập kế hoạch lại (tối ưu cho 1 phút game)
        self.last_planning_time = 0      # Thời gian lập kế hoạch cuối

        # Performance tracking
        self.mode_switch_count = 0
        
        # Caching để tối ưu performance
        self._evaluation_cache = {}
        self._cache_max_size = 1000
    
    def set_mode(self, mode):
        """
        Set AI mode từ bên ngoài (ONLINE hoặc OFFLINE)
        """
        if mode in ["ONLINE", "OFFLINE"]:
            self.current_mode = mode
            # Reset planning khi chuyển mode
            self.offline_plan = []
            self.offline_plan_index = 0
            self.offline_plan_valid = False

    def get_direction(self, pellet_group, ghost_group=None):
        """
        Main decision function - chọn direction dựa trên mode hiện tại
        """
        direction = self._get_online_direction(pellet_group, ghost_group)

        return direction

# ==========================================================
#                    MINIMAX ALGORITHM
# ----------------------------------------------------------
# Thuật toán Minimax cho Pac-Man (không alpha-beta)
# - Pac-Man là người chơi tối đa (Maximizing Player)
# - Ghost là người chơi tối thiểu (Minimizing Player)
# - Đệ quy tìm kiếm trạng thái tốt nhất cho Pac-Man
# ==========================================================

    def minimax(self, pacman, ghostgroup, pellet_group, depth, is_maximizing_player=True):
        """
        Thuật toán Minimax cho Pac-Man (dạng tổng quát)
        """
        if self.is_terminal_state(pacman, ghostgroup, pellet_group) or depth == 0:
            return self.evaluate(pacman, ghostgroup, pellet_group), None

        if is_maximizing_player:
            max_eval = float('-inf')
            best_action = None
            for action in self.get_legal_actions(pacman, ghostgroup, pellet_group, True):
                next_pacman, next_ghostgroup, next_pellet_group = self.apply_action(pacman, ghostgroup, pellet_group, action, True)
                eval_score, _ = self.minimax(next_pacman, next_ghostgroup, next_pellet_group, depth - 1, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_action = action
            return max_eval, best_action
        else:
            min_eval = float('inf')
            best_action = None
            for action in self.get_legal_actions(pacman, ghostgroup, pellet_group, False):
                next_pacman, next_ghostgroup, next_pellet_group = self.apply_action(pacman, ghostgroup, pellet_group, action, False)
                eval_score, _ = self.minimax(next_pacman, next_ghostgroup, next_pellet_group, depth - 1, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_action = action
            return min_eval, best_action

    def is_terminal_state(self, pacman, ghostgroup, pellet_group):
        # Pacman bị ghost bắt
        for ghost in ghostgroup.ghosts:
            if ghost.node == pacman.node:
                return True

        # Tất cả pellets đã ăn hết
        pellets_left = any(pellet.visible for pellet in pellet_group.pelletList)
        if not pellets_left:
            return True

        return False

    def evaluate(self, pacman, ghostgroup, pellet_group):
        """Đánh giá trạng thái game"""
        # Giá trị càng cao càng tốt cho Pacman, càng thấp càng tốt cho Ghost
        # Tiêu chí: khoảng cách tới pellet gần nhất, khoảng cách tới ghost gần nhất, số pellet còn lại
        pacman_node = getattr(pacman, 'node', None)
        if pacman_node is None:
            return -10000
            
        ghost_nodes = [getattr(ghost, 'node', None) for ghost in getattr(ghostgroup, 'ghosts', []) if getattr(ghost, 'alive', True)]
        ghost_nodes = [node for node in ghost_nodes if node is not None]
        
        pellet_nodes = [getattr(pellet, 'node', None) for pellet in getattr(pellet_group, 'pelletList', []) if getattr(pellet, 'visible', True)]
        pellet_nodes = [node for node in pellet_nodes if node is not None]

        # Nếu Pacman bị bắt, trạng thái rất xấu
        for ghost_node in ghost_nodes:
            if ghost_node == pacman_node:
                return -10000

        # Nếu ăn hết pellet, trạng thái rất tốt
        if len(pellet_nodes) == 0:
            return 10000

        # Khoảng cách tới pellet gần nhất
        min_pellet_dist = min(
            (self._calculate_distance(pacman_node, p) for p in pellet_nodes),
            default=float('inf')
        )

        # Khoảng cách tới ghost gần nhất
        min_ghost_dist = min(
            (self._calculate_distance(pacman_node, g) for g in ghost_nodes),
            default=float('inf')
        )

        pellets_left = len(pellet_nodes)
        pellet_bonus = max(0, 50 - 10 * min_pellet_dist)
        ghost_penalty = -1000 if min_ghost_dist <= 2 else -500 / (min_ghost_dist + 1)
        safety_bonus = 100 if min_ghost_dist >= 6 else 20 if min_ghost_dist >= 3 else 0

        # Điểm đánh giá tổng hợp
        score = (
            -3 * min_pellet_dist +      # Ưu tiên pellet gần
            4 * min_ghost_dist +        # Ưu tiên tránh xa ghost
            -15 * pellets_left +        # Ăn nhiều pellet
            ghost_penalty +             # Phạt nếu quá gần ghost
            pellet_bonus +              # Thưởng khi gần pellet
            safety_bonus                # Thưởng khi an toàn
        )
        return score

    def get_legal_actions(self, pacman, ghostgroup, pellet_group, is_pacman):
        """Lấy danh sách hành động hợp lệ"""
        actions = []
        if is_pacman:
            for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
                if self._can_move_in_direction(pacman.node, direction):
                    actions.append(direction)
        else:
            for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
                if ghostgroup.ghosts and ghostgroup.ghosts[0].node:
                    if self._can_move_in_direction(ghostgroup.ghosts[0].node, direction):
                        actions.append(direction)
        return actions

    def apply_action(self, pacman, ghostgroup, pellet_group, action, is_maximizing_player):
        """Áp dụng hành động và trả về trạng thái mới"""
        if is_maximizing_player:
        # Di chuyển Pac-Man
            new_pacman_node = pacman.node.neighbors[action]
            new_pacman = type('Pacman', (), {'node': new_pacman_node})()
            return new_pacman, ghostgroup, pellet_group
        else:
            # Di chuyển TẤT CẢ Ghosts theo cùng 1 action
            new_ghosts = []
            for ghost in ghostgroup.ghosts:
                if hasattr(ghost, 'node') and ghost.node:
                    new_ghost_node = ghost.node.neighbors[action]
                    new_ghost = type('Ghost', (), {
                        'node': new_ghost_node, 
                        'alive': getattr(ghost, 'alive', True)
                    })()
                    new_ghosts.append(new_ghost)
            
            new_ghostgroup = type('GhostGroup', (), {'ghosts': new_ghosts})()
            return pacman, new_ghostgroup, pellet_group

# ==========================================================
#                    END OF MINIMAX ALGORITHM
# ==========================================================

# ==========================================================
#                ALPHA-BETA PRUNING ALGORITHM
# ----------------------------------------------------------
# Thuật toán Alpha-Beta Pruning cho Pac-Man
# - Là phiên bản tối ưu của Minimax, cắt tỉa các nhánh không cần thiết
# - Pac-Man là người chơi tối đa (Maximizing Player)
# - Ghost là người chơi tối thiểu (Minimizing Player)
# - Sử dụng hai giá trị alpha (giá trị tốt nhất cho Max) và beta (giá trị tốt nhất cho Min)
# - Nếu tìm được nhánh tệ hơn giá trị hiện tại của Max hoặc Min, dừng duyệt nhánh đó (cắt tỉa)
# - Đệ quy tìm kiếm trạng thái tốt nhất cho Pac-Man với hiệu suất cao hơn Minimax thường
# ==========================================================


# ==========================================================
#                    END OF ALPHA-BETA PRUNING ALGORITHM
# ==========================================================
# ==========================================================


# ==========================================================
#                    HILL CLIMBING ALGORITHM
# ----------------------------------------------------------
# Thuật toán Hill Climbing cho Pac-Man
# - Bắt đầu từ trạng thái hiện tại, thử các hành động lân cận
# - Chọn hành động mang lại giá trị đánh giá tốt nhất
# - Lặp lại cho đến khi không còn cải thiện
# ==========================================================
 
# ==========================================================
#                    END OF HILL CLIMBING ALGORITHM
# ==========================================================
# ==========================================================
#                    GENETIC ALGORITHM
# ----------------------------------------------------------
# Thuật toán Genetic Algorithm cho Pac-Man
# - Mã hóa chuỗi hành động thành cá thể (chromosome)
# - Tạo quần thể, đánh giá, chọn lọc, lai ghép, đột biến
# - Lặp lại qua nhiều thế hệ để tìm chuỗi hành động tối ưu
# ==========================================================
# ==========================================================
#                    END OF GENETIC ALGORITHM
# ==========================================================
# ==========================================================
#                    EXPECTIMAX ALGORITHM
# ----------------------------------------------------------
# Thuật toán Expectimax cho Pac-Man
# - Là biến thể của Minimax, dùng khi đối thủ (Ghost) di chuyển ngẫu nhiên
# - Pac-Man là người chơi tối đa (Maximizing Player)
# - Ghost là "chance node" (nút xác suất), chọn hành động ngẫu nhiên
# - Ở lượt Ghost, giá trị nút là kỳ vọng (trung bình có trọng số) của các trạng thái con
# - Đệ quy tìm kiếm trạng thái tốt nhất cho Pac-Man khi Ghost không tối ưu mà hành động ngẫu nhiên
# ==========================================================
# ==========================================================
#                    END OF EXPECTIMAX ALGORITHM
# ==========================================================

# ==========================================================
#                    MONTE CARLO TREE SEARCH (MCTS)
# ----------------------------------------------------------
# Thuật toán Monte Carlo Tree Search cho Pac-Man
# - Xây dựng cây tìm kiếm bằng cách mô phỏng nhiều lần từ trạng thái hiện tại
# - Gồm 4 bước: Selection, Expansion, Simulation, Backpropagation
# - Chọn hành động dựa trên thống kê kết quả mô phỏng
# - Phù hợp với môi trường có nhiều trạng thái và không xác định
# ==========================================================
# ==========================================================
#                END OF MONTE CARLO TREE SEARCH (MCTS)
# ==========================================================
# ==========================================================
#                    Q-LEARNING
# ----------------------------------------------------------
# Thuật toán Q-Learning cho Pac-Man
# - Học giá trị Q cho từng cặp (trạng thái, hành động)
# - Cập nhật Q-value dựa trên phần thưởng nhận được và giá trị tối đa tiếp theo
# - Không cần mô hình môi trường, học qua trải nghiệm
# - Sử dụng hàm Q để chọn hành động tối ưu tại mỗi trạng thái
# ==========================================================
# ==========================================================
#                    END OF Q-LEARNING
# ==========================================================
# ==========================================================
#                    DEEP Q-LEARNING
# ----------------------------------------------------------
# Thuật toán Deep Q-Learning cho Pac-Man
# - Sử dụng mạng nơ-ron sâu (Deep Neural Network) để xấp xỉ hàm Q
# - Đầu vào là trạng thái, đầu ra là Q-value cho mỗi hành động
# - Học từ trải nghiệm bằng cách tối ưu hàm mất mát giữa Q thực tế và Q dự đoán
# - Giải quyết bài toán không gian trạng thái lớn, phức tạp
# ==========================================================
# ==========================================================
#                    END OF DEEP Q-LEARNING
# ==========================================================
# ==========================================================
#                    A* ALGORITHM
# ----------------------------------------------------------
# Thuật toán A* cho Pac-Man
# - Tìm đường đi ngắn nhất từ vị trí hiện tại đến mục tiêu (pellet)
# - Sử dụng hàm heuristic (ước lượng khoảng cách còn lại) để tối ưu tìm kiếm
# - Đảm bảo tìm được đường đi tối ưu nếu heuristic phù hợp
# - Phù hợp cho môi trường có bản đồ xác định, ít thay đổi
# ==========================================================
# ==========================================================
#                END OF A* ALGORITHM
# ==========================================================
# ==========================================================
#                    GREEDY ALGORITHM
# ----------------------------------------------------------
# Thuật toán Greedy cho Pac-Man
# - Luôn chọn hành động đưa Pac-Man đến pellet gần nhất tại mỗi bước
# - Không xét đến các trạng thái tương lai, chỉ quan tâm lợi ích trước mắt
# - Đơn giản, tốc độ nhanh nhưng có thể không tối ưu toàn cục
# - Phù hợp cho các bài toán cần giải quyết nhanh, không yêu cầu tối ưu tuyệt đối
# ==========================================================
# ==========================================================
#                END OF GREEDY ALGORITHM
# ==========================================================
    def _get_online_direction(self, pellet_group, ghost_group):
        """Lấy direction từ thuật toán đã chọn"""
        
        current_node = self.pacman.node
        algorithm_name = getattr(self.pacman, 'pathfinder_name', 'A*')
        
        try:
            if algorithm_name == 'Minimax':
                # Sử dụng Minimax với depth tối ưu
                print("Using Minimax algorithm")
                eval_score, action = self.minimax(self.pacman, ghost_group, pellet_group, 3 , True)
                if action is not None:
                    return action
                else:
                    return self._get_random_direction(current_node)
            
            else:
                # Sử dụng thuật toán pathfinding đã chọn
                algorithm_func = getattr(self.pacman, 'pathfinder', astar_practical)
                
                # Tìm đường đi đến pellet gần nhất
                path = algorithm_func(current_node, pellet_group)
                if path and len(path) > 1:
                    next_node = path[1]
                    return self._get_direction_from_nodes(current_node, next_node)
                else:
                    return self._get_random_direction(current_node)
                    
        except Exception as e:
            print(f"Algorithm {algorithm_name} error: {e}")
            return self._get_random_direction(current_node)

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

    def _get_direction_from_nodes(self, from_node, to_node):
        """Lấy direction từ from_node đến to_node"""
        return self._get_direction_between_nodes(from_node, to_node)

    def _get_random_direction(self, current_node):
        """Lấy direction ngẫu nhiên từ current_node"""
        import random
        valid_directions = []
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            if self._can_move_in_direction(current_node, direction):
                valid_directions.append(direction)
        
        if valid_directions:
            return random.choice(valid_directions)
        return STOP

    def _calculate_distance(self, node1, node2):
        """Tính khoảng cách Manhattan giữa hai nodes"""

        if node1 is None or node2 is None:
            return float('inf')

        dx = abs(node1.position.x - node2.position.x)
        dy = abs(node1.position.y - node2.position.y)
        return dx + dy