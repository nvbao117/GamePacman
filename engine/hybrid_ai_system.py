import copy
import logging
import math
import random
from typing import Dict, Optional, Tuple

from constants import (
    BLINKY,
    CHASE,
    CLYDE,
    DOWN,
    FREIGHT,
    GHOST,
    INKY,
    LEFT,
    NCOLS,
    NROWS,
    PACMAN,
    PINKY,
    PORTAL,
    POWERPELLET,
    RED,
    RIGHT,
    SCATTER,
    SPAWN,
    STOP,
    TILEHEIGHT,
    TILEWIDTH,
    UP,
)
from objects.vector import Vector2

logger = logging.getLogger(__name__)

ORTHOGONAL_DIRECTIONS: Tuple[int, ...] = (UP, DOWN, LEFT, RIGHT)
ALL_DIRECTIONS: Tuple[int, ...] = ORTHOGONAL_DIRECTIONS + (PORTAL,)
MAX_SIMULATED_GHOSTS = 2
DEFAULT_PLANNING_INTERVAL = 60.0
THREAT_RANGE = 8
THREAT_DECAY = 3
LATE_GAME_PROGRESS_THRESHOLD = 0.8
FREIGHT_CHASE_RADIUS = 3
DEAD_END_NEIGHBORS = 1
CORRIDOR_NEIGHBORS = 2
SAFE_EXIT_NEIGHBORS = 3
GRID_SIZE = max(TILEWIDTH, 1)
REVERSE_DIRECTION = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}
DANGEROUS_GHOST_MODES = {CHASE, SCATTER}
DEFAULT_ALGORITHM = "A*"

EVALUATION_WEIGHTS: Dict[str, float] = {
    "progress": 1.0,
    "remaining_pellets": -20.0,
    "pellet_proximity": -200.0,
    "threat": -5000.0,
    "power_play": 1500.0,
    "capsules": -50.0,
    "route_efficiency": -5.0,
}

class HybridAISystem:
    def __init__(self, pacman):
        self.pacman = pacman
        self.game_instance = None
        self.last_online_decision = 0.0

        self.current_mode = "ONLINE"
        self.planning_interval = DEFAULT_PLANNING_INTERVAL
        self.last_planning_time = 0.0

        # Offline planning variables
        self.offline_plan = []
        self.offline_plan_index = 0
        self.offline_plan_valid = False

        # Performance tracking
        self.mode_switch_count = 0

        # Caching d? t?i uu performance
        self._evaluation_cache = {}
        self._cache_max_size = 1000

        self.prev_q_state = None
        self.prev_q_action = None
        self._last_pacman_pos = None
        self.prev_pellet_count = 0
        self._portal_used = False

        self._evaluation_weights = dict(EVALUATION_WEIGHTS)
        self._algorithm_handlers = {
            "Minimax": self._run_minimax,
            "Alpha-Beta": self._run_alpha_beta,
            "Hill Climbing": self._run_hill_climbing,
            "A*": self._run_astar,
            "A* Online": self._run_astar,
        }

    def set_mode(self, mode):
        if mode in ["ONLINE", "OFFLINE"]:
            self.current_mode = mode
            self.offline_plan = []
            self.offline_plan_index = 0
            self.offline_plan_valid = False

    def get_direction(self, pellet_group, ghost_group=None, fruit=None):
        return self._get_online_direction(pellet_group, ghost_group, fruit)

