from constants import *
from objects.nodes import Node

def dfs(startNode, endNode, pellet_group):
    """Main DFS function that routes to appropriate pathfinding algorithm."""
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None

    if endNode is not None and endNode in pellet_nodes:
        return dfs_to_target(startNode, endNode)
    
    return dfs_to_nearest_pellet(startNode, pellet_nodes)

def dfs_to_target(startNode, targetNode):
    """Find path to specific target using DFS with parent tracking."""
    if startNode == targetNode:
        return [startNode]

    stack = [startNode]
    parent = {startNode: None}
    visited = {startNode}

    while stack:
        current_node = stack.pop()

        if current_node == targetNode:
            return trace_path(parent, current_node)

        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)
            if (neighbor and neighbor not in visited and 
                can_move_to(current_node, direction)):
                visited.add(neighbor)
                parent[neighbor] = current_node
                stack.append(neighbor)

    return None

def dfs_to_nearest_pellet(startNode, pellet_nodes):
    """Find path to nearest pellet using DFS with parent tracking."""
    if startNode in pellet_nodes:
        return [startNode]

    stack = [startNode]
    parent = {startNode: None}
    visited = {startNode}

    while stack:
        current_node = stack.pop()

        if current_node in pellet_nodes:
            return trace_path(parent, current_node)

        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)
            if (neighbor and neighbor not in visited and 
                can_move_to(current_node, direction)):
                visited.add(neighbor)
                parent[neighbor] = current_node
                stack.append(neighbor)

    return None

def dfs_with_priority(startNode, endNode, pellet_group, priority_direction=None):
    """DFS with directional priority preference."""
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None

    if endNode is not None and endNode in pellet_nodes:
        return dfs_to_target_with_priority(startNode, endNode, priority_direction)
    
    return dfs_to_nearest_pellet_with_priority(startNode, pellet_nodes, priority_direction)

def dfs_to_target_with_priority(startNode, targetNode, priority_direction=None):
    """Find path to target with directional priority."""
    if startNode == targetNode:
        return [startNode]
    
    stack = [startNode]
    parent = {startNode: None}
    visited = {startNode}

    while stack:
        current_node = stack.pop()

        if current_node == targetNode:
            return trace_path(parent, current_node)
        
        directions = get_prioritized_directions(priority_direction)
        
        for direction in directions:
            neighbor = current_node.neighbors.get(direction)
            
            if (neighbor and neighbor not in visited and 
                can_move_to(current_node, direction)):
                visited.add(neighbor)
                parent[neighbor] = current_node
                stack.append(neighbor)

    return None

def dfs_to_nearest_pellet_with_priority(startNode, pellet_nodes, priority_direction=None):
    """Find path to nearest pellet with directional priority."""
    if startNode in pellet_nodes:
        return [startNode]
    
    stack = [startNode]
    parent = {startNode: None}
    visited = {startNode}

    while stack:
        current_node = stack.pop()

        if current_node in pellet_nodes:
            return trace_path(parent, current_node)
        
        directions = get_prioritized_directions(priority_direction)
        
        for direction in directions:
            neighbor = current_node.neighbors.get(direction)
            
            if (neighbor and neighbor not in visited and 
                can_move_to(current_node, direction)):
                visited.add(neighbor)
                parent[neighbor] = current_node
                stack.append(neighbor)

    return None

def smart_dfs_for_pacman(startNode, endNode, pellet_group, max_depth=15):
    """Smart DFS with depth limiting and optimizations."""
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None

    # If we have a specific target that contains a pellet, go for it
    if endNode is not None and endNode in pellet_nodes:
        return limited_dfs_iterative(startNode, endNode, pellet_nodes, max_depth)
    
    # Otherwise find nearest pellet
    return limited_dfs_iterative(startNode, None, pellet_nodes, max_depth)

def limited_dfs_iterative(startNode, target, pellet_nodes, max_depth):
    """Iterative depth-limited DFS to avoid recursion stack issues."""
    stack = [(startNode, [startNode], 0)]  # (node, path, depth)
    visited_at_depth = {}  # Track best depth we've seen each node
    
    while stack:
        current_node, path, depth = stack.pop()
        
        # Skip if we've seen this node at a better (lower) depth
        if current_node in visited_at_depth and visited_at_depth[current_node] <= depth:
            continue
        visited_at_depth[current_node] = depth
        
        # Check if we found our goal
        if current_node in pellet_nodes and (target is None or current_node == target):
            return path
        
        # Don't explore further if we've reached max depth
        if depth >= max_depth:
            continue
            
        # Add neighbors to stack
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)
            
            if (neighbor and can_move_to(current_node, direction) and
                (neighbor not in visited_at_depth or visited_at_depth[neighbor] > depth + 1)):
                stack.append((neighbor, path + [neighbor], depth + 1))
    
    return None

