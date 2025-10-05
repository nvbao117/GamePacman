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
    """
    BFS practical pathfinding to collect all pellets.
    Optionally uses a heuristic function to prioritize which pellet to go to next.
    """
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = get_visible_pellet_nodes(pellet_group)

    if not pellet_nodes:
        return None

    # Debug: In ra heuristic đang sử dụng
    if heuristic_func is not None:
        print(f"🎯 BFS using heuristic: {heuristic_func.__name__}")
    else:
        print("🎯 BFS using NO heuristic (None)")

    current_node = startNode
    remaining_pellets = set(pellet_nodes)
    full_path = []

    while remaining_pellets:
        if heuristic_func is not None:
            # Tìm pellet gần nhất theo heuristic
            nearest_pellet = min(remaining_pellets, key=lambda p: heuristic_func(current_node, p))
            path_to_pellet = bfs_find_nearest_pellet(current_node, {nearest_pellet})
        else:
            if len(remaining_pellets) <= 7:
                path_to_pellet = bfs_few_pellets(current_node, remaining_pellets)
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
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = get_visible_pellet_nodes(pellet_group)

    if not pellet_nodes:
        return None

    # Debug: In ra heuristic đang sử dụng
    if heuristic_func is not None:
        print(f"🎯 DFS using heuristic: {heuristic_func.__name__}")
    else:
        print("🎯 DFS using NO heuristic (None)")

    current_node = startNode
    remaining_pellets = set(pellet_nodes)
    full_path = []

    while remaining_pellets:
        if heuristic_func is not None:
            # Tìm pellet gần nhất theo heuristic
            nearest_pellet = min(remaining_pellets, key=lambda p: heuristic_func(current_node, p))
            path_to_pellet = dfs_find_nearest_pellet(current_node, {nearest_pellet})
        else:
            if len(remaining_pellets) <= 7:
                path_to_pellet = dfs_few_pellets(current_node, remaining_pellets)
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
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = get_visible_pellet_nodes(pellet_group)
    if not pellet_nodes:
        return None

    ghost_nodes = set()
    if ghost_group is not None and hasattr(ghost_group, 'ghosts'):
        for ghost in ghost_group.ghosts:
            if hasattr(ghost, 'node') and getattr(ghost, 'visible', True):
                ghost_nodes.add(ghost.node)

    remaining_pellets = set(pellet_nodes)
    path = []
    current_node = startNode
    if current_node in remaining_pellets:
        remaining_pellets.remove(current_node)
        path.append(current_node)

    while remaining_pellets:
        if heuristic_func is not None:
            next_pellet = min(remaining_pellets, key=lambda p: heuristic_func(current_node, p))
        else:
            next_pellet = min(remaining_pellets, key=lambda p: heuristic_manhattan(current_node, p))
        sub_path = astar_single(current_node, next_pellet, ghost_nodes, heuristic_func, ghost_avoid_dist)
        if sub_path is None:
            break
        if path and sub_path[0] == path[-1]:
            path.extend(sub_path[1:])
        else:
            path.extend(sub_path)
        current_node = next_pellet
        remaining_pellets.remove(next_pellet)

    return path if path else None

def astar_single(start, goal, ghost_nodes=None, heuristic_func=None, ghost_avoid_dist=2):
    from queue import PriorityQueue

    if start == goal:
        return [start]

    open_set = PriorityQueue()
    open_set.put((0, start))
    came_from = {start: None}
    g_score = {start: 0}

    # Để né ghost: tạo set các node nguy hiểm (gần ghost trong ghost_avoid_dist)
    danger_nodes = set()
    if ghost_nodes:
        for ghost_node in ghost_nodes:
            # BFS nhỏ để lấy các node trong bán kính ghost_avoid_dist quanh ghost
            queue = [(ghost_node, 0)]
            visited = set([ghost_node])
            while queue:
                node, dist = queue.pop(0)
                if dist > ghost_avoid_dist:
                    continue
                danger_nodes.add(node)
                for direction in get_all_directions():
                    neighbor = node.neighbors.get(direction)
                    if neighbor and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, dist + 1))

    while not open_set.empty():
        _, current = open_set.get()
        if current == goal:
            # Truy vết đường đi
            path = []
            while current is not None:
                path.insert(0, current)
                current = came_from[current]
            return path

        for direction in get_all_directions():
            neighbor = current.neighbors.get(direction)
            if neighbor and can_move_to(current, direction):
                # Né ghost: bỏ qua node nguy hiểm (trừ khi là goal)
                if neighbor in danger_nodes and neighbor != goal:
                    continue
                tentative_g = g_score[current] + 1
                if neighbor not in g_score or tentative_g < g_score[neighbor]:
                    g_score[neighbor] = tentative_g
                    if heuristic_func is not None:
                        h = heuristic_func(neighbor, goal)
                    else:
                        h = heuristic_manhattan(neighbor, goal)
                    # Có thể cộng thêm penalty nếu neighbor gần ghost (tăng heuristic)
                    if ghost_nodes:
                        min_ghost_dist = min(heuristic_manhattan(neighbor, g) for g in ghost_nodes)
                        if min_ghost_dist <= ghost_avoid_dist:
                            h += 100 * (ghost_avoid_dist + 1 - min_ghost_dist)  # penalty mạnh khi gần ghost
                    f = tentative_g + h
                    open_set.put((f, neighbor))
                    came_from[neighbor] = current
    return None

