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
        self.last_online_decision = 0 

        self.current_mode = "ONLINE"  
        self.planning_interval = 60.0   
        self.last_planning_time = 0     

        # Offline planning variables
        self.offline_plan = []
        self.offline_plan_index = 0
        self.offline_plan_valid = False

        # Performance tracking
        self.mode_switch_count = 0
        
        # Caching để tối ưu performance
        self._evaluation_cache = {}
        self._cache_max_size = 1000
        
        self.prev_q_state = None
        self.prev_q_action = None
        self._last_pacman_pos = None
        self.prev_pellet_count = 0
        self._portal_used = False
    def set_mode(self, mode):
        if mode in ["ONLINE", "OFFLINE"]:
            self.current_mode = mode
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
    def minimax(self, pacman, ghostgroup, pellet_group, depth, agent_index=0):
        if depth == 0 or self.is_terminal_state(pacman, ghostgroup, pellet_group):
            return self.evaluate(pacman, ghostgroup, pellet_group), None

        num_agents = 3  
        is_pacman = (agent_index == 0)
        
        actions = self.get_legal_actions_for_agent(pacman, ghostgroup, pellet_group, agent_index)
        
        if not actions:
            eval_score = self.evaluate(pacman, ghostgroup, pellet_group)
            return eval_score, None

        # Tính toán agent tiếp theo và depth tiếp theo
        next_agent = (agent_index + 1) % num_agents
        next_depth = depth - 1 if next_agent == 0 else depth
        
        if is_pacman:
            max_eval = float('-inf')
            best_action = actions[0]
            
            action_scores = []
            
            for i, action in enumerate(actions):
                next_state = self.apply_action_for_agent(
                    pacman, ghostgroup, pellet_group, action, agent_index
                )
                next_pacman, next_ghostgroup, next_pellet_group = next_state
                
                eval_score, _ = self.minimax(
                    next_pacman, next_ghostgroup, next_pellet_group, next_depth, next_agent
                )
                
                
                noise = i * 1.0  # Base noise để ưu tiên action đầu tiên
                if hasattr(pacman, 'previous_direction'):
                    prev_dir = getattr(pacman, 'previous_direction', None)
                    if prev_dir:
                        reverse_pairs = [(UP, DOWN), (DOWN, UP), (LEFT, RIGHT), (RIGHT, LEFT)]
                        if (action, prev_dir) in reverse_pairs:
                            noise = -10000  # PENALTY CỰC CỰC LỚN cho U-turn!
                        else:
                            noise += 100  # Bonus lớn cho non-U-turn
                
                eval_score += noise
                action_scores.append((action, eval_score))
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_action = action
            
            return max_eval, best_action
        else:
            
            min_eval = float('inf')
            best_action = actions[0]

            if len(actions) > 3:
                actions = self._get_best_ghost_actions(pacman, ghostgroup, actions, agent_index)[:3]
            
            for action in actions:
                
                next_state = self.apply_action_for_agent(
                    pacman, ghostgroup, pellet_group, action, agent_index
                )
                next_pacman, next_ghostgroup, next_pellet_group = next_state
                
                # Đệ quy với Pacman
                eval_score, _ = self.minimax(
                    next_pacman, next_ghostgroup, next_pellet_group, next_depth, next_agent
                )
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_action = action
            
            return min_eval, best_action

    def get_legal_actions_for_agent(self, pacman, ghostgroup, pellet_group, agent_index):
        actions = []
        
        if agent_index == 0:
            for direction in [UP, DOWN, LEFT, RIGHT]:
                if self._can_move_in_direction(pacman.node, direction):
                    actions.append(direction)
        else:            
            closest_ghosts = self._get_n_closest_ghosts(pacman, ghostgroup, n=2)
            ghost_idx = agent_index - 1  
            if not ghostgroup.ghosts:
                return []
            if ghost_idx < len(closest_ghosts):
                ghost = closest_ghosts[ghost_idx]
                if ghost and hasattr(ghost, 'node') and ghost.node:
                    for direction in [UP, DOWN, LEFT, RIGHT]:
                        if self._can_move_in_direction(ghost.node, direction):
                            actions.append(direction)    
        return actions 

    def _get_n_closest_ghosts(self, pacman, ghostgroup, n=2):
        if not ghostgroup.ghosts:
            return []
        
        ghost_distances = []
        for ghost in ghostgroup.ghosts:
            if ghost.node and pacman.node:
                distance = self._calculate_distance(pacman.node, ghost.node)
                ghost_distances.append((ghost, distance))
        
        ghost_distances.sort(key=lambda x: x[1])
        return [ghost for ghost, _ in ghost_distances[:n]]
    
    def _get_closest_ghost_to_pacman(self, pacman, ghostgroup):
        """Tìm ghost gần Pacman nhất (legacy - sử dụng _get_n_closest_ghosts)"""
        closest_ghosts = self._get_n_closest_ghosts(pacman, ghostgroup, n=1)
        return closest_ghosts[0] if closest_ghosts else None

    def _get_best_ghost_actions(self, pacman, ghostgroup, actions, agent_index):
        """Sắp xếp actions của ghost dựa trên mode (CHASE/SCATTER/FREIGHT)"""
        if not pacman.node:
            return actions
        
        closest_ghost = self._get_closest_ghost_to_pacman(pacman, ghostgroup)
        if not closest_ghost or not hasattr(closest_ghost, 'node'):
            return actions
        
        # Kiểm tra mode của ghost
        ghost_mode = getattr(closest_ghost, 'mode', None)
        current_mode = ghost_mode.current if ghost_mode and hasattr(ghost_mode, 'current') else CHASE
        
        action_scores = []
        for action in actions:
            if action in closest_ghost.node.neighbors and closest_ghost.node.neighbors[action]:
                next_node = closest_ghost.node.neighbors[action]
                distance = self._calculate_distance(next_node, pacman.node)
                
                if current_mode == FREIGHT:
                    import random
                    score = random.random()  # Random score
                elif current_mode == SCATTER:
                    score = -distance  # Âm để sort ngược → xa Pacman
                else:
                    score = distance  # Gần Pacman
                
                action_scores.append((action, score))
        
        action_scores.sort(key=lambda x: x[1])
        return [action for action, _ in action_scores]

    def apply_action_for_agent(self, pacman, ghostgroup, pellet_group, action, agent_index):

        if agent_index == 0:
            if action == STOP:
                return pacman, ghostgroup, pellet_group
            
            if action not in pacman.node.neighbors or pacman.node.neighbors[action] is None:
                return pacman, ghostgroup, pellet_group
            
            new_pacman_node = pacman.node.neighbors[action]
            new_pacman = type('Pacman', (), {
                'node': new_pacman_node,
                'alive': getattr(pacman, 'alive', True),
                'direction': action,  # Direction MỚI
                'previous_direction': getattr(pacman, 'direction', None),
                'previous': pacman.node  # LƯU node hiện tại làm previous (CRITICAL FIX)
            })()
            new_pellet_group = self._simulate_eat_pellets_fast(new_pacman, pellet_group)
            
            return new_pacman, ghostgroup, new_pellet_group
        else:
            # ===== DI CHUYỂN 2 GHOST GẦN NHẤT =====
            closest_ghosts = self._get_n_closest_ghosts(pacman, ghostgroup, n=2)
            ghost_idx = agent_index - 1
            
            if ghost_idx >= len(closest_ghosts):
                return pacman, ghostgroup, pellet_group
                
            target_ghost = closest_ghosts[ghost_idx]
            
            if not target_ghost or not hasattr(target_ghost, 'node') or action == STOP:
                return pacman, ghostgroup, pellet_group
            
            # Kiểm tra có thể di chuyển
            if action not in target_ghost.node.neighbors or target_ghost.node.neighbors[action] is None:
                return pacman, ghostgroup, pellet_group
            
            # TỐI ƯU: Chỉ cập nhật ghost này, các ghost khác giữ nguyên reference
            new_ghost_node = target_ghost.node.neighbors[action]
            new_ghost = type('Ghost', (), {
                'node': new_ghost_node,
                'alive': getattr(target_ghost, 'alive', True),
                'mode': getattr(target_ghost, 'mode', None)
            })()
            
            # Tạo ghost group mới với ghost đã di chuyển
            new_ghosts = []
            for g in ghostgroup.ghosts:
                if g == target_ghost:
                    new_ghosts.append(new_ghost)
                else:
                    new_ghosts.append(g)  # Giữ nguyên reference (không copy)
            
            new_ghostgroup = type('GhostGroup', (), {'ghosts': new_ghosts})()
            return pacman, new_ghostgroup, pellet_group

    def _simulate_eat_pellets_fast(self, pacman, pellet_group):
        pacman_node = getattr(pacman, 'node', None)
        if not pacman_node:
            return pellet_group
        
        pellets_left = []
        if hasattr(pellet_group, 'pelletList'):
            for pellet in pellet_group.pelletList:
                pellet_node = getattr(pellet, 'node', None)
                if pellet_node and pellet_node != pacman_node and getattr(pellet, 'visible', True):
                    pellets_left.append(pellet) 
        
        new_pellet_group = type('PelletGroup', (), {
            'pelletList': pellets_left
        })()
        
        return new_pellet_group

    def is_terminal_state(self, pacman, ghostgroup, pellet_group):
        for ghost in ghostgroup.ghosts:
            if ghost.node == pacman.node:
                return True

        pellets_left = any(pellet.visible for pellet in pellet_group.pelletList)
        if not pellets_left:
            return True

        return False

    def evaluate(self, pacman, ghostgroup, pellet_group):
        pacman_node = getattr(pacman, 'node', None)
        if pacman_node is None:
            return -10000
            
        revisit_penalty = 0
        
        freight_ghosts = []
        normal_ghosts = []
        spawn_ghosts = [] 
        
        for ghost in getattr(ghostgroup, 'ghosts', []):
            if not getattr(ghost, 'alive', True):
                continue
            ghost_node = getattr(ghost, 'node', None)
            if ghost_node is None:
                continue
                
            ghost_mode = getattr(ghost, 'mode', None)
            if ghost_mode and hasattr(ghost_mode, 'current'):
                if ghost_mode.current == FREIGHT:
                    freight_ghosts.append(ghost_node)
                elif ghost_mode.current == SPAWN:
                    spawn_ghosts.append(ghost_node)  
                else:
                    normal_ghosts.append(ghost_node)
            else:
                normal_ghosts.append(ghost_node)
        
        power_pellet_nodes = []
        normal_pellet_nodes = []
        
        for pellet in getattr(pellet_group, 'pelletList', []):
            if not getattr(pellet, 'visible', True):
                continue
            pellet_node = getattr(pellet, 'node', None)
            if pellet_node is None:
                continue
            
            pellet_name = getattr(pellet, 'name', None)
            if pellet_name == POWERPELLET:
                power_pellet_nodes.append(pellet_node)
            else:
                normal_pellet_nodes.append(pellet_node)
        
        pellet_nodes = power_pellet_nodes + normal_pellet_nodes  

        for ghost_node in normal_ghosts:
            if ghost_node == pacman_node:
                return -10000  
        
        for ghost_node in freight_ghosts:
            if ghost_node == pacman_node:
                return 5000  

        if len(pellet_nodes) == 0:
            return 10000


        power_pellet_dist = 100
        if power_pellet_nodes:
            power_distances = [self._calculate_distance(pacman_node, p) for p in power_pellet_nodes]
            power_pellet_dist = min(power_distances)
        
        pellet_distances = [self._calculate_distance(pacman_node, p) for p in pellet_nodes]
        min_pellet_dist = min(pellet_distances) if pellet_distances else 100
        avg_pellet_dist = sum(pellet_distances) / len(pellet_distances) if pellet_distances else 100
        
        normal_ghost_dist = 100 
        if normal_ghosts:
            ghost_distances = [self._calculate_distance(pacman_node, g) for g in normal_ghosts]
            normal_ghost_dist = min(ghost_distances)
        

        freight_ghost_dist = 100  
        if freight_ghosts:
            freight_distances = [self._calculate_distance(pacman_node, g) for g in freight_ghosts]
            freight_ghost_dist = min(freight_distances)
        
        
        # Penalty quay đầu
        reverse_penalty = 0
        if hasattr(pacman, 'direction') and hasattr(pacman, 'previous_direction'):
            current_dir = getattr(pacman, 'direction', None)
            prev_dir = getattr(pacman, 'previous_direction', None)
            
            if current_dir and prev_dir and current_dir != prev_dir:
                reverse_pairs = [(UP, DOWN), (DOWN, UP), (LEFT, RIGHT), (RIGHT, LEFT)]
                if (current_dir, prev_dir) in reverse_pairs:
                    
                    should_penalize = True
                    if normal_ghosts:
                        min_normal_dist = min([self._calculate_distance(pacman_node, g) for g in normal_ghosts])
                        if min_normal_dist < 4:  # Cho phép U-turn khi ghost gần < 4 tiles
                            should_penalize = False
                    
                    if should_penalize:
                        reverse_penalty = 0
        
        pellets_left = len(pellet_nodes)
        total_pellets = getattr(pellet_group, 'total_pellets', pellets_left)
        pellet_progress = (total_pellets - pellets_left) / total_pellets if total_pellets > 0 else 0
        
        position_score = self._evaluate_position_strategy(pacman_node, normal_ghosts + freight_ghosts)
        
        density_score = self._evaluate_pellet_density(pacman_node, pellet_nodes)
        
        safety_score = self._evaluate_safety(pacman_node, normal_ghosts)
        

        ghost_avoidance_score = 0
        if normal_ghosts:
            if normal_ghost_dist < 2:
                ghost_avoidance_score = -50000 / (normal_ghost_dist + 0.1)  
            elif normal_ghost_dist < 4:
                ghost_avoidance_score = -15000 / (normal_ghost_dist + 0.1)
            elif normal_ghost_dist < 7:
                ghost_avoidance_score = -3000 / (normal_ghost_dist + 0.1)  
                ghost_avoidance_score = -500 / (normal_ghost_dist + 0.1)    
            else:
                ghost_avoidance_score = 5.0 * normal_ghost_dist            
        
        freight_bonus = 0
        if freight_ghosts and len(freight_ghosts) > 0:
            # Chỉ ưu tiên ăn freight ghost khi RẤT an toàn và gần
            if freight_ghost_dist < 5:  # Giảm từ < 8, chỉ đuổi khi RẤT GẦN
                freight_bonus = 2000 / (freight_ghost_dist + 0.5)  # Giảm mạnh từ 3000
                if normal_ghosts and normal_ghost_dist < 8:  # Tăng từ < 7
                    freight_bonus = 0  # Bỏ qua hoàn toàn nếu có ghost nguy hiểm gần
                # Thêm penalty nếu freight ghost quá xa so với pellet gần nhất
                if freight_ghost_dist > min_pellet_dist * 2:
                    freight_bonus = 0  # Ưu tiên pellet hơn freight ghost xa
            else:
                freight_bonus = 0  # Không đuổi theo freight ghost xa
        else:
            # Không có freight ghost → KHÔNG được đuổi ghost bình thường
            freight_bonus = 0


        power_pellet_bonus = 0
        if power_pellet_nodes:
            if normal_ghosts:
                if normal_ghost_dist < 3:
                    power_pellet_bonus = 2000 / (power_pellet_dist + 0.5)  # Tăng từ 1000
                elif normal_ghost_dist < 5:
                    power_pellet_bonus = 800 / (power_pellet_dist + 0.5)   # Tăng từ 400
                elif normal_ghost_dist < 8:
                    power_pellet_bonus = 300 / (power_pellet_dist + 1)     # Tăng từ 200
            else:
                power_pellet_bonus = -0.5 * power_pellet_dist  # Giảm từ -1.0
        
        score = (
            15.0 * ghost_avoidance_score +   # Tăng trọng số từ 2.0 → 10.0 (QUAN TRỌNG NHẤT)
            power_pellet_bonus +             # BONUS ĐỘNG dựa trên ghost
            freight_bonus +                  # ĂN GHOST FREIGHT (khi an toàn)
            -1.0 * min_pellet_dist +         # Giảm từ -0.5 (ít ưu tiên hơn)
            -0.5 * avg_pellet_dist +         # Giảm từ -0.3
            -8.0 * pellets_left +            # Giảm từ -8.0
            40.0 * pellet_progress +         # Giảm từ 50.0
            reverse_penalty +                
            revisit_penalty +                
            position_score * 0.3 +           # Giảm trọng số
            density_score * 0.5 +            # Giảm trọng số
            safety_score * 0.8               # Giảm trọng số
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
            new_pacman_node = pacman.node.neighbors[action]
            new_pacman = type('Pacman', (), {'node': new_pacman_node})()
            return new_pacman, ghostgroup, pellet_group
        else:
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
    def alpha_beta_pruning(self, pacman, ghostgroup, pellet_group, depth, alpha=-float('inf'), beta=float('inf'), agent_index=0):
        if depth == 0 or self.is_terminal_state(pacman, ghostgroup, pellet_group):
            return self.evaluate(pacman, ghostgroup, pellet_group), None

        num_agents = 3
        is_pacman = (agent_index == 0)
        
        actions = self.get_legal_actions_for_agent(pacman, ghostgroup, pellet_group, agent_index)
        
        if not actions:
            eval_score = self.evaluate(pacman, ghostgroup, pellet_group)
            return eval_score, None

        next_agent = (agent_index + 1) % num_agents
        next_depth = depth - 1 if next_agent == 0 else depth
        
        if is_pacman:
            max_eval = float('-inf')
            best_action = actions[0]
            
            for action in actions:
                next_state = self.apply_action_for_agent(
                    pacman, ghostgroup, pellet_group, action, agent_index
                )
                next_pacman, next_ghostgroup, next_pellet_group = next_state
                
                eval_score, _ = self.alpha_beta_pruning(
                    next_pacman, next_ghostgroup, next_pellet_group, 
                    next_depth, alpha, beta, next_agent
                )
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_action = action
                
                alpha = max(alpha, max_eval)
                if alpha >= beta:
                    break  
            
            return max_eval, best_action
        else:
            min_eval = float('inf')
            best_action = actions[0]

            if len(actions) > 3:
                actions = self._get_best_ghost_actions(pacman, ghostgroup, actions, agent_index)[:3]
            
            for action in actions:
                next_state = self.apply_action_for_agent(
                    pacman, ghostgroup, pellet_group, action, agent_index
                )
                next_pacman, next_ghostgroup, next_pellet_group = next_state
                
                eval_score, _ = self.alpha_beta_pruning(
                    next_pacman, next_ghostgroup, next_pellet_group,
                    next_depth, alpha, beta, next_agent
                )
                
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
        REWARD ĐƯỢC TĂNG để học nhanh hơn trong 500-1000 episodes:
        - Pellet: 10 → 50 (động viên ăn pellets)
        - Capsule: 50 → 150 (khuyến khích dùng power-ups)
        - Ghost: 500 → 1000 (ưu tiên ăn ghosts khi scared)
        - Death: -500 → -1000 (penalty mạnh hơn)
        - Win: 500 → 2000 (động viên hoàn thành)
        - Step: -1 → -0.5 (giảm penalty để không sợ di chuyển)
        """
        reward = 0.0

        if current_pellet_count < prev_pellet_count:
            pellets_eaten = prev_pellet_count - current_pellet_count
            pellet_reward = 50.0 * pellets_eaten  # TĂNG x5
            reward += pellet_reward
        
        capsule_reward = self._check_capsule_eaten(pacman, pellet_group)
        if capsule_reward > 0:
            reward += capsule_reward * 3  # 50 → 150
        
        scared_ghost_reward = self._check_scared_ghost_eaten(pacman, ghost_group)
        if scared_ghost_reward > 0:
            reward += scared_ghost_reward * 2  # 500 → 1000
        
        if not pacman.alive:
            death_penalty = -1000.0  # TĂNG penalty
            reward += death_penalty
            return reward
        
        if current_pellet_count == 0:
            win_reward = 2000.0  # TĂNG x4
            reward += win_reward
            return reward
        
        step_penalty = -0.5  # GIẢM penalty
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
        Hàm Q-learning với flow đúng chuẩn:
        1. Chọn action từ state hiện tại
        2. Tính reward từ action trước đó
        3. Update Q-table với (prev_state, prev_action, reward, current_state)
        
        Trả về: (action, step_reward)
        """
        # Khởi tạo Q-agent nếu chưa có
        if not hasattr(self, 'q_agent'):
            self.init_q_learning()
            self.prev_q_state = None
            self.prev_q_action = None
            self.prev_pellet_count = len([p for p in pellet_group.pelletList if p.visible])
        
        # Lấy state và legal actions hiện tại
        current_state = self.get_q_state(self.pacman, pellet_group, ghost_group)
        legal_actions = self.get_legal_actions(self.pacman)
        if not legal_actions:
            return STOP, 0.0

        step_reward = 0.0
        
        # Training mode: Tính reward và update Q-table
        if self.training_mode and self.prev_q_state is not None:
            current_pellet_count = len([p for p in pellet_group.pelletList if p.visible])
            
            # Tính reward cho transition (prev_state, prev_action) -> current_state
            step_reward = self._calculate_step_reward(
                self.pacman,
                pellet_group,
                ghost_group,
                self.prev_q_action,
                self.prev_pellet_count,
                current_pellet_count
            )
            
            # Check terminal state
            done = not self.pacman.alive or current_pellet_count == 0
            
            # Update Q-table
            self.q_agent.add_reward(step_reward)
            self.q_agent.observe(current_state, legal_actions, done)
            
            # Update pellet count
            self.prev_pellet_count = current_pellet_count
            
            # Nếu done, reset và return STOP
            if done:
                self.prev_q_state = None
                self.prev_q_action = None
                self.q_agent.start_episode()
                return STOP, step_reward

        # Chọn action mới từ current_state
        if self._last_pacman_pos is not None and self._last_pacman_pos != self.pacman.node:
            if (self._last_pacman_pos.neighbors[PORTAL] is not None and 
                self._last_pacman_pos.neighbors[PORTAL] == self.pacman.node):
                self._portal_used = True
            else:
                self._portal_used = False
        
        action = self.q_agent.selection_action(current_state, legal_actions)
        
        # Lưu state và action cho lần sau
        self.prev_q_state = current_state
        self.prev_q_action = action
        
        return action, step_reward

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
        Thuật toán A* Online cho Pac-Man:
        - Heuristic: Manhattan distance
        - Cost: có penalty khi gần ghost
        - Ưu tiên ăn nhiều pellet trên đường đi
        """
        import heapq
        
        start_node = getattr(pacman, 'node', None)
        if not start_node:
            return STOP
        
        # Thu thập ghost nodes (chỉ ghost bình thường, không phải FREIGHT)
        dangerous_ghost_nodes = []
        for ghost in getattr(ghostgroup, 'ghosts', []):
            if getattr(ghost, 'alive', True):
                ghost_mode = getattr(ghost, 'mode', None)
                current_mode = ghost_mode.current if ghost_mode and hasattr(ghost_mode, 'current') else CHASE
                # Chỉ coi ghost là nguy hiểm nếu không ở chế độ FREIGHT
                if current_mode != FREIGHT:
                    ghost_node = getattr(ghost, 'node', None)
                    if ghost_node:
                        dangerous_ghost_nodes.append(ghost_node)
        
        # Thu thập pellet nodes
        pellet_nodes = []
        pellet_nodes_set = set()
        for pellet in getattr(pellet_group, 'pelletList', []):
            if getattr(pellet, 'visible', True):
                pellet_node = getattr(pellet, 'node', None)
                if pellet_node:
                    pellet_nodes.append(pellet_node)
                    pellet_nodes_set.add(pellet_node)
        
        if not pellet_nodes:
            return STOP
        
        # Hàm tính cost của node
        def calculate_node_cost(node):
            BASE_COST = 1
            
            # Bonus nếu node có pellet (ưu tiên ăn nhiều pellet)
            pellet_bonus = -0.5 if node in pellet_nodes_set else 0
            
            if not dangerous_ghost_nodes:
                return BASE_COST + pellet_bonus
            
            # Tìm ghost gần nhất
            min_ghost_dist = min(
                self._calculate_distance(node, ghost_node) 
                for ghost_node in dangerous_ghost_nodes
            )
            
            # Penalty theo khoảng cách ghost (né ghost)
            if min_ghost_dist == 0:
                return 100  # Node có ghost - tránh tuyệt đối
            elif min_ghost_dist <= 2:
                return BASE_COST + 50 + pellet_bonus
            elif min_ghost_dist <= 4:
                return BASE_COST + 20 + pellet_bonus
            elif min_ghost_dist <= 6:
                return BASE_COST + 5 + pellet_bonus
            else:
                return BASE_COST + pellet_bonus
        
        # Tìm pellet gần nhất làm target
        target_pellet = min(
            pellet_nodes, 
            key=lambda p: self._calculate_distance(start_node, p)
        )
        
        # Khởi tạo A* search
        open_set = []
        h_start = self._calculate_distance(start_node, target_pellet)
        heapq.heappush(open_set, (h_start, 0, start_node))
        
        came_from = {}
        g_score = {start_node: 0}
        closed_set = set()
        
        # A* main loop
        while open_set:
            f_score, g_current, current_node = heapq.heappop(open_set)
            
            # Skip nếu đã xét
            if current_node in closed_set:
                continue
            
            closed_set.add(current_node)
            
            # Kiểm tra đích
            if current_node == target_pellet:
                # Reconstruct path
                node = target_pellet
                while node in came_from:
                    prev_node, direction = came_from[node]
                    if prev_node == start_node:
                        return direction
                    node = prev_node
                return STOP
            
            # Duyệt các neighbor
            for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
                neighbor = current_node.neighbors.get(direction)
                
                if neighbor is None or neighbor in closed_set:
                    continue
                
                # Tính cost với penalty ghost và bonus pellet
                edge_cost = calculate_node_cost(neighbor)
                tentative_g = g_score[current_node] + edge_cost
                
                # Cập nhật nếu tìm được đường tốt hơn
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = (current_node, direction)
                    g_score[neighbor] = tentative_g
                    
                    # f(n) = g(n) + h(n)
                    h_score = self._calculate_distance(neighbor, target_pellet)
                    f_score = tentative_g + h_score
                    
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))
        
        # Không tìm thấy path
        return STOP

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
        """Lấy direction từ thuật toán ONLINE đã chọn"""
        
        current_node = self.pacman.node
        algorithm_name = getattr(self.pacman, 'pathfinder_name', 'A*')        
        try:
            if algorithm_name == 'Minimax':
                current_direction = getattr(self.pacman, 'direction', None)
                pacman_with_dir = type('Pacman', (), {
                    'node': self.pacman.node,
                    'alive': getattr(self.pacman, 'alive', True),
                    'direction': current_direction,
                    'previous_direction': current_direction  
                })()
                eval_score, action = self.minimax(pacman_with_dir, ghost_group, pellet_group, depth=2, agent_index=0)
                return action

            
            elif algorithm_name == 'Alpha-Beta':
                # Tạo Pacman object với direction
                current_direction = getattr(self.pacman, 'direction', None)
                pacman_with_dir = type('Pacman', (), {
                    'node': self.pacman.node,
                    'alive': getattr(self.pacman, 'alive', True),
                    'direction': current_direction,
                    'previous_direction': current_direction
                })()
                
                # Gọi Alpha-Beta với multi-agent (agent_index=0 cho Pacman)
                eval_score, action = self.alpha_beta_pruning(
                    pacman_with_dir, ghost_group, pellet_group, 
                    depth=2, alpha=-float('inf'), beta=float('inf'), agent_index=0
                )
                
                return action

            elif algorithm_name == 'Hill Climbing':
                action = self.hill_climbing(self.pacman, ghost_group, pellet_group, 50)
                return action

            elif algorithm_name == 'Q-Learning':
                action,_ = self.q_learning_get_direction(pellet_group, ghost_group)
                return action
            elif algorithm_name == 'A* Online':
                print("A* Online")
                action = self.astar_pacman_direction(self.pacman, ghost_group, pellet_group)
                return action

            else:
                return self._get_random_direction(current_node)
                    
        except Exception as e:
            print(f"[ONLINE] Algorithm {algorithm_name} error: {e}")
            return self._get_random_direction(current_node)

    def _can_move_in_direction(self, current_node, direction):
        """Kiểm tra có thể di chuyển theo hướng không"""

        if direction == PORTAL:
            return current_node.neighbors[PORTAL] is not None
        else:
            return (current_node.neighbors[direction] is not None and
                    PACMAN in current_node.access[direction])

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
        if node1 is None or node2 is None:
            return float('inf')

        dx = abs(node1.position.x - node2.position.x)
        dy = abs(node1.position.y - node2.position.y)
        return (dx + dy) // 16

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
            
        nearby_pellets = 0
        for pellet_node in pellet_nodes:
            if self._calculate_distance(pacman_node, pellet_node) <= 3:
                nearby_pellets += 1
        
        density_bonus = nearby_pellets * 8
        
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
        

        if min_ghost_dist <= 1:
            return -1000  
        elif min_ghost_dist <= 2:
            return -250  
        elif min_ghost_dist <= 3:
            return -50  
        elif min_ghost_dist <= 5:
            return 0    
        elif min_ghost_dist <= 8:
            return 40   
        else:
            return 80   

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
        
        if min_power_dist <= 3:
            return 30  
        elif min_power_dist <= 6:
            return 15 
        else:
            return 0  

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

  
   
       
       