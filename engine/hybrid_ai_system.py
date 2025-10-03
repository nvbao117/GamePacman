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
                # Pac-Man di chuyển - CHỈ di chuyển Pac-Man, KHÔNG di chuyển Ghost
                next_pacman, next_ghostgroup, next_pellet_group = self.apply_action_for_agent(
                    pacman, ghostgroup, pellet_group, action, 0
                )
                
                # Đệ quy - Ghost sẽ di chuyển ở bước tiếp theo
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
                # Ghost di chuyển - CHỈ di chuyển Ghost này
                next_pacman, next_ghostgroup, next_pellet_group = self.apply_action_for_agent(
                    pacman, ghostgroup, pellet_group, action, agent_index
                )
                
                # Đệ quy - Agent tiếp theo sẽ di chuyển
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
            for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
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
                    for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
                        if self._can_move_in_direction(ghost.node, direction):
                            actions.append(direction)    
        return actions 

    def _simulate_ghost_action(self, pacman, ghost_group, pellet_group, ghost_action, agent_index):
        """
        Mô phỏng di chuyển của một Ghost cụ thể
        """
        if agent_index == 0:
            # Nếu là Pac-Man, sử dụng _simulate_full_turn
            return self._simulate_full_turn(pacman, ghost_group, pellet_group, ghost_action)
        else:
            # Nếu là Ghost, chỉ di chuyển Ghost đó
            return self.apply_action_for_agent(pacman, ghost_group, pellet_group, ghost_action, agent_index)
    
    def _simulate_full_turn(self, pacman, ghost_group, pellet_group, pacman_action):
        """
        Mô phỏng một lượt chơi hoàn chỉnh:
        - Pac-Man di chuyển theo action
        - Ghost di chuyển theo AI của chúng
        - Trả về trạng thái mới
        """
        # 1. Di chuyển Pac-Man
        next_pacman, _, next_pellet_group = self.apply_action_for_agent(
            pacman, ghost_group, pellet_group, pacman_action, 0
        )
        
        # 2. Mô phỏng di chuyển của tất cả Ghost
        next_ghost_group = self._simulate_ghost_movements(next_pacman, ghost_group)
        
        return next_pacman, next_ghost_group, next_pellet_group
    
    def _simulate_ghost_movements(self, pacman, ghost_group):
        """
        Mô phỏng di chuyển của tất cả Ghost trong một turn
        """
        if not ghost_group or not hasattr(ghost_group, 'ghosts'):
            return ghost_group
            
        new_ghosts = []
        for ghost in ghost_group.ghosts:
            if not ghost or not hasattr(ghost, 'node') or not ghost.node:
                new_ghosts.append(ghost)
                continue
                
            # Tìm hướng di chuyển tốt nhất cho ghost này dựa trên mode
            best_direction = self._get_ghost_best_direction(ghost, pacman, ghost_group)
            
            # Di chuyển ghost
            if best_direction in ghost.node.neighbors and ghost.node.neighbors[best_direction]:
                new_ghost_node = ghost.node.neighbors[best_direction]
                new_ghost = type('Ghost', (), {
                    'node': new_ghost_node,
                    'alive': getattr(ghost, 'alive', True),
                    'mode': getattr(ghost, 'mode', None),
                    'name': getattr(ghost, 'name', GHOST),
                    'color': getattr(ghost, 'color', RED),
                    'goal': getattr(ghost, 'goal', None),
                    'pacman': pacman,
                    'blinky': self._get_blinky_from_group(ghost_group),
                    'spawnNode': getattr(ghost, 'spawnNode', None),
                    'directions': getattr(ghost, 'directions', {}),
                    'position': new_ghost_node.position
                })()
                new_ghosts.append(new_ghost)
            else:
                new_ghosts.append(ghost)
        
        # Tạo ghost group mới
        new_ghost_group = type('GhostGroup', (), {'ghosts': new_ghosts})()
        return new_ghost_group
    
    def _get_ghost_best_direction(self, ghost, pacman, ghost_group):
        """
        Tìm hướng di chuyển tốt nhất cho một ghost dựa trên mode
        """
        if not ghost.node or not pacman.node:
            return STOP
            
        valid_directions = []
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            if direction in ghost.node.neighbors and ghost.node.neighbors[direction]:
                valid_directions.append(direction)
        
        if not valid_directions:
            return STOP
            
        # Xác định goal dựa trên mode và loại ghost
        goal = self._get_ghost_goal(ghost, pacman, ghost_group)
        
        # Tìm hướng gần nhất với goal
        best_direction = STOP
        min_distance = float('inf')
        
        for direction in valid_directions:
            next_node = ghost.node.neighbors[direction]
            if next_node:
                distance = (next_node.position - goal).magnitudeSquared()
                if distance < min_distance:
                    min_distance = distance
                    best_direction = direction
        
        return best_direction if best_direction != STOP else valid_directions[0]
    
    def _get_ghost_goal(self, ghost, pacman, ghost_group):

        from constants import SCATTER, CHASE, FREIGHT, SPAWN
        from objects.vector import Vector2
        
        # Lấy mode hiện tại (mặc định là CHASE nếu không có)
        current_mode = getattr(ghost, 'mode', None)
        if hasattr(current_mode, 'current'):
            mode = current_mode.current
        else:
            mode = CHASE  # Mặc định
            
        ghost_name = getattr(ghost, 'name', GHOST)
        
        if mode == SCATTER:
            # Mode SCATTER: di chuyển về góc (theo code gốc)
            if ghost_name == PINKY:
                return Vector2(0, TILEHEIGHT * NROWS)  # Góc dưới trái
            elif ghost_name == INKY:
                return Vector2(TILEWIDTH * NCOLS, TILEHEIGHT * NROWS)  # Góc dưới phải
            elif ghost_name == CLYDE:
                return Vector2(0, TILEHEIGHT * NROWS)  # Góc dưới trái (giống Pinky)
            else:  # BLINKY
                return Vector2(0, 0)  # Góc trên trái (khác với code cũ)
                
        elif mode == CHASE:
            # Mode CHASE: di chuyển theo Pac-Man
            if ghost_name == PINKY:
                # Pinky: 4 tiles trước Pac-Man
                pacman_direction = getattr(pacman, 'direction', RIGHT)
                pacman_pos = pacman.node.position if pacman.node else Vector2(0, 0)
                if hasattr(pacman, 'directions') and pacman_direction in pacman.directions:
                    return pacman_pos + pacman.directions[pacman_direction] * TILEWIDTH * 4
                else:
                    return pacman_pos
            elif ghost_name == INKY:
                # Inky: phức tạp hơn, cần Blinky
                blinky = self._get_blinky_from_group(ghost_group)
                pacman_pos = pacman.node.position if pacman.node else Vector2(0, 0)
                if blinky and blinky.node:
                    vec1 = pacman_pos + pacman.directions.get(pacman.direction, Vector2(1, 0)) * TILEWIDTH * 2
                    vec2 = (vec1 - blinky.node.position) * 2
                    return blinky.node.position + vec2
                else:
                    return pacman_pos
            elif ghost_name == CLYDE:
                # Clyde: di chuyển về Pac-Man nếu xa, scatter nếu gần (theo code gốc)
                pacman_pos = pacman.node.position if pacman.node else Vector2(0, 0)
                d = pacman_pos - ghost.node.position
                ds = d.magnitudeSquared()
                if ds <= (TILEWIDTH * 8) ** 2:
                    # Gần Pac-Man -> scatter (góc dưới trái)
                    return Vector2(0, TILEHEIGHT * NROWS)
                else:
                    # Xa Pac-Man -> chase (4 tiles trước Pac-Man)
                    pacman_direction = getattr(pacman, 'direction', RIGHT)
                    if hasattr(pacman, 'directions') and pacman_direction in pacman.directions:
                        return pacman_pos + pacman.directions[pacman_direction] * TILEWIDTH * 4
                    else:
                        return pacman_pos
            else:  # BLINKY
                # Blinky: trực tiếp về Pac-Man
                pacman_pos = pacman.node.position if pacman.node else Vector2(0, 0)
                return pacman_pos
                
        elif mode == FREIGHT:
            # Mode FREIGHT: di chuyển ngẫu nhiên
            import random
            valid_directions = [d for d in [UP, DOWN, LEFT, RIGHT, PORTAL] 
                              if d in ghost.node.neighbors and ghost.node.neighbors[d]]
            if valid_directions:
                return ghost.node.neighbors[random.choice(valid_directions)].position
            else:
                return ghost.node.position
                
        elif mode == SPAWN:
            # Mode SPAWN: di chuyển về spawn node
            spawn_node = getattr(ghost, 'spawnNode', None)
            if spawn_node and hasattr(spawn_node, 'position'):
                return spawn_node.position
            else:
                pacman_pos = pacman.node.position if pacman.node else Vector2(0, 0)
                return pacman_pos
        else:  # Mode khác
            pacman_pos = pacman.node.position if pacman.node else Vector2(0, 0)
            return pacman_pos
    
    def _get_blinky_from_group(self, ghost_group):
        """
        Tìm Blinky trong ghost group
        """
        if not ghost_group or not hasattr(ghost_group, 'ghosts'):
            return None
            
        for ghost in ghost_group.ghosts:
            if hasattr(ghost, 'name') and ghost.name == BLINKY:
                return ghost
        return None

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
                'previous': pacman.node,  # LƯU node hiện tại làm previous (CRITICAL FIX)
                'position': new_pacman_node.position,  # Thêm thuộc tính position
                'directions': getattr(pacman, 'directions', {})  # Thêm directions
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
                'mode': getattr(target_ghost, 'mode', None),
                'direction': action,  # Direction MỚI
                'previous_direction': getattr(target_ghost, 'direction', None),
                'name': getattr(target_ghost, 'name', GHOST),
                'color': getattr(target_ghost, 'color', RED),
                'goal': getattr(target_ghost, 'goal', None),
                'spawnNode': getattr(target_ghost, 'spawnNode', None),
                'directions': getattr(target_ghost, 'directions', {}),
                'position': new_ghost_node.position
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
        just_left_freight_ghosts = []

        for ghost in getattr(ghostgroup, 'ghosts', []):
            if not getattr(ghost, 'alive', True):
                continue
            ghost_node = getattr(ghost, 'node', None)
            if ghost_node is None:
                continue

            ghost_mode = getattr(ghost, 'mode', None)
            # Detect if ghost just left FREIGHT mode (i.e., was FREIGHT last turn, now is normal)
            prev_mode = getattr(ghost, 'previous_mode', None)
            if ghost_mode and hasattr(ghost_mode, 'current'):
                if ghost_mode.current == FREIGHT:
                    freight_ghosts.append(ghost_node)
                elif ghost_mode.current == SPAWN:
                    spawn_ghosts.append(ghost_node)
                else:
                    if prev_mode == FREIGHT:
                        just_left_freight_ghosts.append(ghost_node)
                    normal_ghosts.append(ghost_node)
            else:
                normal_ghosts.append(ghost_node)

        # Gộp ghost vừa ra khỏi freight vào nhóm ghost nguy hiểm nhất
        all_danger_ghosts = normal_ghosts + just_left_freight_ghosts

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

        for ghost_node in all_danger_ghosts:
            if ghost_node == pacman_node:
                return -10000

        for ghost_node in freight_ghosts:
            if ghost_node == pacman_node:
                return 6000

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
        if all_danger_ghosts:
            ghost_distances = [self._calculate_distance(pacman_node, g) for g in all_danger_ghosts]
            normal_ghost_dist = min(ghost_distances)
        else:
            normal_ghost_dist = 100

        freight_ghost_dist = 0
        if freight_ghosts:
            freight_distances = [self._calculate_distance(pacman_node, g) for g in freight_ghosts]
            freight_ghost_dist = min(freight_distances)

        # Penalty quay đầu
        reverse_penalty = 0
        if hasattr(pacman, 'direction') and hasattr(pacman, 'previous_direction'):
            current_dir = getattr(pacman, 'direction', None)
            prev_dir = getattr(pacman, 'previous_direction', None)

            if current_dir and prev_dir and current_dir != prev_dir:
                reverse_pairs = [(UP, DOWN), (DOWN, UP), (LEFT, RIGHT), (RIGHT, LEFT), (PORTAL, PORTAL)]
                if (current_dir, prev_dir) in reverse_pairs:

                    should_penalize = True
                    if all_danger_ghosts:
                        min_normal_dist = min([self._calculate_distance(pacman_node, g) for g in all_danger_ghosts])
                        if min_normal_dist < 4:
                            should_penalize = False

                    if should_penalize:
                        reverse_penalty = -15  # Phạt quay đầu

        pellets_left = len(pellet_nodes)
        total_pellets = getattr(pellet_group, 'total_pellets', pellets_left)
        pellet_progress = (total_pellets - pellets_left) / total_pellets if total_pellets > 0 else 0

        position_score = self._evaluate_position_strategy(pacman_node, all_danger_ghosts + freight_ghosts)

        density_score = self._evaluate_pellet_density(pacman_node, pellet_nodes)

        safety_score = self._evaluate_safety(pacman_node, all_danger_ghosts)

        ghost_avoidance_score = 0
        if all_danger_ghosts:
            if normal_ghost_dist < 2:
                ghost_avoidance_score = -50000
            elif normal_ghost_dist < 4:
                ghost_avoidance_score = -20000
            elif normal_ghost_dist < 7:
                ghost_avoidance_score = -2000
            else:
                ghost_avoidance_score = 0

        freight_bonus = 0
        if freight_ghosts and len(freight_ghosts) > 0:
            # Ưu tiên cao cho việc ăn freight ghost
            if freight_ghost_dist < 10:  # Tăng từ 5 lên 10
                # Bonus cao khi gần
                freight_bonus = 10000 / (freight_ghost_dist + 0.5) 

                # Chỉ hủy nếu normal ghost RẤT GẦN (nguy hiểm thật sự)
                if all_danger_ghosts and normal_ghost_dist < 3:  # Giảm từ 8 xuống 3
                    freight_bonus = 0  # Quá nguy hiểm
            else:
                # Vẫn có bonus nhỏ ngay cả khi xa
                freight_bonus = 1000 / (freight_ghost_dist + 1)  # 100-1000 điểm
        else:
            freight_bonus = 0

        power_pellet_bonus = 0
        if power_pellet_nodes:
            if all_danger_ghosts:
                if normal_ghost_dist < 3:
                    power_pellet_bonus = 5000 / (power_pellet_dist + 0.5)  # Ưu tiên cao khi nguy hiểm
                elif normal_ghost_dist < 5:
                    power_pellet_bonus = 2000 / (power_pellet_dist + 0.5)  # Ưu tiên trung bình
                elif normal_ghost_dist < 8:
                    power_pellet_bonus = 500 / (power_pellet_dist + 1)     # Ưu tiên thấp
            else:
                power_pellet_bonus = 1000 / (power_pellet_dist + 0.5)  # Ưu tiên khi an toàn

        score = (
            50.0 * ghost_avoidance_score +   
            power_pellet_bonus +                
            2 * freight_bonus +                        
            -0.5 * min_pellet_dist +            
            -0.2 * avg_pellet_dist +        
            -2.0 * pellets_left +               
            10.0 * pellet_progress +        
            reverse_penalty +
            revisit_penalty +
            position_score * 0.1 +         
            density_score * 0.2 +           
            safety_score * 0.3              
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
                # Pac-Man di chuyển - CHỈ di chuyển Pac-Man, KHÔNG di chuyển Ghost
                next_pacman, next_ghostgroup, next_pellet_group = self.apply_action_for_agent(
                    pacman, ghostgroup, pellet_group, action, 0
                )
                
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
                # Ghost di chuyển - CHỈ di chuyển Ghost này
                next_pacman, next_ghostgroup, next_pellet_group = self.apply_action_for_agent(
                    pacman, ghostgroup, pellet_group, action, agent_index
                )
                
                # Đệ quy - Agent tiếp theo sẽ di chuyển
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
    def hill_climbing(self, pacman, ghost_group, pellet_group, max_steps=5):
        """
        Hill Climbing với lookahead:
        1. Thử tất cả action đầu tiên có thể
        2. Với mỗi action, thực hiện hill climbing để xem kết quả cuối cùng
        3. Chọn action đầu tiên dẫn đến kết quả tốt nhất
        """
        # Lấy tất cả action đầu tiên có thể
        first_actions = self.get_legal_actions_for_agent(pacman, ghost_group, pellet_group, 0)
        
        if not first_actions:
            return STOP
            
        best_first_action = None
        best_final_score = float('-inf')
        
        # Thử từng action đầu tiên
        for first_action in first_actions:
            # Bắt đầu hill climbing từ action này
            final_score = self._hill_climb_from_action(
                pacman, ghost_group, pellet_group, first_action, max_steps
            )
            
            # Cập nhật action tốt nhất
            if final_score > best_final_score:
                best_final_score = final_score
                best_first_action = first_action
                
        return best_first_action if best_first_action is not None else STOP
    
    def _hill_climb_from_action(self, pacman, ghost_group, pellet_group, first_action, max_steps):
        """
        Thực hiện hill climbing bắt đầu từ một action cụ thể
        Trả về score cuối cùng sau khi leo hết
        """
        # Thực hiện action đầu tiên
        current_pacman, current_ghost_group, current_pellet_group = self._simulate_full_turn(
            pacman, ghost_group, pellet_group, first_action
        )
        current_score = self.evaluate(current_pacman, current_ghost_group, current_pellet_group)
        
        # Tiếp tục hill climbing
        for step in range(max_steps - 1):  # -1 vì đã thực hiện 1 step đầu
            neighbors = self.get_legal_actions_for_agent(current_pacman, current_ghost_group, current_pellet_group, 0)
            
            if not neighbors:
                break
                
            best_neighbor_score = float('-inf')
            best_neighbor_action = None
            
            for action in neighbors: 
                next_pacman, next_ghost_group, next_pellet_group = self._simulate_full_turn(
                    current_pacman, current_ghost_group, current_pellet_group, action
                )
                score = self.evaluate(next_pacman, next_ghost_group, next_pellet_group)
                
                if score > best_neighbor_score:
                    best_neighbor_score = score
                    best_neighbor_action = action
            
            if best_neighbor_score > current_score:
                current_score = best_neighbor_score
                current_pacman, current_ghost_group, current_pellet_group = self._simulate_full_turn(
                    current_pacman, current_ghost_group, current_pellet_group, best_neighbor_action
                )
            else:
                break
                
        return current_score
      
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
        neighbor_count = sum(1 for d in [UP, DOWN, LEFT, RIGHT, PORTAL]
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
        neighbor_count = sum(1 for d in [UP, DOWN, LEFT, RIGHT, PORTAL] 
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
        for direction in (UP,DOWN,LEFT,RIGHT, PORTAL):
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
# ==========================================================
    def astar_pacman_direction(self, pacman, ghostgroup, pellet_group):
        import heapq
        import math

        start_node = getattr(pacman, 'node', None)
        if not start_node:
            return STOP

        # Phân loại ghosts theo mức độ nguy hiểm
        dangerous_ghosts = []
        freight_ghosts = []
        spawn_ghosts = []
        
        for ghost in getattr(ghostgroup, 'ghosts', []):
            if not getattr(ghost, 'alive', True):
                continue
                
            ghost_node = getattr(ghost, 'node', None)
            if not ghost_node:
                continue
                
            ghost_mode = getattr(ghost, 'mode', None)
            if ghost_mode and hasattr(ghost_mode, 'current'):
                if ghost_mode.current == FREIGHT:
                    freight_ghosts.append(ghost_node)
                elif ghost_mode.current == SPAWN:
                    spawn_ghosts.append(ghost_node)
                else:
                    dangerous_ghosts.append(ghost_node)
            else:
                dangerous_ghosts.append(ghost_node)

        # Thu thập và phân loại pellets
        power_pellets = []
        normal_pellets = []
        all_pellets = []
        
        for pellet in getattr(pellet_group, 'pelletList', []):
            if not getattr(pellet, 'visible', True):
                continue
                
            pellet_node = getattr(pellet, 'node', None)
            if not pellet_node:
                continue
                
            all_pellets.append(pellet_node)
            pellet_name = getattr(pellet, 'name', None)
            if pellet_name == POWERPELLET:
                power_pellets.append(pellet_node)
            else:
                normal_pellets.append(pellet_node)

        if not all_pellets:
            return STOP

        def calculate_heuristic(node, target):
            """Heuristic function: Manhattan distance + safety factor"""
            base_dist = self._calculate_distance(node, target)
            
            # Safety factor: tránh ghost nguy hiểm
            safety_factor = 0
            if dangerous_ghosts:
                min_danger_dist = min(self._calculate_distance(node, g) for g in dangerous_ghosts)
                if min_danger_dist <= 2:
                    safety_factor = 100  # Rất nguy hiểm
                elif min_danger_dist <= 4:
                    safety_factor = 50   # Nguy hiểm
                elif min_danger_dist <= 6:
                    safety_factor = 20   # Cảnh giác
            
            return base_dist + safety_factor

        def calculate_node_cost(node):
            """Tính cost của node dựa trên nhiều yếu tố chiến lược"""
            BASE_COST = 1
            
            # 1. Pellet bonus (ưu tiên ăn pellets)
            pellet_bonus = 0
            if node in all_pellets:
                # Power pellet có giá trị cao hơn nhiều
                if node in power_pellets:
                    pellet_bonus = -50  # Ưu tiên rất cao
                else:
                    pellet_bonus = -5   # Ưu tiên thấp hơn
            
            # 2. Ghost avoidance (quan trọng nhất - sống sót)
            ghost_penalty = 0
            if dangerous_ghosts:
                min_danger_dist = min(self._calculate_distance(node, g) for g in dangerous_ghosts)
                if min_danger_dist == 0:
                    return 50000  # Tuyệt đối tránh
                elif min_danger_dist == 1:
                    ghost_penalty = 10000  # Rất nguy hiểm
                elif min_danger_dist == 2:
                    ghost_penalty = 5000   # Nguy hiểm
                elif min_danger_dist == 3:
                    ghost_penalty = 1000   # Cảnh giác
                elif min_danger_dist <= 5:
                    ghost_penalty = 200    # Chú ý
            
            # 3. Freight ghost bonus (cơ hội ăn ghost)
            freight_bonus = 0
            if freight_ghosts:
                min_freight_dist = min(self._calculate_distance(node, g) for g in freight_ghosts)
                if min_freight_dist <= 3:
                    freight_bonus = -200  # Ưu tiên cao ăn freight ghost
                    # Nhưng chỉ khi không quá nguy hiểm
                    if dangerous_ghosts:
                        min_danger = min(self._calculate_distance(node, g) for g in dangerous_ghosts)
                        if min_danger < 4:
                            freight_bonus = 0  # Quá nguy hiểm, hủy bonus
            
            # 4. Position risk (dead end, corridor)
            position_risk = 0
            neighbor_count = sum(1 for d in [UP, DOWN, LEFT, RIGHT, PORTAL] 
                               if node.neighbors.get(d) is not None)
            if neighbor_count <= 1:
                position_risk = 500  # Dead end - rất nguy hiểm
            elif neighbor_count == 2:
                position_risk = 100  # Corridor - hạn chế di chuyển
            
            # 5. Game progress factor (late game pellets quý giá hơn)
            progress_factor = 0
            if hasattr(pellet_group, 'total_pellets'):
                remaining = len([p for p in pellet_group.pelletList if p.visible])
                total = pellet_group.total_pellets
                if total > 0:
                    progress = (total - remaining) / total
                    if progress > 0.8:  # Late game
                        progress_factor = -20  # Pellets rất quý giá
            
            # 6. Escape route bonus (ưu tiên vị trí có nhiều lối thoát)
            escape_bonus = 0
            if neighbor_count >= 3:
                escape_bonus = -10  # Nhiều lối thoát = an toàn hơn
            
            return (BASE_COST + pellet_bonus + ghost_penalty + 
                   freight_bonus + position_risk + progress_factor + escape_bonus)

        def select_best_target():
            """Chọn mục tiêu tốt nhất dựa trên tình huống hiện tại"""
            # Nếu có ghost nguy hiểm gần, ưu tiên power pellet
            if dangerous_ghosts and power_pellets:
                min_danger_dist = min(self._calculate_distance(start_node, g) for g in dangerous_ghosts)
                if min_danger_dist <= 6:
                    # Tìm power pellet gần nhất và an toàn nhất
                    best_power = None
                    best_score = float('inf')
                    for pp in power_pellets:
                        dist = self._calculate_distance(start_node, pp)
                        # Kiểm tra an toàn trên đường đi
                        safety_score = 0
                        if dangerous_ghosts:
                            min_ghost_on_path = min(self._calculate_distance(pp, g) for g in dangerous_ghosts)
                            safety_score = min_ghost_on_path
                        total_score = dist - safety_score * 3  # Ưu tiên an toàn
                        if total_score < best_score:
                            best_score = total_score
                            best_power = pp
                    if best_power:
                        return best_power
            
            # Nếu có freight ghost gần và an toàn, ưu tiên ăn ghost
            if freight_ghosts:
                min_freight_dist = min(self._calculate_distance(start_node, g) for g in freight_ghosts)
                if min_freight_dist <= 5:
                    # Kiểm tra an toàn
                    if not dangerous_ghosts or min(self._calculate_distance(start_node, g) for g in dangerous_ghosts) > 4:
                        return min(freight_ghosts, key=lambda p: self._calculate_distance(start_node, p))
            
            # Mặc định: tìm pellet gần nhất và an toàn nhất
            best_pellet = None
            best_score = float('inf')
            for pellet in all_pellets:
                dist = self._calculate_distance(start_node, pellet)
                safety_penalty = 0
                if dangerous_ghosts:
                    min_ghost_dist = min(self._calculate_distance(pellet, g) for g in dangerous_ghosts)
                    if min_ghost_dist <= 2:
                        safety_penalty = 500  # Rất nguy hiểm
                    elif min_ghost_dist <= 4:
                        safety_penalty = 100  # Nguy hiểm
                total_score = dist + safety_penalty
                if total_score < best_score:
                    best_score = total_score
                    best_pellet = pellet
            
            return best_pellet

        # Chọn mục tiêu tối ưu
        target = select_best_target()
        
        # A* search với priority queue
        open_set = []
        h_start = calculate_heuristic(start_node, target)
        heapq.heappush(open_set, (h_start, 0, start_node))
        
        came_from = {}
        g_score = {start_node: 0}
        closed_set = set()
        
        # Giới hạn số node để tránh timeout
        max_nodes = 2000
        nodes_explored = 0
        
        while open_set and nodes_explored < max_nodes:
            f_score, g_current, current_node = heapq.heappop(open_set)
            nodes_explored += 1
            
            if current_node in closed_set:
                continue
                
            closed_set.add(current_node)
            
            # Kiểm tra đích
            if current_node == target:
                # Reconstruct path để tìm direction đầu tiên
                path = []
                node = target
                while node in came_from:
                    prev_node, direction = came_from[node]
                    path.append(direction)
                    node = prev_node
                
                # Trả về direction đầu tiên trong path
                return path[-1] if path else STOP
            
            # Duyệt neighbors
            for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
                neighbor = current_node.neighbors.get(direction)
                
                if neighbor is None or neighbor in closed_set:
                    continue
                
                # Tính cost với hàm đánh giá thông minh
                edge_cost = calculate_node_cost(neighbor)
                tentative_g = g_score[current_node] + edge_cost
                
                # Cập nhật nếu tìm được đường tốt hơn
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    came_from[neighbor] = (current_node, direction)
                    g_score[neighbor] = tentative_g
                    
                    h_score = calculate_heuristic(neighbor, target)
                    f_score = tentative_g + h_score
                    
                    heapq.heappush(open_set, (f_score, tentative_g, neighbor))
        
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
                action = self.hill_climbing(self.pacman, ghost_group, pellet_group)
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

  
   
       
       