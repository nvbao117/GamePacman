# =============================================================================
# ALGORITHMS_PRACTICAL.PY - TẤT CẢ THUẬT TOÁN THỰC TẾ CHO PACMAN
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
def bfs_practical(startNode, pellet_group, heuristic_func=None):
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
def dfs_practical(startNode, pellet_group, heuristic_func=None):
    """DFS thực tế: fast exploration với heuristic tùy chọn"""
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None
    
    return dfs_guided_exploration(startNode, pellet_nodes, heuristic_func)

def dfs_guided_exploration(startNode, pellet_nodes, heuristic_func=None):
    """DFS với hướng dẫn thông minh và heuristic tùy chọn"""
    current_node = startNode
    remaining_pellets = set(pellet_nodes)
    path = [current_node]
    
    if current_node in remaining_pellets:
        remaining_pellets.remove(current_node)
    
    while remaining_pellets:
        # Chọn direction tốt nhất dựa trên heuristic hoặc density
        if heuristic_func is not None:
            best_direction = choose_best_dfs_direction_with_heuristic(current_node, remaining_pellets, heuristic_func)
        else:
            best_direction = choose_best_dfs_direction(current_node, remaining_pellets)
        if not best_direction:
            break
        
        # Follow direction cho đến khi gặp pellet hoặc dead end
        exploration_path = explore_direction_dfs(current_node, best_direction, remaining_pellets)
        if exploration_path:
            path.extend(exploration_path[1:])
            current_node = exploration_path[-1]
            
            # Remove collected pellets
            for node in exploration_path[1:]:
                remaining_pellets.discard(node)
    
    return path

def choose_best_dfs_direction(current_node, remaining_pellets):
    """Chọn direction tốt nhất cho DFS"""
    best_direction = None
    best_score = -1
    
    for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
        neighbor = current_node.neighbors.get(direction)
        if neighbor and can_move_to(current_node, direction):
            # Score dựa trên số pellets trong hướng này
            score = count_pellets_in_direction(neighbor, remaining_pellets, direction, depth=10)
            if score > best_score:
                best_score = score
                best_direction = direction
    
    return best_direction

def choose_best_dfs_direction_with_heuristic(current_node, remaining_pellets, heuristic_func):
    """Chọn direction tốt nhất cho DFS dựa trên heuristic"""
    best_direction = None
    best_score = float('inf')
    
    for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
        neighbor = current_node.neighbors.get(direction)
        if neighbor and can_move_to(current_node, direction):
            # Tìm pellet gần nhất theo heuristic
            nearest_pellet = min(remaining_pellets, key=lambda p: heuristic_func(neighbor, p))
            score = heuristic_func(neighbor, nearest_pellet)
            if score < best_score:
                best_score = score
                best_direction = direction
    
    return best_direction

def explore_direction_dfs(start_node, direction, remaining_pellets, max_depth=20):
    """Explore theo một direction cho đến khi gặp pellet"""
    current_node = start_node
    path = [current_node]
    depth = 0
    
    while depth < max_depth:
        if current_node.neighbors.get(direction):
            next_node = current_node.neighbors[direction]
            if can_move_to(current_node, direction):
                path.append(next_node)
                current_node = next_node
                depth += 1
                
                # Found pellet
                if next_node in remaining_pellets:
                    return path
            else:
                break
        else:
            break
    
    return path if len(path) > 1 else None

# =============================================================================
# A*
# =============================================================================
def astar_practical(startNode, pellet_group, heuristic_func=None):
    """A* thực tế với heuristic tùy chọn"""
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None
    
    return astar_guided_greedy(startNode, pellet_nodes, heuristic_func)

def astar_guided_greedy(startNode, pellet_nodes, heuristic_func=None):
    """A* guided greedy selection với heuristic tùy chọn"""
    current_node = startNode
    remaining_pellets = set(pellet_nodes)
    path = [current_node]
    
    if current_node in remaining_pellets:
        remaining_pellets.remove(current_node)
    
    while remaining_pellets:
        # Tìm pellet tốt nhất với A* evaluation
        best_pellet = None
        best_cost = float('inf')
        
        # Check top 8 candidates với heuristic tùy chọn
        if heuristic_func is not None:
            candidates = sorted(remaining_pellets,
                              key=lambda p: heuristic_func(current_node, p))[:8]
        else:
            candidates = sorted(remaining_pellets,
                              key=lambda p: manhattan_distance(current_node, p))[:8]
        
        for pellet in candidates:
            # A* cost = actual distance + heuristic to remaining
            actual_distance = astar_distance_fast(current_node, pellet)
            if actual_distance is not None:
                remaining_after = remaining_pellets - {pellet}
                if heuristic_func is not None:
                    # Sử dụng heuristic function được cung cấp
                    heuristic_cost = min(heuristic_func(pellet, p) for p in remaining_after) if remaining_after else 0
                else:
                    heuristic_cost = estimate_remaining_cost(pellet, remaining_after)
                total_cost = actual_distance + heuristic_cost
                
                if total_cost < best_cost:
                    best_cost = total_cost
                    best_pellet = pellet
        
        if not best_pellet:
            break
        
        # Get path to best pellet
        pellet_path = astar_shortest_path_fast(current_node, best_pellet)
        if pellet_path:
            path.extend(pellet_path[1:])
            current_node = best_pellet
            remaining_pellets.remove(best_pellet)
        else:
            break
    
    return path

