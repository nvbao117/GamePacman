# =============================================================================
# ALGORITHMS.PY - TẤT CẢ THUẬT TOÁN THỰC TẾ CHO PACMAN
# =============================================================================
# Tối ưu hóa tất cả algorithms để chạy nhanh trong thực tế

from collections import deque
from queue import PriorityQueue
from constants import *
import time
import math

# =============================================================================
# BFS
# =============================================================================
def bfs(startNode, pellet_group, heuristic_func=None):
    print("BFS")

    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = get_visible_pellet_nodes(pellet_group)

    if not pellet_nodes:
        return None

    if heuristic_func is not None:
        print(f"🎯 BFS using heuristic: {heuristic_func.__name__}")

    current_node = startNode
    remaining_pellets = set(pellet_nodes)
    full_path = []
    if len(remaining_pellets) <= 7:
        path_to_pellet = bfs_few_pellets(current_node, remaining_pellets)
        return path_to_pellet
    while remaining_pellets:
        if heuristic_func is not None:
            nearest_pellet = min(remaining_pellets, key=lambda p: heuristic_func(current_node, p))
            path_to_pellet = bfs_find_nearest_pellet(current_node, {nearest_pellet})
        else:
            path_to_pellet = bfs_find_nearest_pellet(current_node, remaining_pellets)
        
        if not path_to_pellet:
            break  

        if full_path and path_to_pellet[0] == full_path[-1]:
            full_path.extend(path_to_pellet[1:])
        else:
            full_path.extend(path_to_pellet)

        current_node = path_to_pellet[-1]
        remaining_pellets.discard(current_node)

    return full_path if full_path else None

def bfs_find_nearest_pellet(start_node, pellet_nodes):
    queue = deque()
    queue.append((start_node, [start_node]))
    visited = set()
    visited.add(start_node)

    while queue:
        current, path = queue.popleft()
        if current in pellet_nodes:
            return path
        for direction in get_all_directions():
            neighbor = current.neighbors.get(direction)
            if is_valid_node(neighbor, current, direction) and neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
    return None

def bfs_few_pellets(start_node, pellet_nodes):
    max_pellets = 7
    from collections import deque
    queue = deque()
    initial_collected = set([start_node]) if start_node in pellet_nodes else set()
    queue.append((start_node, [start_node], initial_collected))
    visited = set()
    visited.add((start_node, frozenset(initial_collected)))
    while queue:
        current, path, collected = queue.popleft()
        if len(collected) >= max_pellets:
            return path
        if len(collected) == len(pellet_nodes):
            return path

        for direction in get_all_directions():
            neighbor = current.neighbors.get(direction)
            if is_valid_node(neighbor, current, direction):
                new_collected = set(collected)
                if neighbor in pellet_nodes:
                    new_collected.add(neighbor)
                state = (neighbor, frozenset(new_collected))
                if state not in visited:
                    visited.add(state)
                    queue.append((neighbor, path + [neighbor], new_collected))
    return None
# =============================================================================
# DFS 
# =============================================================================
def dfs(startNode, pellet_group, heuristic_func=None):
    print("DFS")
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = get_visible_pellet_nodes(pellet_group)

    if not pellet_nodes:
        return None

    if heuristic_func is not None:
        print(f"🎯 DFS using heuristic: {heuristic_func.__name__}")

    current_node = startNode
    remaining_pellets = set(pellet_nodes)
    full_path = []
    path_to_pellet = None
    use_special_case = len(remaining_pellets) <= 7
    if use_special_case:
        path_to_pellet = dfs_few_pellets(current_node, remaining_pellets)
        if path_to_pellet:
            return path_to_pellet
    if not use_special_case or path_to_pellet is None:
        while remaining_pellets:
            if heuristic_func is not None:
                nearest_pellet = min(remaining_pellets, key=lambda p: heuristic_func(current_node, p))
                path_to_pellet = dfs_find_nearest_pellet(current_node, {nearest_pellet})
            else:
                path_to_pellet = dfs_find_nearest_pellet(current_node, remaining_pellets)
            if not path_to_pellet:
                break
            if full_path and path_to_pellet[0] == full_path[-1]:
                full_path.extend(path_to_pellet[1:])
            else:
                full_path.extend(path_to_pellet)
            current_node = path_to_pellet[-1]
            remaining_pellets.discard(current_node)
    return full_path if full_path else None