# ==========================================================
#                    MINIMAX ALGORITHM
# ----------------------------------------------------------
# Thuật toán Minimax cho Pac-Man (không alpha-beta)
# - Pac-Man là người chơi tối đa (Maximizing Player)
# - Ghost là người chơi tối thiểu (Minimizing Player)
# - Đệ quy tìm kiếm trạng thái tốt nhất cho Pac-Man
# ==========================================================
    def minimax(self, pacman, ghostgroup, pellet_group, depth, agent_index=0, fruit=None):
        if depth == 0 or self.is_terminal_state(pacman, ghostgroup, pellet_group):
            return self.evaluate(pacman, ghostgroup, pellet_group, fruit), None

        num_agents = 1 + 2
        is_pacman = (agent_index == 0)
        
        actions = self.get_legal_actions_for_agent(pacman, ghostgroup, pellet_group, agent_index)
        
        if not actions:
            eval_score = self.evaluate(pacman, ghostgroup, pellet_group, fruit)
            return eval_score, None

        next_agent = (agent_index + 1) % num_agents
        next_depth = depth - 1 if next_agent == 0 else depth
        
        if is_pacman:
            max_eval = float('-inf')
            best_action = actions[0]
            
            for i, action in enumerate(actions):
                next_pacman, next_ghostgroup, next_pellet_group = self.apply_action_for_agent(
                    pacman, ghostgroup, pellet_group, action, 0,fruit
                )
                eval_score, _ = self.minimax(next_pacman, next_ghostgroup, next_pellet_group, next_depth, next_agent)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_action = action
            return max_eval, best_action
        else:   
            min_eval = float('inf')
            best_action = actions[0]

            for action in actions:
                next_pacman, next_ghostgroup, next_pellet_group = self.apply_action_for_agent(
                    pacman, ghostgroup, pellet_group, action, agent_index,fruit
                )
                eval_score, _ = self.minimax(next_pacman, next_ghostgroup, next_pellet_group, next_depth, next_agent,fruit)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_action = action
            return min_eval, best_action

    def is_terminal_state(self, pacman, ghostgroup, pellet_group):
        for ghost in self._ghosts(ghostgroup):
            if ghost.node == pacman.node:
                return True

        pellets_left = any(pellet.visible for pellet in pellet_group.pelletList)
        if not pellets_left:
            return True

        return False

    def get_legal_actions_for_agent(self, pacman, ghostgroup, pellet_group, agent_index):
        if agent_index == 0:
            node = getattr(pacman, "node", None)
            entity_type = PACMAN
        else:
            ghosts = getattr(ghostgroup, "ghosts", None) or []
            ghost_idx = agent_index - 1
            if ghost_idx >= len(ghosts):
                return []
            ghost = ghosts[ghost_idx]
            node = getattr(ghost, "node", None)
            entity_type = GHOST
        if node is None:
            return []
        return [direction for direction in ALL_DIRECTIONS if self._can_move_in_direction(node, direction, entity_type)]

    def _can_move_in_direction(self, current_node, direction, entity_type=PACMAN):
        if current_node is None:
            return False
        if direction == PORTAL:
            return current_node.neighbors.get(PORTAL) is not None

        neighbor = current_node.neighbors.get(direction)
        if neighbor is None:
            return False

        access = getattr(current_node, "access", {})
        allowed = access.get(direction)
        if not allowed:
            return True
        if isinstance(allowed, (set, list, tuple)):
            return entity_type in allowed
        return True

    def apply_action_for_agent(self, pacman, ghostgroup, pellet_group, action, agent_index, fruit=None):
        if agent_index == 0:
            if action == STOP:
                return pacman, ghostgroup, pellet_group
            pacman_node = getattr(pacman, "node", None)
            if pacman_node is None:
                return pacman, ghostgroup, pellet_group
            if action not in pacman_node.neighbors:
                return pacman, ghostgroup, pellet_group
            next_node = pacman_node.neighbors.get(action)
            if next_node is None:
                return pacman, ghostgroup, pellet_group
            new_pacman = self._clone_entity(
                pacman,
                node=next_node,
                previous=pacman_node,
                previous_direction=getattr(pacman, "direction", None),
                direction=action,
                position=getattr(next_node, "position", getattr(pacman, "position", None)),
            )
            new_pellet_group = self._simulate_eat_pellets_fast(new_pacman, pellet_group)
            return new_pacman, ghostgroup, new_pellet_group

        closest_ghosts = self._get_n_closest_ghosts(pacman, ghostgroup, n=MAX_SIMULATED_GHOSTS)
        ghost_idx = agent_index - 1
        if ghost_idx >= len(closest_ghosts):
            return pacman, ghostgroup, pellet_group
        target_ghost = closest_ghosts[ghost_idx]
        ghost_node = getattr(target_ghost, "node", None)
        if action == STOP or ghost_node is None:
            return pacman, ghostgroup, pellet_group
        if action not in ghost_node.neighbors:
            return pacman, ghostgroup, pellet_group
        next_node = ghost_node.neighbors.get(action)
        if next_node is None:
            return pacman, ghostgroup, pellet_group
        new_ghost = self._clone_entity(
            target_ghost,
            node=next_node,
            previous_direction=getattr(target_ghost, "direction", None),
            direction=action,
            position=getattr(next_node, "position", getattr(target_ghost, "position", None)),
        )
        original_ghosts = getattr(ghostgroup, "ghosts", None) or []
        new_ghosts = [new_ghost if g is target_ghost else g for g in original_ghosts]
        new_ghostgroup = self._clone_entity(ghostgroup, ghosts=new_ghosts)
        return pacman, new_ghostgroup, pellet_group

    def _simulate_eat_pellets_fast(self, pacman, pellet_group):
        pacman_node = getattr(pacman, "node", None)
        pellets = getattr(pellet_group, "pelletList", None) or []
        if pacman_node is None or not pellets:
            return pellet_group
        remaining = [
            pellet
            for pellet in pellets
            if getattr(pellet, "node", None) is not pacman_node and getattr(pellet, "visible", True)
        ]
        return self._clone_entity(pellet_group, pelletList=remaining)

    def _get_n_closest_ghosts(self, pacman, ghostgroup, n=MAX_SIMULATED_GHOSTS):
        pacman_node = getattr(pacman, 'node', None)
        if pacman_node is None:
            return []

        ghost_distances = []
        for ghost in self._ghosts(ghostgroup):
            ghost_node = getattr(ghost, 'node', None)
            if ghost_node is None:
                continue
            distance = self._calculate_distance(pacman_node, ghost_node)
            ghost_distances.append((ghost, distance))

        ghost_distances.sort(key=lambda x: x[1])
        return [ghost for ghost, _ in ghost_distances[:n]]

    def evaluate(self, pacman, ghostgroup, pellet_group, fruit=None):
        state = {
            'pacman': pacman,
            'ghostgroup': ghostgroup,
            'pellet_group': pellet_group,
            'fruit': fruit
        }
        weights = self._evaluation_weights
        return (
            weights['progress'] * self.GameProgress(state) +
            weights['remaining_pellets'] * self.RemainingPellets(state) +
            weights['pellet_proximity'] * self.PelletProximity(state) +
            weights['threat'] * self.ThreatLevel(state) +
            weights['power_play'] * self.PowerPlayValue(state) +
            weights['capsules'] * self.StrateCapsules(state) + 
            weights['route_efficiency'] * self.RouteEfficiency(state)
        )

    # Lấy điểm số hiện tại của Pac-Man
    def GameProgress(self, state):
        pacman = state.get('pacman')
        return getattr(pacman, 'score', 0) if pacman else 0

    def RemainingPellets(self, state):
        return len(self._pellets(state.get('pellet_group')))

    def PelletProximity(self, state):
        pacman = state.get('pacman')
        pellet_group = state.get('pellet_group')
        pacman_node = getattr(pacman, 'node', None)
        pellets = self._pellets(pellet_group)
        if pacman_node is None or not pellets:
            return 0
        distances = [
            self._calculate_distance(pacman_node, getattr(pellet, 'node', None))
            for pellet in pellets
            if getattr(pellet, 'node', None) is not None and getattr(pellet, 'visible', True)
        ]
        return min(distances, default=0)

    def ThreatLevel(self, state):
        pacman = state.get('pacman')
        ghostgroup = state.get('ghostgroup')
        pacman_node = getattr(pacman, 'node', None)
        if pacman_node is None:
            return 0
        total_risk = 0.0
        for ghost in self._ghosts(ghostgroup):
            if not getattr(ghost, 'visible', True):
                continue
            mode_controller = getattr(ghost, 'mode', None)
            if getattr(mode_controller, 'current', None) not in DANGEROUS_GHOST_MODES:
                continue
            ghost_node = getattr(ghost, 'node', None)
            if ghost_node is None:
                continue
            dist = self._calculate_distance(pacman_node, ghost_node)
            if dist == math.inf or dist > THREAT_RANGE:
                continue
            total_risk += 1.0 / ((dist + 1) ** THREAT_DECAY)
        return total_risk

    def PowerPlayValue(self, state):
        pacman = state.get('pacman')
        ghostgroup = state.get('ghostgroup')
        pacman_node = getattr(pacman, 'node', None)
        if pacman_node is None:
            return 0
        value = 0.0
        for ghost in self._ghosts(ghostgroup):
            if not getattr(ghost, 'visible', True):
                continue
            mode_controller = getattr(ghost, 'mode', None)
            if getattr(mode_controller, 'current', None) != FREIGHT:
                continue
            time_total = getattr(mode_controller, 'time', 0)
            time_timer = getattr(mode_controller, 'timer', 0)
            time_left = max(0, float(time_total) - float(time_timer))
            time_ratio = time_left / (float(time_total) + 0.0001) 

            ghost_node = getattr(ghost, 'node', None)
            if pacman_node is not None and ghost_node is not None:
                dist = self._calculate_distance(pacman_node, ghost_node)
                distance_factor = 1.0 / (dist + 1)
            else:
                distance_factor = 1.0

            value += 200 * time_ratio * distance_factor
        return value

    def StrateCapsules(self, state):
        pellets = self._pellets(state.get('pellet_group'))
        return sum(1 for pellet in pellets if getattr(pellet, 'name', None) == POWERPELLET)

    def RouteEfficiency(self, state):
        pellet_group = state.get('pellet_group')
        pacman = state.get('pacman')
        pellets = self._pellets(pellet_group)
        pacman_node = getattr(pacman, 'node', None)
        if not pellets or pacman_node is None:
            return 0

        pellet_nodes = {getattr(pellet, 'node', None) for pellet in pellets if getattr(pellet, 'node', None)}

        def count_connected_components(nodes):
            nodes = set(nodes)
            visited = set()
            components = 0
            for node in nodes:
                if node in visited:
                    continue
                components += 1
                stack = [node]
                while stack:
                    current = stack.pop()
                    if current in visited:
                        continue
                    visited.add(current)
                    for neighbor in current.neighbors.values():
                        if neighbor and neighbor in nodes and neighbor not in visited:
                            stack.append(neighbor)
            return components

        components = count_connected_components(pellet_nodes)
        distances = [
            self._calculate_distance(pacman_node, getattr(pellet, 'node', None))
            for pellet in pellets
            if getattr(pellet, 'node', None)
        ]
        closest = min(distances, default=0)
        return (components - 1) + closest

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
        """Simulate a full ghost turn based on their active modes."""
        ghosts = []
        for ghost in self._ghosts(ghost_group):
            node = getattr(ghost, 'node', None)
            if node is None:
                ghosts.append(ghost)
                continue
            best_direction = self._get_ghost_best_direction(ghost, pacman, ghost_group)
            next_node = node.neighbors.get(best_direction)
            if next_node is None:
                ghosts.append(ghost)
                continue
            ghosts.append(
                self._clone_entity(
                    ghost,
                    node=next_node,
                    direction=best_direction,
                    position=getattr(next_node, 'position', getattr(ghost, 'position', None)),
                )
            )
        return self._clone_entity(ghost_group, ghosts=ghosts)

    def _get_ghost_best_direction(self, ghost, pacman, ghost_group):
        """
        Tìm hướng di chuyển tốt nhất cho một ghost dựa trên mode
        """
        if not ghost.node or not pacman.node:
            return STOP
            
        valid_directions = []
        for direction in ALL_DIRECTIONS:
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
        mode_controller = getattr(ghost, 'mode', None)
        mode = getattr(mode_controller, 'current', CHASE)
        ghost_name = getattr(ghost, 'name', GHOST)
        pacman_node = getattr(pacman, 'node', None)
        pacman_position = pacman_node.position if pacman_node else Vector2(0, 0)
        pacman_direction = getattr(pacman, 'direction', RIGHT)
        directions = getattr(pacman, 'directions', {})
        ghost_node = getattr(ghost, 'node', None)

        if mode == SCATTER:
            if ghost_name == PINKY:
                return Vector2(0, TILEHEIGHT * NROWS)
            if ghost_name == INKY:
                return Vector2(TILEWIDTH * NCOLS, TILEHEIGHT * NROWS)
            if ghost_name == CLYDE:
                return Vector2(0, TILEHEIGHT * NROWS)
            return Vector2(0, 0)

        if mode == CHASE:
            if ghost_name == PINKY and pacman_direction in directions:
                return pacman_position + directions[pacman_direction] * TILEWIDTH * 4
            if ghost_name == INKY:
                blinky = self._get_blinky_from_group(ghost_group)
                if blinky and getattr(blinky, 'node', None):
                    vec1 = pacman_position + directions.get(pacman_direction, Vector2(1, 0)) * TILEWIDTH * 2
                    vec2 = (vec1 - blinky.node.position) * 2
                    return blinky.node.position + vec2
                return pacman_position
            if ghost_name == CLYDE:
                ghost_position = getattr(ghost, 'position', Vector2())
                delta = pacman_position - ghost_position
                if delta.magnitudeSquared() <= (TILEWIDTH * 8) ** 2 and pacman_direction in directions:
                    return Vector2(0, TILEHEIGHT * NROWS)
                if pacman_direction in directions:
                    return pacman_position + directions[pacman_direction] * TILEWIDTH * 4
                return pacman_position
            return pacman_position

        if mode == FREIGHT:
            if ghost_node is None:
                return pacman_position
            valid = [direction for direction in ALL_DIRECTIONS if ghost_node.neighbors.get(direction)]
            if valid:
                return ghost_node.neighbors[random.choice(valid)].position
            return ghost_node.position

        if mode == SPAWN:
            spawn_node = getattr(ghost, 'spawnNode', None)
            if spawn_node and spawn_node.position:
                return spawn_node.position
            return pacman_position

        return pacman_position

    def _get_blinky_from_group(self, ghost_group):
        """
        Tìm Blinky trong ghost group
        """
        if not ghost_group or not ghost_group.ghosts:
            return None
            
        for ghost in ghost_group.ghosts:
            if ghost.name == BLINKY:
                return ghost
        return None
    
    def _get_closest_ghost_to_pacman(self, pacman, ghostgroup):
        """Tìm ghost gần Pacman nhất (legacy - sử dụng _get_n_closest_ghosts)"""
        closest_ghosts = self._get_n_closest_ghosts(pacman, ghostgroup, n=1)
        return closest_ghosts[0] if closest_ghosts else None

    def _get_best_ghost_actions(self, pacman, ghostgroup, actions, agent_index):
        """Sắp xếp actions của ghost dựa trên mode (CHASE/SCATTER/FREIGHT)"""
        if not pacman.node:
            return actions
        
        closest_ghost = self._get_closest_ghost_to_pacman(pacman, ghostgroup)
        if not closest_ghost or not closest_ghost.node:
            return actions
        
        # Kiểm tra mode của ghost
        ghost_mode = closest_ghost.mode
        current_mode = ghost_mode.current if ghost_mode and ghost_mode.current else CHASE
        
        action_scores = []
        for action in actions:
            if action in closest_ghost.node.neighbors and closest_ghost.node.neighbors[action]:
                next_node = closest_ghost.node.neighbors[action]
                distance = self._calculate_distance(next_node, pacman.node)
                
                if current_mode == FREIGHT:
                            score = random.random()  # Random score
                elif current_mode == SCATTER:
                    score = -distance  # Âm để sort ngược → xa Pacman
                else:
                    score = distance  # Gần Pacman
                
                action_scores.append((action, score))
        
        action_scores.sort(key=lambda x: x[1])
        return [action for action, _ in action_scores]

    def get_legal_actions(self, pacman, ghostgroup, pellet_group, is_pacman):
        agent_index = 0 if is_pacman else 1
        return self.get_legal_actions_for_agent(pacman, ghostgroup, pellet_group, agent_index)



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
    def alpha_beta_pruning(self, pacman, ghostgroup, pellet_group, depth, alpha=-math.inf, beta=math.inf, agent_index=0):
        if depth == 0 or self.is_terminal_state(pacman, ghostgroup, pellet_group):
            return self.evaluate(pacman, ghostgroup, pellet_group), None

        ghosts = self._ghosts(ghostgroup)
        num_agents = 1 + len(ghosts)
        actions = list(self.get_legal_actions_for_agent(pacman, ghostgroup, pellet_group, agent_index))
        if not actions:
            return self.evaluate(pacman, ghostgroup, pellet_group), None

        next_agent = (agent_index + 1) % num_agents
        next_depth = depth - 1 if next_agent == 0 else depth

        if agent_index == 0:
            best_value = -math.inf
            best_action = actions[0]
            for order, action in enumerate(actions):
                next_state = self.apply_action_for_agent(pacman, ghostgroup, pellet_group, action, 0)
                value, _ = self.alpha_beta_pruning(*next_state, next_depth, alpha, beta, next_agent)
                value += self._alpha_beta_noise(pacman, action, order)
                if value > best_value:
                    best_value = value
                    best_action = action
                alpha = max(alpha, best_value)
                if beta <= alpha:
                    break
            return best_value, best_action

        if len(actions) > 3:
            actions = self._get_best_ghost_actions(pacman, ghostgroup, actions, agent_index)[:3]

        best_value = math.inf
        best_action = actions[0]
        for action in actions:
            next_state = self.apply_action_for_agent(pacman, ghostgroup, pellet_group, action, agent_index)
            value, _ = self.alpha_beta_pruning(*next_state, next_depth, alpha, beta, next_agent)
            if value < best_value:
                best_value = value
                best_action = action
            beta = min(beta, best_value)
            if beta <= alpha:
                break
        return best_value, best_action

    def _alpha_beta_noise(self, pacman, action, order):
        noise = float(order)
        prev_dir = getattr(pacman, 'previous_direction', None)
        if prev_dir is None:
            return noise
        if REVERSE_DIRECTION.get(action) == prev_dir:
            return -10000.0
        return noise + 100.0

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

        start_node = getattr(pacman, 'node', None)
        if start_node is None:
            return STOP

        dangerous_nodes = []
        freight_nodes = []
        for ghost in self._ghosts(ghostgroup):
            if not getattr(ghost, 'visible', True):
                continue
            node = getattr(ghost, 'node', None)
            if node is None:
                continue
            mode = getattr(getattr(ghost, 'mode', None), 'current', None)
            if mode == FREIGHT:
                freight_nodes.append(node)
            elif mode == SPAWN:
                continue
            else:
                dangerous_nodes.append(node)

        pellets = [
            pellet
            for pellet in self._pellets(pellet_group)
            if getattr(pellet, 'visible', True) and getattr(pellet, 'node', None)
        ]
        if not pellets:
            return STOP

        power_pellets = [pellet.node for pellet in pellets if getattr(pellet, 'name', None) == POWERPELLET]
        normal_pellets = [pellet.node for pellet in pellets if getattr(pellet, 'name', None) != POWERPELLET]
        all_pellets = power_pellets + normal_pellets

        def heuristic(node, target):
            base = self._calculate_distance(node, target)
            if not dangerous_nodes:
                return base
            min_danger = min(self._calculate_distance(node, ghost_node) for ghost_node in dangerous_nodes)
            if min_danger <= 2:
                return base + 100
            if min_danger <= 4:
                return base + 50
            if min_danger <= 6:
                return base + 20
            return base

        def node_cost(node):
            cost = 1.0
            if node in all_pellets:
                cost -= 50.0 if node in power_pellets else 5.0

            if dangerous_nodes:
                min_danger = min(self._calculate_distance(node, ghost_node) for ghost_node in dangerous_nodes)
                if min_danger == 0:
                    return 50000.0
                if min_danger == 1:
                    cost += 10000.0
                elif min_danger == 2:
                    cost += 5000.0
                elif min_danger == 3:
                    cost += 1000.0
                elif min_danger <= 5:
                    cost += 200.0

            if freight_nodes:
                min_freight = min(self._calculate_distance(node, freight_node) for freight_node in freight_nodes)
                if min_freight <= FREIGHT_CHASE_RADIUS:
                    bonus = -200.0
                    if dangerous_nodes:
                        min_danger = min(self._calculate_distance(node, ghost_node) for ghost_node in dangerous_nodes)
                        if min_danger < 4:
                            bonus = 0.0
                    cost += bonus

            neighbor_count = sum(1 for direction in ALL_DIRECTIONS if node.neighbors.get(direction))
            if neighbor_count <= DEAD_END_NEIGHBORS:
                cost += 500.0
            elif neighbor_count == CORRIDOR_NEIGHBORS:
                cost += 100.0
            elif neighbor_count >= SAFE_EXIT_NEIGHBORS:
                cost -= 10.0

            pellets_remaining = len(pellets)
            total_pellets = getattr(pellet_group, 'total_pellets', pellets_remaining)
            if total_pellets:
                progress = (total_pellets - pellets_remaining) / float(total_pellets)
                if progress > LATE_GAME_PROGRESS_THRESHOLD:
                    cost -= 20.0
            return cost

        def choose_target():
            if dangerous_nodes and power_pellets:
                min_danger = min(self._calculate_distance(start_node, node) for node in dangerous_nodes)
                if min_danger <= 6:
                    best_power = None
                    best_score = math.inf
                    for pellet_node in power_pellets:
                        distance = self._calculate_distance(start_node, pellet_node)
                        safety = 0
                        if dangerous_nodes:
                            safety = min(self._calculate_distance(pellet_node, ghost_node) for ghost_node in dangerous_nodes)
                        score = distance - safety * 3
                        if score < best_score:
                            best_score = score
                            best_power = pellet_node
                    if best_power:
                        return best_power

            if freight_nodes:
                min_freight = min(self._calculate_distance(start_node, node) for node in freight_nodes)
                if min_freight <= 5:
                    if not dangerous_nodes or min(self._calculate_distance(start_node, node) for node in dangerous_nodes) > 4:
                        return min(freight_nodes, key=lambda node: self._calculate_distance(start_node, node))

            best_pellet = None
            best_score = math.inf
            for pellet_node in all_pellets:
                distance = self._calculate_distance(start_node, pellet_node)
                safety_penalty = 0
                if dangerous_nodes:
                    min_ghost = min(self._calculate_distance(pellet_node, node) for node in dangerous_nodes)
                    if min_ghost <= 2:
                        safety_penalty = 500
                    elif min_ghost <= 4:
                        safety_penalty = 100
                score = distance + safety_penalty
                if score < best_score:
                    best_score = score
                    best_pellet = pellet_node
            return best_pellet

        target_node = choose_target()
        open_set = []
        heapq.heappush(open_set, (heuristic(start_node, target_node), 0.0, start_node))
        came_from = {}
        g_score = {start_node: 0.0}
        visited = set()

        while open_set:
            _, current_cost, current = heapq.heappop(open_set)
            if current in visited:
                continue
            visited.add(current)

            if current is target_node:
                while came_from.get(current) and came_from[current][0] is not start_node:
                    current = came_from[current][0]
                if current is target_node and came_from.get(current) is None:
                    return STOP
                direction = came_from[current][1] if came_from.get(current) else STOP
                return direction

            for direction in ALL_DIRECTIONS:
                neighbor = current.neighbors.get(direction)
                if neighbor is None:
                    continue
                tentative = current_cost + node_cost(neighbor)
                if tentative >= g_score.get(neighbor, math.inf):
                    continue
                came_from[neighbor] = (current, direction)
                g_score[neighbor] = tentative
                f_score = tentative + heuristic(neighbor, target_node)
                heapq.heappush(open_set, (f_score, tentative, neighbor))

        return STOP

    def _get_online_direction(self, pellet_group, ghost_group, fruit=None):
        current_node = getattr(self.pacman, 'node', None)
        if current_node is None:
            return STOP
        algorithm_name = getattr(self.pacman, 'pathfinder_name', DEFAULT_ALGORITHM)
        handler = self._algorithm_handlers.get(algorithm_name, self._run_astar)
        try:
            return handler(pellet_group, ghost_group, fruit)
        except Exception as exc:  # pragma: no cover
            logger.exception("[ONLINE] Algorithm %s error: %s", algorithm_name, exc)
            return self._get_random_direction(current_node)

    def _run_minimax(self, pellet_group, ghost_group, fruit):
        pacman_copy = self._clone_entity(
            self.pacman,
            direction=getattr(self.pacman, 'direction', None),
            previous_direction=getattr(self.pacman, 'direction', None),
        )
        score, action = self.minimax(pacman_copy, ghost_group, pellet_group, depth=2, agent_index=0, fruit=fruit)
        if action is None:
            return self._get_random_direction(getattr(self.pacman, 'node', None))
        return action

    def _run_alpha_beta(self, pellet_group, ghost_group, fruit):
        pacman_copy = self._clone_entity(
            self.pacman,
            direction=getattr(self.pacman, 'direction', None),
            previous_direction=getattr(self.pacman, 'direction', None),
        )
        _, action = self.alpha_beta_pruning(pacman_copy, ghost_group, pellet_group, depth=3, agent_index=0)
        if action is None:
            return self._get_random_direction(getattr(self.pacman, 'node', None))
        return action

    def _run_hill_climbing(self, pellet_group, ghost_group, fruit):
        return self.hill_climbing(self.pacman, ghost_group, pellet_group)

    def _run_astar(self, pellet_group, ghost_group, fruit):
        return self.astar_pacman_direction(self.pacman, ghost_group, pellet_group)

    def _get_random_direction(self, current_node):
        """Return a random legal direction from current_node."""
        if current_node is None:
            return STOP
        valid_directions = [
            direction
            for direction in ALL_DIRECTIONS
            if self._can_move_in_direction(current_node, direction)
        ]
        return random.choice(valid_directions) if valid_directions else STOP

    def _calculate_distance(self, node1, node2):
        """
        Tính maze distance (số bước ngắn nhất trên maze) giữa node1 và node2 bằng BFS.
        """
        if node1 is None or node2 is None:
            return float('inf')
        if node1 == node2:
            return 0

        from collections import deque
        visited = set()
        queue = deque([(node1, 0)])
        while queue:
            current, dist = queue.popleft()
            if current == node2:
                return dist
            visited.add(current)
            for neighbor in current.neighbors.values():
                if neighbor and neighbor not in visited:
                    queue.append((neighbor, dist + 1))
        return float('inf')

    def _evaluate_power_pellets(self, pacman_node, pellet_group):
        """Đánh giá power pellets (nếu có trong game)"""    
        if not pacman_node or not pellet_group.powerPellets:
            return 0
            
        # Tìm power pellets còn lại
        power_pellets = []
        if pellet_group.powerPellets:
            power_pellets = [pp for pp in pellet_group.powerPellets if pp.visible]
        
        if not power_pellets:
            return 0
            
        # Tính khoảng cách đến power pellet gần nhất
        min_power_dist = min(
            (self._calculate_distance(pacman_node, pp.node) for pp in power_pellets if pp.node),
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
        for direction in ALL_DIRECTIONS:
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

    @staticmethod
    def _clone_entity(entity, **overrides):
        if entity is None:
            return None
        clone = copy.copy(entity)
        for attr, value in overrides.items():
            setattr(clone, attr, value)
        return clone

    @staticmethod
    def _ghosts(ghostgroup):
        if ghostgroup is None:
            return tuple()
        ghosts = getattr(ghostgroup, 'ghosts', None)
        if not ghosts:
            return tuple()
        return tuple(ghosts)

    @staticmethod
    def _pellets(pellet_group):
        if pellet_group is None:
            return tuple()
        pellets = getattr(pellet_group, 'pelletList', None)
        if not pellets:
            return tuple()
        return tuple(pellets)