def estimate_remaining_cost(current_node, remaining_pellets):
    """Estimate cost để visit remaining pellets"""
    if not remaining_pellets:
        return 0
    
    # Simple heuristic: average distance to remaining pellets
    distances = [manhattan_distance(current_node, p) for p in remaining_pellets]
    return sum(distances) / len(distances) * 0.5  # Scale down

# =============================================================================
# UCS
# =============================================================================
def ucs_practical(startNode, pellet_group, heuristic_func=None):
    """UCS thực tế với cost optimization và heuristic tùy chọn"""
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None
    
    return ucs_cost_optimized_greedy(startNode, pellet_nodes, heuristic_func)

def ucs_cost_optimized_greedy(startNode, pellet_nodes, heuristic_func=None):
    """UCS với cost optimization và heuristic tùy chọn"""
    current_node = startNode
    remaining_pellets = set(pellet_nodes)
    path = [current_node]
    total_cost = 0
    
    if current_node in remaining_pellets:
        remaining_pellets.remove(current_node)
    
    while remaining_pellets:
        # Tìm pellet với cost/benefit ratio tốt nhất
        best_pellet = None
        best_ratio = float('inf')
        
        # Sắp xếp candidates theo heuristic hoặc manhattan distance
        if heuristic_func is not None:
            candidates = sorted(remaining_pellets,
                              key=lambda p: heuristic_func(current_node, p))[:6]
        else:
            candidates = sorted(remaining_pellets,
                              key=lambda p: manhattan_distance(current_node, p))[:6]
        
        for pellet in candidates:
            pellet_path, path_cost = ucs_shortest_path_with_cost_fast(current_node, pellet)
            if pellet_path:
                # Benefit = pellet value + position advantage
                benefit = 1.0 + calculate_position_benefit(pellet, remaining_pellets)
                ratio = path_cost / benefit
                
                if ratio < best_ratio:
                    best_ratio = ratio
                    best_pellet = pellet
        
        if not best_pellet:
            break
        
        # Get path to best pellet
        pellet_path, path_cost = ucs_shortest_path_with_cost_fast(current_node, best_pellet)
        if pellet_path:
            path.extend(pellet_path[1:])
            current_node = best_pellet
            remaining_pellets.remove(best_pellet)
            total_cost += path_cost
        else:
            break
    
    return path

def calculate_position_benefit(pellet, remaining_pellets):
    """Calculate benefit của position này"""
    if not remaining_pellets:
        return 0
    
    # Benefit cao nếu gần nhiều pellets khác
    nearby_count = sum(1 for p in remaining_pellets 
                      if manhattan_distance(pellet, p) <= 5)
    return nearby_count * 0.2

# =============================================================================
# IDS
# =============================================================================
def ids_practical(startNode, pellet_group, heuristic_func=None):
    """IDS thực tế với limited depth và heuristic tùy chọn"""
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None
    
    return ids_limited_search(startNode, pellet_nodes, heuristic_func)

def ids_limited_search(startNode, pellet_nodes, heuristic_func=None):
    """IDS với limited search per pellet và heuristic tùy chọn"""
    current_node = startNode
    remaining_pellets = set(pellet_nodes)
    path = [current_node]
    
    if current_node in remaining_pellets:
        remaining_pellets.remove(current_node)
    
    while remaining_pellets:
        # Tìm pellet tiếp theo với limited IDS và heuristic
        best_pellet = None
        best_path = None
        min_depth = float('inf')
        
        # Sắp xếp pellets theo heuristic hoặc manhattan distance
        if heuristic_func is not None:
            sorted_pellets = sorted(remaining_pellets, key=lambda p: heuristic_func(current_node, p))
        else:
            sorted_pellets = sorted(remaining_pellets, key=lambda p: manhattan_distance(current_node, p))
        
        # Try IDS on nearest candidates (đã được sắp xếp theo heuristic)
        candidates = sorted_pellets[:5]
        
        for pellet in candidates:
            for depth in range(1, 15):  # Limited depth
                pellet_path = ids_depth_limited_search(current_node, pellet, depth)
                if pellet_path:
                    if len(pellet_path) < min_depth:
                        min_depth = len(pellet_path)
                        best_pellet = pellet
                        best_path = pellet_path
                    break  # Found at this depth
        
        if not best_path:
            break
        
        path.extend(best_path[1:])
        current_node = best_pellet
        remaining_pellets.remove(best_pellet)
    
    return path