def dfs_find_nearest_pellet(start_node, pellet_nodes):
    stack = []
    stack.append((start_node, [start_node]))
    visited = set()
    visited.add(start_node)

    while stack:
        current, path = stack.pop()
        if current in pellet_nodes:
            return path
        for direction in get_all_directions():
            neighbor = current.neighbors.get(direction)
            if is_valid_node(neighbor, current, direction) and neighbor not in visited:
                visited.add(neighbor)
                stack.append((neighbor, path + [neighbor]))
    return None

def dfs_few_pellets(start_node, pellet_nodes):
    max_pellets = 7
    stack = []
    stack.append((start_node, [start_node], set([start_node]) if start_node in pellet_nodes else set()))
    visited = set()
    visited.add((start_node, frozenset(set([start_node]) if start_node in pellet_nodes else set())))
    while stack:
        current, path, collected = stack.pop()
        if len(collected) >= max_pellets:
            return path
        if len(collected) == len(pellet_nodes):
            return path

        for direction in get_all_directions():
            neighbor = current.neighbors.get(direction)
            if is_valid_node(neighbor, current, direction):
                new_collected = set(collected)
                if neighbor in pellet_nodes:
                    new_collected.add(neighbor)
                state = (neighbor, frozenset(new_collected))
                if state not in visited:
                    visited.add(state)
                    stack.append((neighbor, path + [neighbor], new_collected))
    return None

# ============================================================================= 
# A*
# =============================================================================
def astar(startNode, pellet_group, ghost_group=None, heuristic_func=None, ghost_avoid_dist=2):
    print("🎯 A* algorithm")
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = get_visible_pellet_nodes(pellet_group)
    if not pellet_nodes:
        return None

    remaining_pellets = set(pellet_nodes)
    path = []
    current_node = startNode
    if current_node in remaining_pellets:
        remaining_pellets.remove(current_node)
        path.append(current_node)

    while remaining_pellets:
        if len(remaining_pellets) <= 7:
            sub_path = astar_few_pellets(current_node, remaining_pellets)
            if sub_path is None:
                break
            if path and sub_path[0] == path[-1]:
                path.extend(sub_path[1:])
            else:
                path.extend(sub_path)
            break  
        else:
            if heuristic_func is not None:
                nearest_pellet = min(remaining_pellets, key=lambda p: heuristic_func(current_node, p))
            else:
                nearest_pellet = min(remaining_pellets, key=lambda p: heuristic_manhattan(current_node, p))
            
            sub_path = astar_single(current_node, nearest_pellet, heuristic_func=heuristic_func)
            if sub_path is None:
                break
            if path and sub_path[0] == path[-1]:
                path.extend(sub_path[1:])
            else:
                path.extend(sub_path)
            
            current_node = nearest_pellet
            remaining_pellets.remove(nearest_pellet)

    return path if path else None

def astar_single(start, goal, heuristic_func=None):
    from queue import PriorityQueue

    if start == goal:
        return [start]

    open_set = PriorityQueue()
    open_set.put((0, start))
    came_from = {start: None}
    g_score = {start: 0}

    while not open_set.empty():
        _, current = open_set.get()
        if current == goal:
            path = []
            while current is not None:
                path.insert(0, current)
                current = came_from[current]
            return path

        for direction in get_all_directions():
            neighbor = current.neighbors.get(direction)
            if is_valid_node(neighbor, current, direction):
                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    if heuristic_func is not None:
                        h = heuristic_func(neighbor, goal)
                    else:
                        h = heuristic_manhattan(neighbor, goal)
                    f = tentative_g + h
                    open_set.put((f, neighbor))
                    came_from[neighbor] = current
    return None

