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

# =============================================================================
# A*
# =============================================================================
def astar(startNode, pellet_group, heuristic_func=None):
    """
    Thuật toán A* (A-star) để tìm đường đi qua tất cả các pellet, 
    sử dụng heuristic để chọn pellet tiếp theo cần đến.
    heuristic_func: hàm heuristic nhận vào 2 node, trả về giá trị ước lượng chi phí.
    Nếu không truyền heuristic_func, mặc định dùng manhattan_distance.
    Trả về đường đi (list các node) ghé qua tất cả pellet.
    """
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
        # Sử dụng heuristic để chọn pellet gần nhất (theo heuristic_func)
        if heuristic_func is not None:
            next_pellet = min(remaining_pellets, key=lambda p: heuristic_func(current_node, p))
        else:
            next_pellet = min(remaining_pellets, key=lambda p: heuristic_manhattan(current_node, p))
        # Tìm đường đi ngắn nhất từ current_node đến next_pellet bằng A*
        sub_path = astar_single(current_node, next_pellet, heuristic_func)
        if sub_path is None:
            break
        # Nối đường đi vào path (tránh lặp node)
        if path and sub_path[0] == path[-1]:
            path.extend(sub_path[1:])
        else:
            path.extend(sub_path)
        current_node = next_pellet
        remaining_pellets.remove(next_pellet)

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
            # Truy vết đường đi
            path = []
            while current is not None:
                path.insert(0, current)
                current = came_from[current]
            return path

        for direction in get_all_directions():
            neighbor = current.neighbors.get(direction)
            if neighbor and can_move_to(current, direction):
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