# =============================================================================
# UCS
# =============================================================================
def ucs(startNode, pellet_group, heuristic_func=None):
    """
    UCS practical pathfinding to collect all pellets.
    Optionally uses a heuristic function to prioritize which pellet to go to next.
    """
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = get_visible_pellet_nodes(pellet_group)

    if not pellet_nodes:
        return None

    # Debug: In ra heuristic đang sử dụng
    if heuristic_func is not None:
        print(f"🎯 UCS using heuristic: {heuristic_func.__name__}")
    else:
        print("🎯 UCS using NO heuristic (None)")

    current_node = startNode
    remaining_pellets = set(pellet_nodes)
    full_path = []

    while remaining_pellets:
        if heuristic_func is not None:
            # Tìm pellet gần nhất theo heuristic
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
# =============================================================================
# IDS
# =============================================================================
def ids(startNode, pellet_group, heuristic_func=None, max_depth=50):
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = get_visible_pellet_nodes(pellet_group)

    if not pellet_nodes:
        return None

    if heuristic_func is not None:
        print(f"🎯 IDS using heuristic: {heuristic_func.__name__}")
    else:
        print("🎯 IDS using NO heuristic (None)")

    current_node = startNode
    remaining_pellets = set(pellet_nodes)
    full_path = []

    while remaining_pellets:
        if heuristic_func is not None:
            # Tìm pellet gần nhất theo heuristic
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
    """
    Tìm đường đi đến pellet gần nhất bằng IDS (Iterative Deepening Search)
    """
    for depth in range(1, max_depth + 1):
        found_path = dls_find_nearest_pellet(start_node, pellet_nodes, depth)
        if found_path is not None:
            return found_path
    return None

def dls_find_nearest_pellet(start_node, pellet_nodes, limit):
    """
    Depth-Limited Search (DLS) cho IDS
    """
    stack = []
    stack.append((start_node, [start_node], 0))
    visited = set()
    visited.add(start_node)

    while stack:
        current, path, depth = stack.pop()
        if current in pellet_nodes:
            return path
        if depth < limit:
            for direction in get_all_directions():
                neighbor = current.neighbors.get(direction)
                if is_valid_node(neighbor, current, direction) and neighbor not in visited:
                    visited.add(neighbor)
                    stack.append((neighbor, path + [neighbor], depth + 1))
    return None

# =============================================================================
# GREEDY
# =============================================================================

def greedy(start_node, pellet_group, heuristic_func=None):
    """
    Tìm đường đi qua tất cả các pellet bằng thuật toán Greedy với heuristic.
    Ở mỗi bước, chọn pellet gần nhất (theo heuristic) và di chuyển tới đó.
    """
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = get_visible_pellet_nodes(pellet_group)
    if not pellet_nodes:
        return None

    # Sử dụng heuristic mặc định nếu không có
    if heuristic_func is None:
        heuristic_func = heuristic_manhattan

    current_node = start_node
    remaining_pellets = set(pellet_nodes)
    full_path = [current_node]

    while remaining_pellets:
        # Tìm pellet gần nhất theo heuristic
        nearest_pellet = min(remaining_pellets, key=lambda n: heuristic_func(current_node, n))
        # Tìm đường đi ngắn nhất (theo số bước) tới pellet gần nhất
        path_to_pellet = greedy_find_path(current_node, nearest_pellet, heuristic_func)
        if not path_to_pellet:
            break  # Không tìm được đường đi

        # Nối đường đi vào full_path (tránh lặp node đầu)
        if full_path and path_to_pellet[0] == full_path[-1]:
            full_path.extend(path_to_pellet[1:])
        else:
            full_path.extend(path_to_pellet)
        current_node = nearest_pellet
        remaining_pellets.discard(nearest_pellet)

    return full_path if len(full_path) > 1 else None

# Hàm này bị lỗi vì khi định nghĩa hàm, tham số mặc định heuristic=heuristic_manhattan
# nhưng tại thời điểm Python đọc định nghĩa hàm này, biến heuristic_manhattan có thể chưa được định nghĩa ở phía trên.
# Để tránh lỗi này, nên đặt giá trị mặc định là None, và trong thân hàm kiểm tra nếu heuristic là None thì gán bằng heuristic_manhattan.
def greedy_find_path(start_node, goal_node, heuristic=None):
    """
    Tìm đường đi từ start_node tới goal_node bằng thuật toán Greedy Best-First Search.
    """
    from collections import deque

    # Sử dụng heuristic mặc định nếu không có
    if heuristic is None:
        heuristic = heuristic_manhattan

    open_set = []
    open_set.append((heuristic(start_node, goal_node), start_node, [start_node]))
    visited = set()
    visited.add(start_node)

    while open_set:
        # Sắp xếp theo heuristic tăng dần
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

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def get_visible_pellet_nodes(pellet_group):
    """Lấy tất cả node của pellet còn hiển thị"""
    return {pellet.node for pellet in pellet_group.pelletList 
            if pellet.node is not None and pellet.visible}

def is_valid_node(neighbor, current_node, direction):
    return neighbor is not None and can_move_to(current_node, direction)

def can_move_to(current_node, direction):
    """Kiểm tra có thể move"""
    if direction == PORTAL:
        return True  
    else:
        return PACMAN in current_node.access[direction]

def get_all_directions():
    return [UP, DOWN, LEFT, RIGHT]

# =============================================================================
# HEURISTIC FUNCTIONS
# =============================================================================
def heuristic_manhattan(node1, node2):
    """Heuristic Manhattan distance (ô lưới)"""
    if node1 is None or node2 is None:
        return float('inf')
    distance = abs(node1.position.x - node2.position.x) + abs(node1.position.y - node2.position.y)
    return distance

def heuristic_euclidean(node1, node2):
    """Heuristic Euclidean distance (khoảng cách thực)"""
    if node1 is None or node2 is None:
        return float('inf')
    dx = node1.position.x - node2.position.x
    dy = node1.position.y - node2.position.y
    distance = (dx ** 2 + dy ** 2) ** 0.5
    return distance