def astar_few_pellets(start_node, pellet_nodes):
    from queue import PriorityQueue

    max_pellets = 7
    def heuristic(current, collected):
        uncollected = pellet_nodes - collected
        if not uncollected:
            return 0
        return min(heuristic_manhattan(current, p) for p in uncollected)

    initial_collected = set()
    if start_node in pellet_nodes:
        initial_collected.add(start_node)

    pq = PriorityQueue()
    g = 0
    h = heuristic(start_node, initial_collected)
    pq.put((g + h, g, start_node, [start_node], frozenset(initial_collected)))
    visited = set()
    visited.add((start_node, frozenset(initial_collected)))

    while not pq.empty():
        f, g, current, path, collected = pq.get()
        collected_set = set(collected)
        if len(collected_set) >= max_pellets or len(collected_set) == len(pellet_nodes):
            return path

        for direction in get_all_directions():
            neighbor = current.neighbors.get(direction)
            if is_valid_node(neighbor, current, direction):
                new_collected = set(collected_set)
                if neighbor in pellet_nodes:
                    new_collected.add(neighbor)
                state = (neighbor, frozenset(new_collected))
                if state not in visited:
                    visited.add(state)
                    new_g = g + 1
                    new_h = heuristic(neighbor, new_collected)
                    pq.put((new_g + new_h, new_g, neighbor, path + [neighbor], frozenset(new_collected)))
    return None

# =============================================================================
# UCS
# =============================================================================
def ucs(startNode, pellet_group, heuristic_func=None):
    print("UCS")
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = get_visible_pellet_nodes(pellet_group)

    if not pellet_nodes:
        return None

    if heuristic_func is not None:
        print(f"🎯 UCS using heuristic: {heuristic_func.__name__}")

    current_node = startNode
    remaining_pellets = set(pellet_nodes)
    full_path = []
    
    if len(remaining_pellets) <= 7:
        path_to_pellet = ucs_few_pellets(current_node, remaining_pellets)
        return path_to_pellet

    while remaining_pellets:
        if heuristic_func is not None:
            nearest_pellet = min(remaining_pellets, key=lambda p: heuristic_func(current_node, p))
            path_to_pellet, _ = ucs_find_nearest_pellet(current_node, {nearest_pellet})
        else:
            path_to_pellet, _ = ucs_find_nearest_pellet(current_node, remaining_pellets)
        if not path_to_pellet:
            break  

        if full_path and path_to_pellet[0] == full_path[-1]:
            full_path.extend(path_to_pellet[1:])
        else:
            full_path.extend(path_to_pellet)

        current_node = path_to_pellet[-1]
        remaining_pellets.discard(current_node)

    return full_path if full_path else None

def ucs_find_nearest_pellet(start_node, pellet_nodes):
    from queue import PriorityQueue
    pq = PriorityQueue()
    pq.put((0, start_node, [start_node]))
    visited = {}

    while not pq.empty():
        cost, current, path = pq.get()
        if current in pellet_nodes:
            return path, cost
        if current in visited and visited[current] <= cost:
            continue
        visited[current] = cost
        for direction in get_all_directions():
            neighbor = current.neighbors.get(direction)
            if is_valid_node(neighbor, current, direction):
                move_cost = 3 if direction == PORTAL else 1
                total_cost = cost + move_cost
                if neighbor not in visited or total_cost < visited.get(neighbor, float('inf')):
                    pq.put((total_cost, neighbor, path + [neighbor]))
    return None, float('inf')

def ucs_few_pellets(start_node, pellet_nodes):
    from queue import PriorityQueue
    max_pellets = 7
    
    pq = PriorityQueue()
    initial_collected = set([start_node]) if start_node in pellet_nodes else set()
    pq.put((0, start_node, [start_node], initial_collected))
    visited = {}
    
    while not pq.empty():
        cost, current, path, collected = pq.get()
        
        if len(collected) >= max_pellets or len(collected) == len(pellet_nodes):
            return path
        
        state = (current, frozenset(collected))
        if state in visited and visited[state] <= cost:
            continue
        visited[state] = cost
        
        for direction in get_all_directions():
            neighbor = current.neighbors.get(direction)
            if is_valid_node(neighbor, current, direction):
                move_cost = 3 if direction == PORTAL else 1
                total_cost = cost + move_cost
                
                new_collected = set(collected)
                if neighbor in pellet_nodes:
                    new_collected.add(neighbor)
                
                new_state = (neighbor, frozenset(new_collected))
                if new_state not in visited or total_cost < visited.get(new_state, float('inf')):
                    pq.put((total_cost, neighbor, path + [neighbor], new_collected))
    
    return None