# ------------------------------------------------------------
# IDS (Iterative Deepening Search)
# ------------------------------------------------------------
def ids(startNode, endNode, pellet_group, max_depth=50):
    """Iterative Deepening Search: tăng dần độ sâu cho đến khi tìm thấy đường đi.

    - Nếu endNode thuộc tập pellet thì tìm đúng đích đó; nếu không, tìm pellet gần bất kỳ.
    - Trả về danh sách nodes tạo thành đường đi hoặc None nếu không tìm thấy.
    """
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    if not pellet_nodes:
        return None

    target = endNode if endNode is not None and endNode in pellet_nodes else None

    for depth_limit in range(max_depth + 1):
        path = _depth_limited_search(startNode, target, pellet_nodes, depth_limit)
        if path is not None:
            return path
    return None

def _depth_limited_search(startNode, target, pellet_nodes, depth_limit):
    """Depth-Limited Search không đệ quy (dùng stack), dừng ở độ sâu cho trước."""
    # Phần tử stack: (node, parent_node, depth, iterator_directions)
    # Dùng parent map để khôi phục đường đi
    parent = {startNode: None}
    stack = [(startNode, 0, iter([UP, DOWN, LEFT, RIGHT, PORTAL]))]

    while stack:
        current_node, depth, dir_iter = stack[-1]

        # Kiểm tra goal
        if (target is None and current_node in pellet_nodes) or (target is not None and current_node == target):
            return trace_path(parent, current_node)

        # Nếu đạt giới hạn độ sâu, backtrack
        if depth == depth_limit:
            stack.pop()
            continue

        # Lấy hướng kế tiếp từ iterator; nếu hết, backtrack
        try:
            direction = next(dir_iter)
        except StopIteration:
            stack.pop()
            continue

        neighbor = current_node.neighbors.get(direction)
        if neighbor and can_move_to(current_node, direction) and neighbor not in parent:
            parent[neighbor] = current_node
            stack.append((neighbor, depth + 1, iter([UP, DOWN, LEFT, RIGHT, PORTAL])))
    
    return None

def can_move_to(current_node, direction):
    """Check if movement in given direction is allowed."""
    if direction == PORTAL:
        return True  
    else:
        return PACMAN in current_node.access[direction]

def trace_path(parent, goalNode):
    """Reconstruct path from parent tracking dictionary."""
    path = []
    current = goalNode
    while current is not None:
        path.insert(0, current)
        current = parent[current]
    return path

def get_prioritized_directions(priority_direction):
    """Get directions list with priority direction first."""
    all_directions = [UP, DOWN, LEFT, RIGHT, PORTAL]
    
    if priority_direction is None:
        return all_directions
    
    if priority_direction in all_directions:
        all_directions.remove(priority_direction)
        return [priority_direction] + all_directions
    
    return all_directions

# Additional utility function for debugging
def dfs_with_stats(startNode, endNode, pellet_group):
    """DFS that returns both path and search statistics."""
    if not pellet_group or not pellet_group.pelletList:
        return None, {"nodes_explored": 0, "max_depth": 0}

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None, {"nodes_explored": 0, "max_depth": 0}

    target = endNode if endNode and endNode in pellet_nodes else None
    
    stack = [(startNode, [startNode], 0)]
    visited = set()
    nodes_explored = 0
    max_depth = 0

    while stack:
        current_node, path, depth = stack.pop()
        
        if current_node in visited:
            continue
            
        visited.add(current_node)
        nodes_explored += 1
        max_depth = max(max_depth, depth)

        if current_node in pellet_nodes and (target is None or current_node == target):
            stats = {"nodes_explored": nodes_explored, "max_depth": max_depth}
            return path, stats

        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)
            if (neighbor and neighbor not in visited and 
                can_move_to(current_node, direction)):
                stack.append((neighbor, path + [neighbor], depth + 1))

    stats = {"nodes_explored": nodes_explored, "max_depth": max_depth}
    return None, stats