def ids_depth_limited_search(start_node, target_node, max_depth):
    """Depth limited search cho IDS"""
    def dls(node, target, depth, path, visited):
        if depth < 0:
            return None
        if node == target:
            return path
        if node in visited:
            return None
        
        visited.add(node)
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = node.neighbors.get(direction)
            if neighbor and can_move_to(node, direction):
                result = dls(neighbor, target, depth-1, path + [neighbor], visited.copy())
                if result:
                    return result
        return None
    
    return dls(start_node, target_node, max_depth, [start_node], set())

# =============================================================================
# GREEDY
# =============================================================================
def greedy_practical(startNode, pellet_group, heuristic_func=None):
    """Greedy thực tế - fastest execution với heuristic tùy chọn"""
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None
    
    return greedy_smart_nearest(startNode, pellet_nodes, heuristic_func)

def greedy_smart_nearest(startNode, pellet_nodes, heuristic_func=None):
    """Smart nearest với lookahead và heuristic tùy chọn"""
    current_node = startNode
    remaining_pellets = set(pellet_nodes)
    path = [current_node]
    
    if current_node in remaining_pellets:
        remaining_pellets.remove(current_node)
    
    while remaining_pellets:
        # Smart selection: không chỉ nearest mà còn xem trước 1 bước
        best_pellet = None
        best_score = -1
        
        # Check top 5 nearest với heuristic
        if heuristic_func is not None:
            candidates = sorted(remaining_pellets, key=lambda p: heuristic_func(current_node, p))[:5]
        else:
            candidates = sorted(remaining_pellets, key=lambda p: manhattan_distance(current_node, p))[:5]
        
        for pellet in candidates:
            # Sử dụng heuristic hoặc manhattan distance
            if heuristic_func is not None:
                distance = heuristic_func(current_node, pellet)
            else:
                distance = manhattan_distance(current_node, pellet)
            
            # Lookahead score: sau khi đến pellet này, còn bao nhiều pellets gần
            remaining_after = remaining_pellets - {pellet}
            if remaining_after:
                if heuristic_func is not None:
                    nearby_after = sum(1 for p in remaining_after 
                                     if heuristic_func(pellet, p) <= 8)
                else:
                    nearby_after = sum(1 for p in remaining_after 
                                     if manhattan_distance(pellet, p) <= 8)
                score = nearby_after * 10 - distance
            else:
                score = 100 - distance  # Last pellet bonus
            
            if score > best_score:
                best_score = score
                best_pellet = pellet
        
        if not best_pellet:
            break
        
        # Simple path to best pellet
        pellet_path = simple_path_to_pellet(current_node, best_pellet)
        if pellet_path:
            path.extend(pellet_path[1:])
            current_node = best_pellet
            remaining_pellets.remove(best_pellet)
        else:
            break
    
    return path

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================
def astar_shortest_path_fast(startNode, targetNode, max_nodes=100):
    """Fast A* với node limit"""
    if startNode == targetNode:
        return [startNode]
    
    pq = PriorityQueue()
    pq.put((0, startNode))
    parent = {startNode: None}
    g_cost = {startNode: 0}
    nodes_explored = 0
    
    while not pq.empty() and nodes_explored < max_nodes:
        current_f, current_node = pq.get()
        nodes_explored += 1
        
        if current_node == targetNode:
            return trace_path(parent, current_node)
        
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)
            
            if neighbor and can_move_to(current_node, direction):
                tentative_g = g_cost[current_node] + 1
                
                if neighbor not in g_cost or tentative_g < g_cost[neighbor]:
                    g_cost[neighbor] = tentative_g
                    f_cost = tentative_g + manhattan_distance(neighbor, targetNode)
                    pq.put((f_cost, neighbor))
                    parent[neighbor] = current_node
    
    return None

def astar_distance_fast(startNode, targetNode):
    """Fast A* distance calculation"""
    path = astar_shortest_path_fast(startNode, targetNode)
    return len(path) - 1 if path else None

def ucs_shortest_path_with_cost_fast(startNode, targetNode, max_nodes=80):
    """Fast UCS với cost"""
    if startNode == targetNode:
        return [startNode], 0
    
    pq = PriorityQueue()
    pq.put((0, startNode))
    parent = {startNode: None}
    costs = {startNode: 0}
    nodes_explored = 0
    
    while not pq.empty() and nodes_explored < max_nodes:
        current_cost, current_node = pq.get()
        nodes_explored += 1
        
        if current_node == targetNode:
            path = trace_path(parent, current_node)
            return path, current_cost
        
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)
            
            if neighbor and can_move_to(current_node, direction):
                move_cost = 3 if direction == PORTAL else 1
                new_cost = current_cost + move_cost
                
                if neighbor not in costs or new_cost < costs[neighbor]:
                    costs[neighbor] = new_cost
                    parent[neighbor] = current_node
                    pq.put((new_cost, neighbor))
    
    return None, float('inf')