# =============================================================================
# IDS
# =============================================================================
def ids(startNode, pellet_group, heuristic_func=None, max_depth=50):
    print("IDS")
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = get_visible_pellet_nodes(pellet_group)

    if not pellet_nodes:
        return None

    if heuristic_func is not None:
        print(f"🎯 IDS using heuristic: {heuristic_func.__name__}")
    

    current_node = startNode
    remaining_pellets = set(pellet_nodes)
    full_path = []
    
    if len(remaining_pellets) <= 7:
        path_to_pellet = ids_few_pellets(current_node, remaining_pellets, max_depth)
        return path_to_pellet

    while remaining_pellets:
        if heuristic_func is not None:
            nearest_pellet = min(remaining_pellets, key=lambda p: heuristic_func(current_node, p))
            path_to_pellet = ids_find_nearest_pellet(current_node, {nearest_pellet}, max_depth)
        else:
            path_to_pellet = ids_find_nearest_pellet(current_node, remaining_pellets, max_depth)
        if not path_to_pellet:
            break  

        if full_path and path_to_pellet[0] == full_path[-1]:
            full_path.extend(path_to_pellet[1:])
        else:
            full_path.extend(path_to_pellet)

        current_node = path_to_pellet[-1]
        remaining_pellets.discard(current_node)

    return full_path if full_path else None

def ids_find_nearest_pellet(start_node, pellet_nodes, max_depth=50):
    for depth in range(1, max_depth + 1):
        found_path = dls_find_nearest_pellet(start_node, pellet_nodes, depth)
        if found_path is not None:
            return found_path
    return None

def dls_find_nearest_pellet(start_node, pellet_nodes, limit):
    stack = []
    stack.append((start_node, [start_node], 0))
    visited_at_depth = {}  

    while stack:
        current, path, depth = stack.pop()
        if current in pellet_nodes:
            return path
        
        if current in visited_at_depth and visited_at_depth[current] <= depth:
            continue
        visited_at_depth[current] = depth
        
        if depth < limit:
            for direction in get_all_directions():
                neighbor = current.neighbors.get(direction)
                if is_valid_node(neighbor, current, direction):
                    stack.append((neighbor, path + [neighbor], depth + 1))
    return None

def ids_few_pellets(start_node, pellet_nodes, max_depth=50):
    max_pellets = 7
    
    for depth_limit in range(1, max_depth * len(pellet_nodes) + 1):
        result = dls_few_pellets(start_node, pellet_nodes, depth_limit, max_pellets)
        if result is not None:
            return result
    return None

def dls_few_pellets(start_node, pellet_nodes, depth_limit, max_pellets):
    stack = []
    initial_collected = set([start_node]) if start_node in pellet_nodes else set()
    stack.append((start_node, [start_node], initial_collected, 0))
    visited_at_depth = {}  
    
    while stack:
        current, path, collected, depth = stack.pop()
        
        if len(collected) >= max_pellets or len(collected) == len(pellet_nodes):
            return path
        
        state = (current, frozenset(collected))
        
        if state in visited_at_depth and visited_at_depth[state] <= depth:
            continue
        visited_at_depth[state] = depth
        
        if depth < depth_limit:
            for direction in get_all_directions():
                neighbor = current.neighbors.get(direction)
                if is_valid_node(neighbor, current, direction):
                    new_collected = set(collected)
                    if neighbor in pellet_nodes:
                        new_collected.add(neighbor)
                    
                    stack.append((neighbor, path + [neighbor], new_collected, depth + 1))
    
    return None

# =============================================================================
# GREEDY
# =============================================================================

def greedy(start_node, pellet_group, heuristic_func=None):
    print("Greedy")

    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = get_visible_pellet_nodes(pellet_group)
    if not pellet_nodes:
        return None

    if heuristic_func is None:
        heuristic_func = heuristic_manhattan

    current_node = start_node
    remaining_pellets = set(pellet_nodes)
    full_path = [current_node]
    
    
    if len(remaining_pellets) <= 7:
        path_to_pellet = greedy_few_pellets(current_node, remaining_pellets, heuristic_func)
        return path_to_pellet if path_to_pellet else full_path

    
    while remaining_pellets:
        nearest_pellet = min(remaining_pellets, key=lambda n: heuristic_func(current_node, n))
        path_to_pellet = greedy_find_path(current_node, nearest_pellet, heuristic_func)
        if not path_to_pellet:
            break  

        if full_path and path_to_pellet[0] == full_path[-1]:
            full_path.extend(path_to_pellet[1:])
        else:
            full_path.extend(path_to_pellet)
        current_node = nearest_pellet
        remaining_pellets.discard(nearest_pellet)

    return full_path if len(full_path) > 1 else None

