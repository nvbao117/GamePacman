import copy
import heapq
import math
import random
from collections import deque
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
GRID_SIZE = max(TILEWIDTH, 1)
DANGEROUS_GHOST_MODES = {CHASE, SCATTER}
DEFAULT_ALGORITHM = "A*"

EVALUATION_WEIGHTS: Dict[str, float] = {
    "progress": 1.0,
    "remaining_pellets": -20.0,
    "pellet_proximity": -100.0,
    "threat": -20000.0,
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
            "Genetic Algorithm": self._run_genetic_algorithm,
            "GBFS": self._run_gbfs,
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

        ghosts = self._ghosts(ghostgroup)
        simulated_ghosts = min(len(ghosts), MAX_SIMULATED_GHOSTS)
        num_agents = 1 + simulated_ghosts  # Pacman + simulated ghosts
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
            # ✅ Fix: dùng cùng danh sách ghost với apply_action_for_agent
            closest_ghosts = self._get_n_closest_ghosts(pacman, ghostgroup, n=MAX_SIMULATED_GHOSTS)
            ghost_idx = agent_index - 1
            if ghost_idx >= len(closest_ghosts):
                return []
            ghost = closest_ghosts[ghost_idx]
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
        pellets = self._pellets(pellet_group)
        visible_pellets = []
        visible_nodes = []
        for pellet in pellets:
            if not getattr(pellet, 'visible', True):
                continue
            visible_pellets.append(pellet)
            node = getattr(pellet, 'node', None)
            if node is not None:
                visible_nodes.append(node)
        state = {
            'pacman': pacman,
            'ghostgroup': ghostgroup,
            'pellet_group': pellet_group,
            'fruit': fruit,
            'pellet_data': {
                'all': pellets,
                'visible': tuple(visible_pellets),
                'visible_nodes': tuple(visible_nodes),
            },
            'heuristic_func': Heuristic.get_heuristic_function(self._resolve_config()),
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
        pellet_data = state.get('pellet_data')
        if pellet_data:
            return len(pellet_data.get('all', ()))
        return len(self._pellets(state.get('pellet_group')))

    def PelletProximity(self, state):
        pacman = state.get('pacman')
        pellet_group = state.get('pellet_group')
        pacman_node = getattr(pacman, 'node', None)
        pellet_data = state.get('pellet_data') or {}
        pellet_nodes = pellet_data.get('visible_nodes')
        if pellet_nodes is None:
            pellet_nodes = [
                getattr(pellet, 'node', None)
                for pellet in self._pellets(pellet_group)
                if getattr(pellet, 'visible', True)
            ]
        pellet_nodes = [node for node in pellet_nodes if node is not None]

        if pacman_node is None or not pellet_nodes:
            return 0
        
        heuristic_func = state.get('heuristic_func')
        if heuristic_func is None:
            heuristic_func = Heuristic.get_heuristic_function(self._resolve_config())
        is_maze_distance = heuristic_func == Heuristic.mazedistance
       
        
        if not pellet_nodes:
            distances = []
        elif is_maze_distance:
            N = 10  
            manhattan = Heuristic.manhattan
            pellet_nodes_sorted = sorted(
                pellet_nodes,
                key=lambda node: manhattan(pacman_node, node)
            )[:N]
            distances = [
                self._calculate_distance(pacman_node, node, heuristic_func=heuristic_func)
                for node in pellet_nodes_sorted
            ]
        else:
            distances = [
                self._calculate_distance(pacman_node, node)
                for node in pellet_nodes
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
                distance_factor = 1.0 / (dist + 0.0001)
            else:
                distance_factor = 1.0

            value += 200 * time_ratio * distance_factor
        return value

    def StrateCapsules(self, state):
        pellet_data = state.get('pellet_data')
        if pellet_data:
            pellets = pellet_data.get('all', ())
        else:
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
        simulated_ghosts = min(len(ghosts), MAX_SIMULATED_GHOSTS)
        num_agents = 1 + simulated_ghosts  # Pacman + simulated ghosts
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
                value += self._alpha_beta_noise(order)
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

    def _alpha_beta_noise(self, order):
        """
        Thêm noise nhỏ để tránh tie-breaking deterministic
        Ưu tiên action đầu tiên khi có cùng giá trị
        """
        return -0.001 * order  


# ==========================================================
#                HILL CLIMBING ALGORITHM CHO PAC-MAN
# ----------------------------------------------------------
# - Tìm hướng đi tốt nhất bằng cách đánh giá các trạng thái lân cận (neighbor states)
# - Luôn chọn nước đi cải thiện điểm số (evaluation) so với hiện tại
# - Không đảm bảo tìm được nghiệm tối ưu toàn cục (có thể mắc kẹt ở local optimum)
# ==========================================================
    def hill_climbing(self, pacman, ghost_group, pellet_group, max_steps=5):
        if pacman is None:
            return STOP

        current_pacman = pacman
        current_ghost_group = ghost_group
        current_pellet_group = pellet_group

        def node_key(node):
            if node is None:
                return ("NONE",)
            position = getattr(node, 'position', None)
            if position is None:
                return ("ID", id(node))
            return ("POS", position.x, position.y)
        def ghost_signature(ghost_state):
            signature = []
            for ghost in self._ghosts(ghost_state):
                node = getattr(ghost, 'node', None)
                mode_controller = getattr(ghost, 'mode', None)
                signature.append((
                    str(getattr(ghost, 'name', '')),
                    node_key(node),
                    str(getattr(mode_controller, 'current', None)),
                ))
            return tuple(sorted(signature))
        evaluation_cache = {}
        def pellet_fingerprint(pellet_state):
            pellets = getattr(pellet_state, 'pelletList', None) or []
            visible = [
                node_key(getattr(pellet, 'node', None))
                for pellet in pellets
                if getattr(pellet, 'visible', True)
            ]
            return tuple(sorted(visible))
        def score_state(pacman_state, ghost_state, pellet_state):
            key = (
                node_key(getattr(pacman_state, 'node', None)),
                pellet_fingerprint(pellet_state),
                ghost_signature(ghost_state),
            )
            if key in evaluation_cache:
                return evaluation_cache[key]
            value = self.evaluate(pacman_state, ghost_state, pellet_state)
            evaluation_cache[key] = value
            return value

        current_score = score_state(current_pacman, current_ghost_group, current_pellet_group)
        best_initial_action = STOP

        

        for _ in range(max_steps):
            actions = self.get_legal_actions_for_agent(current_pacman, current_ghost_group, current_pellet_group, 0)
            if not actions:
                break

            best_neighbor_score = current_score
            best_neighbor_state = None
            best_neighbor_action = STOP

            for action in actions:
                next_pacman, next_ghost_group, next_pellet_group = self.apply_action_for_agent(
                    current_pacman, current_ghost_group, current_pellet_group, action, 0
                )
                neighbor_score = score_state(next_pacman, next_ghost_group, next_pellet_group)
                if neighbor_score > best_neighbor_score:
                    best_neighbor_score = neighbor_score
                    best_neighbor_state = (next_pacman, next_ghost_group, next_pellet_group)
                    best_neighbor_action = action

            if best_neighbor_state is None:
                break

            if best_initial_action == STOP:
                best_initial_action = best_neighbor_action

            current_pacman, current_ghost_group, current_pellet_group = best_neighbor_state
            current_score = best_neighbor_score

        return best_initial_action
      
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
    def genetic_algorithm(
        self,
        pacman,
        ghost_group,
        pellet_group,
        fruit=None,
        population_size=20,
        sequence_length=6,
        generations=15,
        mutation_rate=0.15,
        elite_fraction=0.2,
        tournament_size=3,
    ):
        heuristic_func = Heuristic.get_heuristic_function(self._resolve_config())
        legal_actions = self.get_legal_actions_for_agent(pacman, ghost_group, pellet_group, 0)
        if not legal_actions:
            return []

        population_size = max(1, population_size)
        sequence_length = max(1, sequence_length)
        generations = max(1, generations)

        def random_sequence():
            return [random.choice(legal_actions) for _ in range(sequence_length)]

        base_pacman_state = self._clone_entity(pacman)
        state_prefix_cache = {(): (base_pacman_state, ghost_group, pellet_group)}
        sequence_score_cache = {}

        def evaluate_sequence(action_sequence):
            sequence_key = tuple(action_sequence)
            if sequence_key in sequence_score_cache:
                return sequence_score_cache[sequence_key]

            base_state = state_prefix_cache[()]
            pacman_state = self._clone_entity(base_state[0])
            ghost_state = base_state[1]
            pellet_state = base_state[2]

            if not action_sequence:
                score = self.evaluate(pacman_state, ghost_state, pellet_state, fruit)
                sequence_score_cache[sequence_key] = score
                return score

            prefix = []
            for action in action_sequence:
                prefix.append(action)
                prefix_key = tuple(prefix)
                cached_state = state_prefix_cache.get(prefix_key)
                if cached_state is not None:
                    pacman_state = self._clone_entity(cached_state[0])
                    ghost_state = cached_state[1]
                    pellet_state = cached_state[2]
                    continue

                pacman_state, ghost_state, pellet_state = self.apply_action_for_agent(
                    pacman_state,
                    ghost_state,
                    pellet_state,
                    action,
                    0,
                    fruit,
                )
                state_prefix_cache[prefix_key] = (
                    self._clone_entity(pacman_state),
                    ghost_state,
                    pellet_state,
                )
            score = self.evaluate(pacman_state, ghost_state, pellet_state, fruit)
            sequence_score_cache[sequence_key] = score
            return score



        def tournament_select(scored_population):
            if not scored_population:
                return []
            pool_size = min(tournament_size, len(scored_population))
            if pool_size <= 0:
                pool_size = 1
            chosen_indices = set()
            population_len = len(scored_population)
            while len(chosen_indices) < pool_size:
                chosen_indices.add(random.randrange(population_len))
            best_index = max(chosen_indices, key=lambda idx: scored_population[idx][0])
            return scored_population[best_index][1][:]


        def crossover(parent_a, parent_b):
            if sequence_length <= 1:
                return parent_a[:]
            point = random.randint(1, sequence_length - 1)
            return parent_a[:point] + parent_b[point:]

        def mutate(sequence):
            return [
                random.choice(legal_actions) if random.random() < mutation_rate else action
                for action in sequence
            ]

        population = [random_sequence() for _ in range(population_size)]
        best_sequence = []
        best_score = -math.inf

        elite_count = max(1, min(int(population_size * elite_fraction), population_size))

        for _ in range(generations):
            scored_population = []
            for individual in population:
                score = evaluate_sequence(individual)
                scored_population.append((score, individual[:]))

            scored_population.sort(key=lambda item: item[0], reverse=True)

            if scored_population and scored_population[0][0] > best_score:
                best_score = scored_population[0][0]
                best_sequence = scored_population[0][1][:]

            new_population = [individual[:] for _, individual in scored_population[:elite_count]]

            while len(new_population) < population_size and scored_population:
                parent1 = tournament_select(scored_population)
                parent2 = tournament_select(scored_population)
                child = crossover(parent1, parent2)
                child = mutate(child)
                new_population.append(child)

            if not new_population:
                break

            population = new_population

        if not best_sequence and population:
            best_sequence = max(
                ((evaluate_sequence(individual), individual) for individual in population),
                key=lambda item: item[0],
            )[1][:]

        return best_sequence


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
        pacman_node = getattr(pacman, 'node', None)
        if pacman_node is None:
            return STOP

        distance_cache = {}

        def cached_distance(node_a, node_b):
            if node_a is None or node_b is None:
                return float('inf')
            key = (node_a, node_b)
            if key in distance_cache:
                return distance_cache[key]
            reverse_key = (node_b, node_a)
            if reverse_key in distance_cache:
                return distance_cache[reverse_key]
            distance = self._calculate_distance(node_a, node_b)
            distance_cache[key] = distance
            distance_cache[reverse_key] = distance
            return distance

        ghosts = []
        for ghost in self._ghosts(ghostgroup):
            ghost_node = getattr(ghost, 'node', None)
            if ghost_node is None:
                continue
            distance = cached_distance(pacman_node, ghost_node)
            ghosts.append((ghost, ghost_node, distance))

        if not ghosts:
            freight_ghost_nodes = []
            is_freight_ghost = False  # ✅ Fix: khởi tạo khi không có ghost
        else:
            nearest_ghost, _, _ = min(ghosts, key=lambda item: item[2])
            is_freight_ghost = getattr(getattr(nearest_ghost, 'mode', None), 'current', None) == FREIGHT
            freight_ghost_nodes = [
                ghost_node
                for ghost, ghost_node, _ in ghosts
                if getattr(getattr(ghost, 'mode', None), 'current', None) == FREIGHT
            ]

        if is_freight_ghost:
            min_dist = float('inf')
            selected_ghost_node = None
            selected_time_left = 0
            for ghost, ghost_node, distance_to_pacman in ghosts:
                mode_controller = getattr(ghost, 'mode', None)
                if ghost_node is None or getattr(mode_controller, 'current', None) != FREIGHT:
                    continue
                time_total = getattr(mode_controller, 'time', 0)
                time_timer = getattr(mode_controller, 'timer', 0)
                time_left = max(0, float(time_total) - float(time_timer))
                dist = distance_to_pacman
                if dist < min_dist and time_left > 0.5:
                    min_dist = dist
                    selected_ghost_node = ghost_node
                    selected_time_left = time_left

            if selected_ghost_node is not None and selected_time_left > 0.5:
                goal_node = selected_ghost_node
            else:
                if freight_ghost_nodes:
                    goal_node = min(
                        freight_ghost_nodes,
                        key=lambda node: cached_distance(pacman_node, node),
                    )
                else:
                    goal_node = None
        else:
            if self.is_ghost_near(pacman_node, ghostgroup):
                power_node = self.find_nearest_power_pellet(pacman_node, pellet_group)
                if power_node is not None:
                    goal_node = power_node
                else:
                    goal_node = self.find_furthes_safe_node(pacman_node, ghostgroup)
            else:
                goal_node = self.find_nearest_pellet(pacman_node, pellet_group)

        if goal_node is None or goal_node == pacman_node:
            return STOP

        open_set = []
        heapq.heappush(open_set, (cached_distance(pacman_node, goal_node), 0, pacman_node, None))
        came_from = {}
        g_score = {pacman_node: 0}
        visited = set()

        while open_set:
            f, g, current, first_direction = heapq.heappop(open_set)
            if current == goal_node:
                return first_direction if first_direction is not None else STOP

            if current in visited:
                continue
            visited.add(current)

            if not hasattr(current, 'neighbors'):
                continue

            for direction, neighbor in current.neighbors.items():
                if neighbor is None:
                    continue

                tentative_g = g + 1
                tentative_f = tentative_g + cached_distance(neighbor, goal_node)
                
                # Kiểm tra xem neighbor đã được thăm chưa hoặc có f-score tốt hơn không
                if neighbor in visited:
                    continue
                    
                # Nếu neighbor đã có trong open_set với f-score tốt hơn, bỏ qua
                if neighbor in g_score and tentative_g >= g_score[neighbor]:
                    continue

                g_score[neighbor] = tentative_g
                next_direction = direction if current == pacman_node else first_direction
                heapq.heappush(open_set, (tentative_f, tentative_g, neighbor, next_direction))
                came_from[neighbor] = (current, direction)

        return STOP




# ==========================================================
#                    END OF A* ALGORITHM
# ==========================================================

# ==========================================================
#                GREEDY BEST FIRST SEARCH (GBFS)
# ----------------------------------------------------------
# Thuật toán Greedy Best First Search cho Pac-Man
# - Luôn chọn node có heuristic nhỏ nhất (gần mục tiêu nhất) để mở rộng tiếp theo
# - Không xét tổng chi phí đường đi, chỉ xét heuristic (ước lượng khoảng cách đến mục tiêu)
# - Thường tìm đường nhanh nhưng không đảm bảo tối ưu như A*
# - Phù hợp khi cần tìm đường nhanh đến pellet/capsule gần nhất, tránh ghost
# ==========================================================
    def GreedyBestFirstSearch(self, pacman, ghostgroup, pellet_group):
        pacman_node = getattr(pacman, 'node', None)
        if pacman_node is None:
            return STOP

        ghosts = [
            ghost
            for ghost in self._ghosts(ghostgroup)
            if getattr(ghost, 'node', None) is not None
        
        ]
        # ghost gần nhất là freight thì trả về true
        if not ghosts:
            freight_ghost_nodes = []
            is_freight_ghost = False  # ✅ Fix: khởi tạo khi không có ghost
        else:
            nearest_ghost = min(
                ghosts,
                key=lambda ghost: self._calculate_distance(pacman_node, getattr(ghost, 'node', None))
            )
            if getattr(getattr(nearest_ghost, 'mode', None), 'current', None) == FREIGHT:
                is_freight_ghost = True
            else:
                is_freight_ghost = False
            freight_ghost_nodes = [
                ghost.node
                for ghost in ghosts
                if getattr(getattr(ghost, 'mode', None), 'current', None) == FREIGHT
            ]

        if is_freight_ghost:
            min_dist = float('inf')
            selected_ghost_node = None
            selected_time_left = 0
            for ghost in ghosts:
                ghost_node = getattr(ghost, 'node', None)
                mode_controller = getattr(ghost, 'mode', None)
                if ghost_node is None or getattr(mode_controller, 'current', None) != FREIGHT:
                    continue
                time_total = getattr(mode_controller, 'time', 0)
                time_timer = getattr(mode_controller, 'timer', 0)
                time_left = max(0, float(time_total) - float(time_timer))
                dist = self._calculate_distance(pacman_node, ghost_node)
                if dist < min_dist and time_left > 0.5:  
                    min_dist = dist
                    selected_ghost_node = ghost_node
                    selected_time_left = time_left

            if selected_ghost_node is not None and selected_time_left > 0.5:
                goal_node = selected_ghost_node
            else:
                if freight_ghost_nodes:
                    goal_node = min(
                        freight_ghost_nodes,
                        key=lambda node: self._calculate_distance(pacman_node, node),
                    )
                else:
                    goal_node = None
        else:
            if self.is_ghost_near(pacman_node, ghostgroup):
                power_node = self.find_nearest_power_pellet(pacman_node, pellet_group)
                if power_node is not None:
                    goal_node = power_node
                else:
                    goal_node = self.find_furthes_safe_node(pacman_node, ghostgroup)
            else:
                goal_node = self.find_nearest_pellet(pacman_node, pellet_group)

        if goal_node is None or goal_node == pacman_node:
            return STOP

        open_set = []
        heapq.heappush(open_set, (self._calculate_distance(pacman_node, goal_node), pacman_node, None))
        visited = set()

        while open_set:
            _, current, first_direction = heapq.heappop(open_set)
            if current == goal_node:
                return first_direction if first_direction is not None else STOP

            visited.add(current)
            if not hasattr(current, 'neighbors'):
                continue

            for direction, neighbor in current.neighbors.items():
                if neighbor is None or neighbor in visited:
                    continue

                next_direction = direction if current == pacman_node else first_direction
                heapq.heappush(
                    open_set,
                    (self._calculate_distance(neighbor, goal_node), neighbor, next_direction),
                )

        return STOP

    def find_furthes_safe_node(self, pacman_node, ghostgroup, max_depth=5):
        visited = set()
        queue = deque([(pacman_node, 0)])
        best_node = pacman_node
        best_dist = -1

        # Get all dangerous ghosts
        dangerous_ghosts = [
            ghost for ghost in self._ghosts(ghostgroup)
            if getattr(ghost, 'node', None) is not None
            and getattr(getattr(ghost, 'mode', None), 'current', None) in DANGEROUS_GHOST_MODES
        ]

        # If no dangerous ghosts, return current position
        if not dangerous_ghosts:
            return pacman_node

        while queue:
            node, depth = queue.popleft()
            if node in visited or depth > max_depth:
                continue
            visited.add(node)

            # Calculate minimum distance to any dangerous ghost
            min_ghost_dist = min(
                (
                    self._calculate_distance(node, ghost.node)
                    for ghost in dangerous_ghosts
                ),
                default=float('inf'),
            )

            if min_ghost_dist > best_dist:
                best_dist = min_ghost_dist
                best_node = node

            for neighbor in node.neighbors.values():
                if neighbor is not None and neighbor not in visited:
                    queue.append((neighbor, depth + 1))

        return best_node

    def find_nearest_power_pellet(self, pacman_node, pellet_group):
        pellet_list = getattr(pellet_group, 'pelletList', None)
        if not pellet_list:
            return None

        return min(
            (
                getattr(pellet, 'node', None)
                for pellet in pellet_list
                if getattr(pellet, 'name', None) == POWERPELLET
                and getattr(pellet, 'node', None) is not None
                and getattr(pellet, 'visible', True)
            ),
            key=lambda node: self._calculate_distance(pacman_node, node),
            default=None,
        )

    def find_nearest_pellet(self, pacman_node, pellet_group):
        pellet_list = getattr(pellet_group, 'pelletList', None)
        if not pellet_list:
            return None

        return min(
            (
                getattr(pellet, 'node', None)
                for pellet in pellet_list
                if getattr(pellet, 'node', None) is not None
                and getattr(pellet, 'visible', True)
            ),
            key=lambda node: self._calculate_distance(pacman_node, node),
            default=None,
        )
    
    def is_ghost_near(self, pacman_node, ghostgroup, threat_range=THREAT_RANGE):
        if pacman_node is None:
            return False

        for ghost in self._ghosts(ghostgroup):
            ghost_node = getattr(ghost, 'node', None)
            if ghost_node is None:
                continue

            mode = getattr(getattr(ghost, 'mode', None), 'current', None)
            if mode in DANGEROUS_GHOST_MODES and self._calculate_distance(pacman_node, ghost_node) <= threat_range:
                return True

        return False

# ==========================================================
#                    END OF GBFS ALGORITHM
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
    def _run_genetic_algorithm(self, pellet_group, ghost_group, fruit):
        pacman_copy = self._clone_entity(
            self.pacman,
            direction=getattr(self.pacman, 'direction', None),
            previous_direction=getattr(self.pacman, 'direction', None),
        )
        action_sequence = self.genetic_algorithm(pacman_copy, ghost_group, pellet_group, fruit)
        if action_sequence:
            return action_sequence[0]
        return self._run_astar(pellet_group, ghost_group, fruit)
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

    def _run_gbfs(self, pellet_group, ghost_group, fruit):
        return self.GreedyBestFirstSearch(self.pacman, ghost_group, pellet_group)

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
    def _resolve_config(self):
        config = self.config
        if config is None and hasattr(self.pacman, 'config'):
            config = getattr(self.pacman, 'config', None)
        return config

    def _calculate_distance(self, node1, node2, heuristic_func=None):
        if not hasattr(node1, 'position') or not hasattr(node2, 'position'):
            return float('inf')
        if heuristic_func is None:
            heuristic_func = Heuristic.get_heuristic_function(self._resolve_config())
        return heuristic_func(node1, node2)

    def _calculate_distance_manhattan(self, node1, node2):
        result = Heuristic.manhattan(node1, node2)
        return result

    def _calculate_distance_euclidean(self, node1, node2):
        func = Heuristic.euclidean
        return func(node1, node2)

