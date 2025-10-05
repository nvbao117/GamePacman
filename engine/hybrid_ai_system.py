import copy
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
    "pellet_proximity": -100.0,
    "threat": -5000.0,
    "power_play": 1500.0,
    "capsules": -50.0
}
from engine.heuristic import Heuristic

class HybridAISystem:
    def __init__(self, pacman, config=None):
        self.pacman = pacman
        self.game_instance = None
        self.last_online_decision = 0.0
        self.config = config
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

    def _get_online_direction(self, pellet_group, ghost_group, fruit=None):
        current_node = getattr(self.pacman, 'node', None)
        if current_node is None:
            return STOP
        algorithm_name = getattr(self.pacman, 'pathfinder_name', DEFAULT_ALGORITHM)
        handler = self._algorithm_handlers.get(algorithm_name, self._run_astar)
        return handler(pellet_group, ghost_group, fruit)
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

        num_agents = 3
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
            weights['capsules'] * self.StrateCapsules(state)
        )
  
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
        return min(distances) if distances else 0
    
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
            total_risk += 1.0 / ((dist + 0.0001) ** THREAT_DECAY)
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
        next_depth = depth - 1 

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

        for action in actions:
            best_value = math.inf
            best_action = actions[0]
            next_state = self.apply_action_for_agent(pacman, ghostgroup, pellet_group, action, agent_index)
            value, _ = self.alpha_beta_pruning(*next_state, next_depth, alpha, beta, next_agent)
            if value < best_value:
                best_value = value
                best_action = action
            beta = min(beta, best_value)
            if beta <= alpha:
                break
        return best_value, best_action



# ==========================================================
#                HILL CLIMBING ALGORITHM CHO PAC-MAN
# ----------------------------------------------------------
# - Tìm hướng đi tốt nhất bằng cách đánh giá các trạng thái lân cận (neighbor states)
# - Luôn chọn nước đi cải thiện điểm số (evaluation) so với hiện tại
# - Không đảm bảo tìm được nghiệm tối ưu toàn cục (có thể mắc kẹt ở local optimum)
# ==========================================================
    def hill_climbing(self, pacman, ghost_group, pellet_group, max_steps=5):
        pass
      
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
#                    A* ALGORITHM
# ----------------------------------------------------------
# ==========================================================

    def astar_pacman_direction(self, pacman, ghostgroup, pellet_group):
        pass




# ==========================================================
#                    END OF A* ALGORITHM
# ==========================================================


# ==========================================================
#        CÁC HÀM HANDLER CHO TỪNG THUẬT TOÁN AI PAC-MAN
# ----------------------------------------------------------
# - Đóng vai trò là "bộ chuyển đổi" giữa hệ thống và các thuật toán tìm đường:
#   + _run_minimax:      Gọi thuật toán Minimax để chọn hướng đi tối ưu cho Pac-Man
#   + _run_alpha_beta:   Gọi thuật toán Alpha-Beta Pruning để chọn hướng đi tối ưu
#   + _run_hill_climbing:Gọi thuật toán Hill Climbing để chọn hướng đi
#   + _run_astar:        Gọi thuật toán A* để chọn hướng đi ngắn nhất/tránh nguy hiểm
# - Các hàm này nhận vào trạng thái hiện tại (pellet_group, ghost_group, fruit)
#   và trả về hướng đi (direction) phù hợp cho Pac-Man
# ==========================================================

    def _run_minimax(self, pellet_group, ghost_group, fruit):
        pacman_copy = self._clone_entity(
            self.pacman,
            direction=getattr(self.pacman, 'direction', None),
            previous_direction=getattr(self.pacman, 'direction', None),
        )
        score, action = self.minimax(pacman_copy, ghost_group, pellet_group, depth=2, agent_index=0, fruit=fruit)
        return action

    def _run_alpha_beta(self, pellet_group, ghost_group, fruit):
        pacman_copy = self._clone_entity(
            self.pacman,
            direction=getattr(self.pacman, 'direction', None),
            previous_direction=getattr(self.pacman, 'direction', None),
        )
        _, action = self.alpha_beta_pruning(pacman_copy, ghost_group, pellet_group, depth=3, agent_index=0)
        return action

    def _run_hill_climbing(self, pellet_group, ghost_group, fruit):
        return self.hill_climbing(self.pacman, ghost_group, pellet_group)

    def _run_astar(self, pellet_group, ghost_group, fruit):
        return self.astar_pacman_direction(self.pacman, ghost_group, pellet_group)

# ==========================================================
#            Các hàm tiện ích static cho HybridAISystem
# ----------------------------------------------------------
#  - Hỗ trợ clone entity, lấy danh sách ghost, pellet, v.v.
#  - Được sử dụng nội bộ cho các thuật toán AI
# ==========================================================
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

# ==========================================================
#                   KHOẢNG CÁCH (DISTANCE)
# ----------------------------------------------------------
# Các hàm và logic liên quan đến tính toán khoảng cách giữa
# Pac-Man, ma, và các đối tượng khác trên bản đồ.
# ==========================================================
    def _calculate_distance(self, node1, node2):
        # Lấy config từ pacman nếu self.config là None
        config = self.config
        if config is None and hasattr(self.pacman, 'config'):
            config = self.pacman.config
        
        func = Heuristic.get_heuristic_function(config)
        return func(node1, node2)

    def _calculate_distance_manhattan(self, node1, node2):
        result = Heuristic.manhattan(node1, node2)
        return result

    def _calculate_distance_euclidean(self, node1, node2):
        func = Heuristic.euclidean
        return func(node1, node2)