def greedy_find_path(start_node, goal_node, heuristic=None):
    from collections import deque

    if heuristic is None:
        heuristic = heuristic_manhattan

    open_set = []
    open_set.append((heuristic(start_node, goal_node), start_node, [start_node]))
    visited = set()
    visited.add(start_node)

    while open_set:
        open_set.sort(key=lambda x: x[0])
        _, current, path = open_set.pop(0)
        if current == goal_node:
            return path
        for direction in get_all_directions():
            neighbor = current.neighbors.get(direction)
            if is_valid_node(neighbor, current, direction) and neighbor not in visited:
                visited.add(neighbor)
                new_path = path + [neighbor]
                h = heuristic(neighbor, goal_node)
                open_set.append((h, neighbor, new_path))
    return None

def greedy_few_pellets(start_node, pellet_nodes, heuristic_func=None):
    if heuristic_func is None:
        heuristic_func = heuristic_manhattan
    
    max_pellets = 7
    
    def calculate_centroid(pellets):
        if not pellets:
            return None
        avg_x = sum(p.position.x for p in pellets) / len(pellets)
        avg_y = sum(p.position.y for p in pellets) / len(pellets)
        return (avg_x, avg_y)
    
    def state_heuristic(node, collected, remaining):
        if not remaining:
            return 0
        centroid = calculate_centroid(remaining)
        if centroid:
            dist = abs(node.position.x - centroid[0]) + abs(node.position.y - centroid[1])
            return dist + len(remaining) * 10  
        return len(remaining) * 10
    
    open_set = []
    initial_collected = set([start_node]) if start_node in pellet_nodes else set()
    initial_remaining = pellet_nodes - initial_collected
    h = state_heuristic(start_node, initial_collected, initial_remaining)
    open_set.append((h, start_node, [start_node], initial_collected))
    visited = {}
    
    while open_set:
        open_set.sort(key=lambda x: x[0])
        _, current, path, collected = open_set.pop(0)
        
        if len(collected) >= max_pellets or len(collected) == len(pellet_nodes):
            return path
        
        state = (current, frozenset(collected))
        if state in visited:
            continue
        visited[state] = True
        
        for direction in get_all_directions():
            neighbor = current.neighbors.get(direction)
            if is_valid_node(neighbor, current, direction):
                new_collected = set(collected)
                if neighbor in pellet_nodes:
                    new_collected.add(neighbor)
                
                new_state = (neighbor, frozenset(new_collected))
                if new_state not in visited:
                    remaining = pellet_nodes - new_collected
                    h = state_heuristic(neighbor, new_collected, remaining)
                    open_set.append((h, neighbor, path + [neighbor], new_collected))
    
    return None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_visible_pellet_nodes(pellet_group):
    return {pellet.node for pellet in pellet_group.pelletList 
            if pellet.node is not None and pellet.visible}

def is_valid_node(neighbor, current_node, direction):
    """
    Args:
        neighbor: Neighbor node
        current_node: Current node
        direction: Direction
    Returns:
        True if valid, False if not
    """
    if neighbor is None:
        return False

    if direction == PORTAL:
        return True
    
    return PACMAN in current_node.access.get(direction, [])

def get_all_directions():
    return [UP, DOWN, LEFT, RIGHT]

# =============================================================================
# HEURISTIC FUNCTIONS
# =============================================================================

def heuristic_manhattan(node1, node2):
    from engine.heuristic import Heuristic
    return Heuristic.manhattan(node1, node2)

def heuristic_euclidean(node1, node2):
    from engine.heuristic import Heuristic
    return Heuristic.euclidean(node1, node2)

def heuristic_mazedistance(node1, node2):
    from engine.heuristic import Heuristic
    return Heuristic.mazedistance(node1, node2)