def simple_path_to_pellet(startNode, targetNode):
    """Đường đi đơn giản nhất"""
    # Simple greedy path
    current = startNode
    path = [current]
    max_steps = 50
    
    for _ in range(max_steps):
        if current == targetNode:
            break
        
        best_neighbor = None
        min_distance = float('inf')
        
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = current.neighbors.get(direction)
            if neighbor and can_move_to(current, direction):
                dist = manhattan_distance(neighbor, targetNode)
                if dist < min_distance:
                    min_distance = dist
                    best_neighbor = neighbor
        
        if best_neighbor:
            path.append(best_neighbor)
            current = best_neighbor
        else:
            break
    
    return path if current == targetNode else None

def count_pellets_in_direction(start_node, pellet_nodes, direction, depth=10):
    """Đếm pellets theo một direction"""
    count = 0
    current = start_node
    
    for _ in range(depth):
        if current.neighbors.get(direction):
            current = current.neighbors[direction]
            if current in pellet_nodes:
                count += 1
        else:
            break
    
    return count

def manhattan_distance(node1, node2):
    """Manhattan distance"""
    if node1 is None or node2 is None:
        return float('inf')
    
    dx = abs(node1.position.x - node2.position.x)
    dy = abs(node1.position.y - node2.position.y)
    return dx + dy

def trace_path(parent, goalNode):
    """Trace path"""
    path = []
    current = goalNode
    while current is not None:
        path.insert(0, current)
        current = parent[current]
    return path

# =============================================================================
# MAIN FUNCTIONS
# =============================================================================
def bfs(startNode, endNode, pellet_group):
    return bfs_practical(startNode, pellet_group)

def bfs_manhattan(startNode, endNode, pellet_group):
    """BFS với Manhattan distance heuristic"""
    return bfs_practical(startNode, pellet_group, heuristic_manhattan)

def bfs_euclidean(startNode, endNode, pellet_group):
    """BFS với Euclidean distance heuristic"""
    return bfs_practical(startNode, pellet_group, heuristic_euclidean)


def dfs(startNode, endNode, pellet_group):
    return dfs_practical(startNode, pellet_group)

def a_star(startNode, endNode, pellet_group):
    return astar_practical(startNode, pellet_group)

def ucs(startNode, endNode, pellet_group):
    return ucs_practical(startNode, pellet_group)

def iterative_deepening_dfs(startNode, endNode, pellet_group, max_depth=50):
    return ids_practical(startNode, pellet_group)

def greedy(startNode, endNode, pellet_group):
    return greedy_practical(startNode, pellet_group)

# =============================================================================
# HEURISTIC COMPARISON UTILITIES
# =============================================================================
def compare_bfs_heuristics(startNode, pellet_group):
    """
    So sánh hiệu suất các heuristic khác nhau cho BFS
    Returns: dict với kết quả của từng heuristic
    """
    heuristics = {
        'no_heuristic': None,
        'manhattan': heuristic_manhattan,
        'euclidean': heuristic_euclidean
    }
    
    results = {}
    
    for name, heuristic in heuristics.items():
        start_time = time.time()
        path = bfs_practical(startNode, pellet_group, heuristic)
        end_time = time.time()
        
        results[name] = {
            'path_length': len(path) if path else 0,
            'execution_time': end_time - start_time,
            'success': path is not None
        }
    
    return results

def get_best_bfs_heuristic(startNode, pellet_group):
    """
    Tự động chọn heuristic tốt nhất cho BFS dựa trên hiệu suất
    """
    results = compare_bfs_heuristics(startNode, pellet_group)
    
    # Chọn heuristic có path ngắn nhất và thành công
    successful_results = {k: v for k, v in results.items() if v['success']}
    
    if not successful_results:
        return None, None
    
    # Ưu tiên path ngắn nhất, nếu bằng nhau thì chọn nhanh nhất
    best_heuristic = min(successful_results.keys(), 
                        key=lambda k: (successful_results[k]['path_length'], 
                                     successful_results[k]['execution_time']))
    
    heuristic_func = None
    if best_heuristic != 'no_heuristic':
        heuristic_func = globals()[f'heuristic_{best_heuristic}']
    
    return best_heuristic, heuristic_func

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
    return [UP, DOWN, LEFT, RIGHT, PORTAL]

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
