import time
import math
import copy
from collections import deque
from queue import PriorityQueue
from constants import *
from engine.algorithms_practical import (
    bfs as bfs_practical, 
    astar as astar_practical,
    dfs, ucs, ids, greedy
)
from engine.q_learning import QLearningAgent,QLearningConfig
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
        
        # Q-learning state tracking
        self.prev_q_state = None
        self.prev_q_action = None
        self._last_pacman_pos = None
        self.prev_pellet_count = 0
        self._portal_used = False
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
        pacman_node = getattr(pacman, 'node', None)
        if pacman_node is None:
            return -10000
            
        ghost_nodes = [getattr(ghost, 'node', None) for ghost in getattr(ghostgroup, 'ghosts', []) if getattr(ghost, 'alive', True)]
        ghost_nodes = [node for node in ghost_nodes if node is not None]
        
        pellet_nodes = [getattr(pellet, 'node', None) for pellet in getattr(pellet_group, 'pelletList', []) if getattr(pellet, 'visible', True)]
        pellet_nodes = [node for node in pellet_nodes if node is not None]

        # Kiểm tra trạng thái kết thúc
        for ghost_node in ghost_nodes:
            if ghost_node == pacman_node:
                return -10000

        if len(pellet_nodes) == 0:
            return 10000

        # 1. Đánh giá khoảng cách đến pellets
        pellet_distances = [self._calculate_distance(pacman_node, p) for p in pellet_nodes]
        min_pellet_dist = min(pellet_distances) if pellet_distances else float('inf')
        avg_pellet_dist = sum(pellet_distances) / len(pellet_distances) if pellet_distances else float('inf')
        
        # 2. Đánh giá khoảng cách đến ghosts
        ghost_distances = [self._calculate_distance(pacman_node, g) for g in ghost_nodes]
        min_ghost_dist = min(ghost_distances) if ghost_distances else float('inf')
        avg_ghost_dist = sum(ghost_distances) / len(ghost_distances) if ghost_distances else float('inf')
        
        # 3. Đánh giá số lượng pellets còn lại
        pellets_left = len(pellet_nodes)
        total_pellets = getattr(pellet_group, 'total_pellets', pellets_left)
        pellet_progress = (total_pellets - pellets_left) / total_pellets if total_pellets > 0 else 0
        
        # 4. Đánh giá vị trí chiến lược (tránh góc, đường cụt)
        position_score = self._evaluate_position_strategy(pacman_node, ghost_nodes)
        
        # 5. Đánh giá mật độ pellets xung quanh
        density_score = self._evaluate_pellet_density(pacman_node, pellet_nodes)
        
        # 6. Đánh giá an toàn dựa trên vị trí ghosts
        safety_score = self._evaluate_safety(pacman_node, ghost_nodes)
        
        # 7. Đánh giá power pellets (nếu có)
        power_pellet_score = self._evaluate_power_pellets(pacman_node, pellet_group)
        
        # 8. Đánh giá hiệu quả di chuyển
        efficiency_score = self._evaluate_movement_efficiency(pacman_node, pellet_nodes, ghost_nodes)
        
        # Tính điểm tổng hợp với trọng số được tối ưu
        score = (
            -1.5 * min_pellet_dist +           # Ưu tiên pellet gần nhất (giảm từ -2.0)
            -0.3 * avg_pellet_dist +           # Ưu tiên trung bình khoảng cách pellets (giảm từ -0.5)
            2.5 * min_ghost_dist +             # Tránh xa ghost gần nhất (giảm từ 3.0)
            0.8 * avg_ghost_dist +             # Tránh xa trung bình các ghosts (giảm từ 1.0)
            -25.0 * pellets_left +             # Ăn nhiều pellets (tăng từ -20.0)
            60.0 * pellet_progress +           # Thưởng tiến độ ăn pellets (tăng từ 50.0)
            position_score +                   # Điểm vị trí chiến lược
            density_score +                    # Điểm mật độ pellets
            safety_score +                     # Điểm an toàn
            power_pellet_score +               # Điểm power pellets
            efficiency_score                   # Điểm hiệu quả di chuyển
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
    def alpha_beta_pruning(self, pacman, ghostgroup, pellet_group, depth, alpha=-float('inf'), beta=float('inf'), is_maximizing_player=True):
        """
        Thuật toán Alpha-Beta Pruning cho game Pac-Man.
        - alpha: giá trị tốt nhất hiện tại cho người chơi tối đa (Max)
        - beta: giá trị tốt nhất hiện tại cho người chơi tối thiểu (Min)
        """
        if self.is_terminal_state(pacman, ghostgroup, pellet_group) or depth == 0:
            return self.evaluate(pacman, ghostgroup, pellet_group), None

        if is_maximizing_player:
            # Phần Maximizing Player (Pacman)
            max_eval = float('-inf')
            best_action = None
            for action in self.get_legal_actions(pacman, ghostgroup, pellet_group, True):
                next_pacman, next_ghostgroup, next_pellet_group = self.apply_action(pacman, ghostgroup, pellet_group, action, True)
                eval_score, _ = self.alpha_beta_pruning(next_pacman, next_ghostgroup, next_pellet_group, depth - 1, alpha, beta, False)
                if eval_score > max_eval:
                    max_eval ,best_action = eval_score, action
                alpha = max(alpha, max_eval)
                if alpha >= beta :
                    break 
            return max_eval, best_action
        else:
            # Phần Minimizing Player (Ghost)
            min_eval = float('inf')
            best_action = None
            for action in self.get_legal_actions(pacman, ghostgroup, pellet_group, False):
                next_pacman, next_ghostgroup, next_pellet_group = self.apply_action(pacman, ghostgroup, pellet_group, action, False)
                eval_score, _ = self.alpha_beta_pruning(next_pacman, next_ghostgroup, next_pellet_group, depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_action = action
                beta = min(beta, min_eval)
                if beta <= alpha:
                    break  
            return min_eval, best_action

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
    def hill_climbing(self, pacman, ghost_group, pellet_group, max_steps=50):
        # Tạo bản copy đơn giản để tránh lỗi đệ quy
        current_pacman = type('Pacman', (), {'node': pacman.node})()
        current_ghost_group = ghost_group  # Sử dụng trực tiếp để tránh lỗi copy
        current_pellet_group = pellet_group  # Sử dụng trực tiếp để tránh lỗi copy
        
        current_score = self.evaluate(current_pacman, current_ghost_group, current_pellet_group) 

        best_action = None
        path = []

        for step in range(max_steps):
            neighbors = self.get_legal_actions(current_pacman, current_ghost_group, current_pellet_group, True)
            if not neighbors:
                break
            
            next_states = [] 
            for action in neighbors: 
                next_pacman, next_ghost_group, next_pellet_group = self.apply_action(current_pacman, current_ghost_group, current_pellet_group, action, True)
                score = self.evaluate(next_pacman, next_ghost_group, next_pellet_group)
                next_states.append((score, action, next_pacman, next_ghost_group, next_pellet_group))

            next_states.sort(reverse=True, key=lambda x: x[0])
            
            best_neighbor_score, best_neighbor_action, best_neighbor_pacman, best_neighbor_ghost_group, best_neighbor_pellet_group = next_states[0]
            
            if best_neighbor_score <= current_score:
                break 

            current_pacman, current_ghost_group, current_pellet_group = best_neighbor_pacman, best_neighbor_ghost_group, best_neighbor_pellet_group
            current_score = best_neighbor_score

            path.append(best_neighbor_action)

            if best_action is None: 
                best_action = best_neighbor_action

        return best_action if best_action is not None else None
      
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
    def init_q_learning(self) : 
        if not hasattr(self,'q_agent') : 
            config = QLearningConfig(
                alpha = 0.2,        
                gamma = 0.8,       
                epsilon = 1.0,      
                epsilon_min = 0.02,  
                epsilon_decay = 0.995,  
            )
            self.q_agent = QLearningAgent(config)
            self.previous_pellet_count = 0
            self.episode_count = 0
            self.training_mode = True

            try:
                self.q_agent.load('q_table.json')
                print("SUCCESS: Loaded Q-table from file")
            except Exception as e:
                print("NEW: Starting with fresh Q-table")
    
    def set_training_mode(self, training):
        """Bật/tắt training mode"""
        self.training_mode = training
        if hasattr(self, 'q_agent'):
            if training:
                print("TRAINING: Training mode: ON")
            else:
                print("TESTING: Testing mode: ON (no Q-table updates)")

    def get_q_state(self, pacman, pellet_group, ghost_group):
        """
        State representation với 8 features cân bằng:
        - Tổng state space: 5×6×4×5×3×3×2×9 = 19,440 states (vẫn reasonable)
        """
        pellet_dir = self._get_pellet_direction(pacman.node, pellet_group)
        pellet_dist = self._get_pellet_distance_bin(pacman.node, pellet_group)
        ghost_status = self._get_ghost_status(pacman.node, ghost_group)
        env_type = self._get_environment_type(pacman.node, pellet_group)
        position_risk = self._get_position_risk(pacman.node)
        game_progress = self._get_game_progress(pellet_group)
        scared_ghost = self._get_scared_ghost(ghost_group)
        pacman_zone = self._get_pacman_zone(pacman.node)

        state = (
            pellet_dir,     # 0-4 (directions)
            pellet_dist,    # 0-5 (distance bins)
            ghost_status,   # 0-3 (threat levels)
            env_type,       # 0-4 (environment types)
            position_risk,  # 0-2 (position risks)
            game_progress,  # 0-2 (game phases)
            scared_ghost,   # 0-1 (scared ghost available)
            pacman_zone,    # 0-8 (9 zones trong maze)
        )

        return state

    def _get_pacman_zone(self, pacman_node):
        if not pacman_node:
            return 0

        MAZE_WIDTH = 27
        MAZE_HEIGHT = 31

        ZONE_WIDTH = MAZE_WIDTH // 3  # 9
        ZONE_HEIGHT = MAZE_HEIGHT // 3  # 10.33 -> 10

        x = int(pacman_node.position.x // TILEWIDTH)
        y = int(pacman_node.position.y // TILEHEIGHT)

        zone_x = min(2, x // ZONE_WIDTH)  # 0, 1, hoặc 2
        zone_y = min(2, y // ZONE_HEIGHT)  # 0, 1, hoặc 2

        zone = zone_y * 3 + zone_x

        return zone

    def _get_pellet_direction(self, pacman_node, pellet_group):
        """Lấy hướng pellet gần nhất {0-4}"""
        if not pacman_node or not pellet_group:
            return 0

        visible_pellets = [p for p in pellet_group.pelletList if p.visible]
        if not visible_pellets:
            return 0

        # Tìm pellet gần nhất
        nearest_pellet = min(visible_pellets, key=lambda p: self._calculate_distance(pacman_node, p.node))
        pellet_dir = self._get_direction_code(pacman_node, nearest_pellet.node)
        return pellet_dir

    def _get_pellet_distance_bin(self, pacman_node, pellet_group):
        """Khoảng cách đến pellet gần nhất {0-5}"""
        if not pacman_node or not pellet_group:
            return 5

        visible_pellets = [p for p in pellet_group.pelletList if p.visible]
        if not visible_pellets:
            return 5

        nearest_pellet = min(visible_pellets, key=lambda p: self._calculate_distance(pacman_node, p.node))
        dist = self._calculate_distance(pacman_node, nearest_pellet.node)

        if dist <= 2:
            return 0
        elif dist <= 4:
            return 1
        elif dist <= 6:
            return 2
        elif dist <= 8:
            return 3
        elif dist <= 12:
            return 4
        else:
            return 5


    def _get_ghost_status(self, pacman_node, ghost_group):
        """Trạng thái tổng hợp của ghosts {0-3}"""
        if not ghost_group or not hasattr(ghost_group, 'ghosts'):
            return 0

        min_dist = float('inf')
        scared_count = 0

        for ghost in ghost_group.ghosts:
            if hasattr(ghost, 'visible') and ghost.visible:
                dist = self._calculate_distance(pacman_node, ghost.node)
                min_dist = min(min_dist, dist)

                if hasattr(ghost, 'mode') and ghost.mode.current == FREIGHT:
                    scared_count += 1

        # 0: Safe (ghost ở xa >5 tiles)
        # 1: Caution (ghost ở khoảng cách trung bình 3-5 tiles, không scared)
        # 2: Danger (ghost ở rất gần ≤3 tiles, không scared)
        # 3: Opportunity (ghost ở gần ≤5 tiles và có scared)

        if min_dist > 5:
            return 0  # Safe - ghost ở xa
        elif min_dist > 3:
            return 1 if scared_count == 0 else 3  # Caution vs Opportunity
        else:  # min_dist <= 3
            return 2 if scared_count == 0 else 3  # Danger vs Opportunity

    def _get_environment_type(self, pacman_node, pellet_group):
        """Loại môi trường xung quanh {0-4}"""
        if not pacman_node:
            return 0

        px = int(pacman_node.position.x // TILEWIDTH)
        py = int(pacman_node.position.y // TILEHEIGHT)
        in_tunnel = (px <= 2 or px >= 25) and py == 17

        if in_tunnel:
            return 4  # Tunnel (highest priority)

        # Capsule check
        capsule_nearby = False
        if hasattr(pellet_group, 'powerpellets'):
            for pp in pellet_group.powerpellets:
                if getattr(pp, 'visible', True):
                    dist = self._calculate_distance(pacman_node, pp.node)
                    if dist <= 6:
                        capsule_nearby = True
                        break

        if capsule_nearby:
            return 3  # Capsule available

        # Dead end check
        neighbor_count = sum(1 for d in [UP, DOWN, LEFT, RIGHT]
                            if pacman_node.neighbors[d] is not None)

        if neighbor_count <= 1:
            return 2  # Dead end
        elif neighbor_count == 2:
            return 1  # Corridor
        else:
            return 0  # Open area 

    def _get_position_risk(self, pacman_node):
        """Mức độ rủi ro của vị trí hiện tại {0-2}"""
        # Dead end = high risk
        neighbor_count = sum(1 for d in [UP, DOWN, LEFT, RIGHT] 
                            if pacman_node.neighbors[d] is not None)
        
        if neighbor_count <= 1:
            return 2 
        elif neighbor_count == 2:
            return 1 
        else:
            return 0 

    def _get_game_progress(self, pellet_group):
        """Tiến độ game {0-2} - Early/Mid/Late game"""
        if not pellet_group or not hasattr(pellet_group, 'pelletList'):
            return 0

        visible_pellets = [p for p in pellet_group.pelletList if p.visible]
        total_pellets = len(pellet_group.pelletList)
        eaten_ratio = (total_pellets - len(visible_pellets)) / total_pellets if total_pellets > 0 else 0

        if eaten_ratio <= 0.3:
            return 0      # Early game: Tập trung ăn pellets an toàn
        elif eaten_ratio <= 0.7:
            return 1      # Mid game: Cân bằng pellets vs ghost
        else:
            return 2      # Late game: Tập trung hoàn thành, pellets quý giá

    def _get_scared_ghost(self, ghost_group):
        """Có ghost nào đang scared không {0-1}"""
        if not ghost_group or not hasattr(ghost_group, 'ghosts'):
            return 0

        for ghost in ghost_group.ghosts:
            if hasattr(ghost, 'mode') and ghost.mode.current == FREIGHT:
                return 1
        return 0

    
    def _get_direction_code(self, from_node, to_node):
        dx = to_node.position.x - from_node.position.x
        dy = to_node.position.y - from_node.position.y 

        if abs(dx) > abs(dy):
            return RIGHT if dx > 0 else LEFT 
        elif abs(dy) > 0:
            return DOWN if dy > 0 else UP  
        else:
            return STOP

    def get_legal_actions(self,pacman): 
        legal = [] 
        for direction in (UP,DOWN,LEFT,RIGHT):
            if self._can_move_in_direction(pacman.node,direction):
                legal.append(direction)
        return legal 

    def _calculate_step_reward(self, pacman, pellet_group, ghost_group, action, 
                                prev_pellet_count, current_pellet_count):
        """
        Hệ thống reward theo công thức toán học:
        R(s, a, s') = +10 (pellet) + 50 (capsule) + 500 (scared ghost) 
                     - 500 (death) + 500 (win) - 1 (step) + 0 (other)
        """
        reward = 0.0

        if current_pellet_count < prev_pellet_count:
            pellets_eaten = prev_pellet_count - current_pellet_count
            pellet_reward = 10.0 * pellets_eaten
            reward += pellet_reward
        
        capsule_reward = self._check_capsule_eaten(pacman, pellet_group)
        if capsule_reward > 0:
            reward += capsule_reward
        
        scared_ghost_reward = self._check_scared_ghost_eaten(pacman, ghost_group)
        if scared_ghost_reward > 0:
            reward += scared_ghost_reward
        
        if not pacman.alive:
            death_penalty = -500.0
            reward += death_penalty
            return reward
        
        if current_pellet_count == 0:
            win_reward = 500.0
            reward += win_reward
            return reward
        
        step_penalty = -1.0
        reward += step_penalty
        

        return reward
    
    def _check_capsule_eaten(self, pacman, pellet_group):
        """Kiểm tra xem có capsule nào được ăn không"""
        # Trả về 50 nếu Pacman vừa ăn 1 power pellet ở vị trí hiện tại
        for capsule in pellet_group.powerpellets:
            if pacman.collideCheck(capsule):
                return 50
        return 0

    def _check_scared_ghost_eaten(self, pacman, ghost_group):
        reward = 0
        for ghost in ghost_group.ghosts:
            if ghost.mode.current == FREIGHT:
                if pacman.collideCheck(ghost):
                    return 500
        return reward
    
    def q_learning_get_direction(self, pellet_group, ghost_group):
        """
        Hàm này trả về hướng di chuyển cho Pac-Man sử dụng Q-learning.
        Trả về: (action, episode_reward)
        episode_reward: tổng reward đã cộng dồn trong episode này

        Đoạn mã cơ bản là đúng, nhưng có một số điểm cần chú ý để training hiệu quả:
        - Đảm bảo self.training_mode = True khi muốn train (tức là cho phép agent học).
        - Gọi hàm này mỗi bước di chuyển của Pac-Man.
        - Khi Pac-Man chết hoặc ăn hết pellets, cần reset trạng thái Q-learning (done=True).
        - Nên lưu Q-table sau mỗi episode để không mất dữ liệu học.
        - Đảm bảo reward được tính hợp lý (xem lại hàm _calculate_step_reward).
        """
        if not hasattr(self, 'q_agent'):
            self.init_q_learning()
            self.prev_q_state = None
            self.prev_q_action = None
            self.prev_pellet_count = len([p for p in pellet_group.pelletList if p.visible])
        
        current_state = self.get_q_state(self.pacman, pellet_group, ghost_group)
        legal_actions = self.get_legal_actions(self.pacman)
        if not legal_actions:
            return STOP, 0.0

        # Luôn tính reward nếu đang trong training mode
        episode_reward = 0.0
        if self.training_mode:
            current_pellet_count = len([p for p in pellet_group.pelletList if p.visible])

            # Chỉ tính reward nếu có thay đổi trạng thái quan trọng
            should_calculate_reward = self.training_mode

            if should_calculate_reward:
                reward = self._calculate_step_reward(
                    self.pacman,
                    pellet_group,
                    ghost_group,
                    self.prev_q_action,
                    self.prev_pellet_count,
                    current_pellet_count
                )
                done = not self.pacman.alive or current_pellet_count == 0

                self.q_agent.add_reward(reward)
                episode_reward = self.q_agent._pending_reward


                self.q_agent.observe(current_state, legal_actions, done)

                if done:
                    self.prev_q_state = None
                    self.prev_q_action = None
                    self.q_agent.start_episode()
                    return STOP, episode_reward

            self.prev_pellet_count = current_pellet_count

        if self._last_pacman_pos is not None and self._last_pacman_pos != self.pacman.node:
            if (self._last_pacman_pos.neighbors[PORTAL] is not None and 
                self._last_pacman_pos.neighbors[PORTAL] == self.pacman.node):
                self._portal_used = True
            else:
                self._portal_used = False
        action = self.q_agent.selection_action(current_state, legal_actions)
        self.prev_q_state = current_state
        self.prev_q_action = action

        # Nếu không phải training mode, episode_reward = 0
        if not self.training_mode:
            episode_reward = 0.0
        
        return action, episode_reward

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
    def astar_pacman_direction(self, pacman, ghostgroup, pellet_group):
        """
        Thuật toán A* cải tiến cho Pac-Man online:
        - Tìm đường ngắn nhất đến pellet gần nhất
        - Tránh các node có ghost với penalty thay vì cấm hoàn toàn
        - Có fallback strategy khi không tìm được đường an toàn
        - Tối ưu cho real-time decision making
        """
        import heapq
        import time

        start_time = time.time()
        max_search_time = 0.01  # Giới hạn thời gian tìm kiếm (10ms)

        start_node = getattr(pacman, 'node', None)
        if start_node is None:
            return None

        # Lấy danh sách node của ghost còn sống với thông tin khoảng cách
        ghost_info = []
        for ghost in getattr(ghostgroup, 'ghosts', []):
            if getattr(ghost, 'alive', True) and getattr(ghost, 'node', None):
                ghost_node = ghost.node
                dist = self._calculate_distance(start_node, ghost_node)
                ghost_info.append((ghost_node, dist))

        # Lấy danh sách pellet còn lại
        pellet_nodes = [getattr(pellet, 'node', None) for pellet in getattr(pellet_group, 'pelletList', []) if getattr(pellet, 'visible', True)]
        pellet_nodes = [node for node in pellet_nodes if node is not None]
        if not pellet_nodes:
            return None

        # Hàm heuristic: khoảng cách Manhattan
        def heuristic(n1, n2):
            return abs(n1.position.x - n2.position.x) + abs(n1.position.y - n2.position.y)

        # Hàm tính cost với penalty cho ghost
        def get_node_cost(node):
            cost = 1  # Base cost
            for ghost_node, dist in ghost_info:
                ghost_dist = self._calculate_distance(node, ghost_node)
                if ghost_dist <= 1:
                    cost += 50  # Rất nguy hiểm
                elif ghost_dist <= 2:
                    cost += 20  # Nguy hiểm
                elif ghost_dist <= 3:
                    cost += 5   # Cảnh giác
            return cost

        # Tìm pellet gần nhất (theo heuristic)
        pellet_nodes = sorted(pellet_nodes, key=lambda n: heuristic(start_node, n))
        
        # Thử tìm đường đến 3 pellets gần nhất
        for target_node in pellet_nodes[:3]:
            if time.time() - start_time > max_search_time:
                break
                
            # A* search từ start_node đến target_node
            open_set = []
            heapq.heappush(open_set, (0 + heuristic(start_node, target_node), 0, start_node, None))
            came_from = {}
            g_score = {start_node: 0}
            closed_set = set()

            found = False
            while open_set and time.time() - start_time < max_search_time:
                _, cost, current, prev = heapq.heappop(open_set)
                
                if current in closed_set:
                    continue
                closed_set.add(current)
                
                if current == target_node:
                    found = True
                    break
                    
                for direction, neighbor in getattr(current, 'neighbors', {}).items():
                    if neighbor is None or neighbor in closed_set:
                        continue
                    
                    # Tính cost với penalty cho ghost
                    node_cost = get_node_cost(neighbor)
                    tentative_g = g_score[current] + node_cost
                    
                    if neighbor not in g_score or tentative_g < g_score[neighbor]:
                        g_score[neighbor] = tentative_g
                        priority = tentative_g + heuristic(neighbor, target_node)
                        heapq.heappush(open_set, (priority, tentative_g, neighbor, current))
                        came_from[neighbor] = (current, direction)
            
            if found:
                # Truy vết lại hướng đi đầu tiên từ start_node
                node = target_node
                while node != start_node:
                    if node not in came_from:
                        break
                    prev, direction = came_from[node]
                    if prev == start_node:
                        return direction
                    node = prev
        
        # Fallback: Nếu không tìm được đường an toàn, chọn hướng ít nguy hiểm nhất
        return self._get_safest_direction(start_node, ghost_info)

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
            
            elif algorithm_name == 'Alpha-Beta':
                # Sử dụng Alpha-Beta Pruning với depth tối ưu
                print("Using Alpha-Beta Pruning algorithm")
                eval_score, action = self.alpha_beta_pruning(self.pacman, ghost_group, pellet_group, 4, -float('inf'), float('inf'), True)
                if action is not None:
                    return action
                else:
                    return self._get_random_direction(current_node)
            elif algorithm_name == 'Hill Climbing':
                print("Using Hill Climbing algorithm")
                action = self.hill_climbing(self.pacman, ghost_group, pellet_group, 50)
                if action is not None:
                    return action
                else:
                    return self._get_random_direction(current_node)
            elif algorithm_name == 'Q-Learning':
                print("Using Q-Learning algorithm")
                action,_ = self.q_learning_get_direction(pellet_group, ghost_group)
                return action
            elif algorithm_name == 'A* Online':
                print("Using A* algorithm")
                action = self.astar_pacman_direction(self.pacman, ghost_group, pellet_group)
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

    def _evaluate_position_strategy(self, pacman_node, ghost_nodes):
        """Đánh giá vị trí chiến lược của Pacman"""
        if not pacman_node:
            return 0
            
        # Đếm số hướng có thể di chuyển (tránh đường cụt)
        available_directions = 0
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            if self._can_move_in_direction(pacman_node, direction):
                available_directions += 1
        
        # Thưởng khi có nhiều lựa chọn di chuyển
        mobility_bonus = available_directions * 5
        
        # Phạt khi ở góc (ít hướng di chuyển)
        corner_penalty = 0
        if available_directions <= 2:
            corner_penalty = -20
        
        # Thưởng khi ở vị trí trung tâm (có thể tiếp cận nhiều pellets)
        center_bonus = 0
        if available_directions >= 3:
            center_bonus = 10
            
        return mobility_bonus + corner_penalty + center_bonus

    def _evaluate_pellet_density(self, pacman_node, pellet_nodes):
        """Đánh giá mật độ pellets xung quanh Pacman"""
        if not pacman_node or not pellet_nodes:
            return 0
            
        # Đếm pellets trong bán kính 3
        nearby_pellets = 0
        for pellet_node in pellet_nodes:
            if self._calculate_distance(pacman_node, pellet_node) <= 3:
                nearby_pellets += 1
        
        # Thưởng khi có nhiều pellets gần
        density_bonus = nearby_pellets * 8
        
        # Thưởng thêm nếu có cluster pellets
        if nearby_pellets >= 3:
            density_bonus += 15
            
        return density_bonus

    def _evaluate_safety(self, pacman_node, ghost_nodes):
        """Đánh giá mức độ an toàn của Pacman"""
        if not pacman_node or not ghost_nodes:
            return 0
            
        min_ghost_dist = min(
            (self._calculate_distance(pacman_node, g) for g in ghost_nodes),
            default=float('inf')
        )
        
        # Hệ thống đánh giá an toàn nhiều cấp
        if min_ghost_dist <= 1:
            return -1000  # Rất nguy hiểm
        elif min_ghost_dist <= 2:
            return -250   # Nguy hiểm
        elif min_ghost_dist <= 3:
            return -50   # Cảnh giác
        elif min_ghost_dist <= 5:
            return 0     # Bình thường
        elif min_ghost_dist <= 8:
            return 40    # An toàn
        else:
            return 80    # Rất an toàn

    def _evaluate_power_pellets(self, pacman_node, pellet_group):
        """Đánh giá power pellets (nếu có trong game)"""
        if not pacman_node or not hasattr(pellet_group, 'powerPellets'):
            return 0
            
        # Tìm power pellets còn lại
        power_pellets = []
        if hasattr(pellet_group, 'powerPellets'):
            power_pellets = [pp for pp in pellet_group.powerPellets if getattr(pp, 'visible', True)]
        
        if not power_pellets:
            return 0
            
        # Tính khoảng cách đến power pellet gần nhất
        min_power_dist = min(
            (self._calculate_distance(pacman_node, pp.node) for pp in power_pellets if hasattr(pp, 'node')),
            default=float('inf')
        )
        
        # Thưởng khi gần power pellet (có thể ăn ghosts)
        if min_power_dist <= 3:
            return 30  # Thưởng cao cho power pellet
        elif min_power_dist <= 6:
            return 15  # Thưởng vừa
        else:
            return 0   # Không thưởng

    def _evaluate_movement_efficiency(self, pacman_node, pellet_nodes, ghost_nodes):
        """Đánh giá hiệu quả di chuyển dựa trên hướng tối ưu"""
        if not pacman_node or not pellet_nodes:
            return 0
            
        # Tìm hướng di chuyển tốt nhất (có nhiều pellets nhất)
        direction_scores = {}
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            if not self._can_move_in_direction(pacman_node, direction):
                continue
                
            next_node = pacman_node.neighbors[direction]
            if not next_node:
                continue
                
            # Đếm pellets có thể tiếp cận từ vị trí tiếp theo
            reachable_pellets = 0
            for pellet_node in pellet_nodes:
                dist = self._calculate_distance(next_node, pellet_node)
                if dist <= 5:  # Trong tầm 5 bước
                    reachable_pellets += 1
            
            # Trừ đi nếu có ghost gần
            ghost_penalty = 0
            for ghost_node in ghost_nodes:
                dist = self._calculate_distance(next_node, ghost_node)
                if dist <= 2:
                    ghost_penalty += 20
                elif dist <= 4:
                    ghost_penalty += 10
            
            direction_scores[direction] = reachable_pellets * 5 - ghost_penalty
        
        if not direction_scores:
            return 0
            
        # Trả về điểm của hướng tốt nhất
        return max(direction_scores.values())

  
   
       
       