from collections import deque
from constants import *
from objects.nodes import Node
def bfs(startNode, endNode, pellet_group):
    """
    Thuật toán BFS tìm đường đi từ startNode đến pellet gần nhất hoặc endNode cụ thể
    
    Args:
        startNode: Node bắt đầu
        endNode: Node đích cụ thể (có thể None để tìm pellet gần nhất)
        pellet_group: Nhóm pellets còn lại trong game
    
    Returns:
        List các nodes tạo thành đường đi, hoặc None nếu không tìm thấy
    """
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None

    if endNode is not None and endNode in pellet_nodes:
        return bfs_to_target(startNode, endNode)
    
    return bfs_to_nearest_pellet(startNode, pellet_nodes)

def bfs_to_target(startNode, targetNode):
    if startNode == targetNode:
        return [startNode]
    
    queue = deque([startNode])
    parent = {startNode: None}
    visited = {startNode}

    while queue:
        current_node = queue.popleft()

        if current_node == targetNode:
            return trace_path(parent, current_node)
        
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)
            
            if (neighbor and neighbor not in visited and 
                can_move_to(current_node, direction)):
                visited.add(neighbor)
                parent[neighbor] = current_node
                queue.append(neighbor)

    return None

def bfs_to_nearest_pellet(startNode, pellet_nodes):
    """
    BFS tìm đường đi đến pellet gần nhất
    """
    if startNode in pellet_nodes:
        return [startNode]
    
    queue = deque([startNode])
    parent = {startNode: None}
    visited = {startNode}

    while queue:
        current_node = queue.popleft()

        if current_node in pellet_nodes:
            return trace_path(parent, current_node)
        
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)
            
            if (neighbor and neighbor not in visited and 
                can_move_to(current_node, direction)):
                visited.add(neighbor)
                parent[neighbor] = current_node
                queue.append(neighbor)

    return None

def can_move_to(current_node, direction):
    """
    Kiểm tra xem có thể di chuyển theo hướng direction từ current_node không
    """
    if direction == PORTAL:
        return True  
    else:
        return PACMAN in current_node.access[direction]

def trace_path(parent, goalNode):
    path = []
    current = goalNode
    while current is not None:
        path.insert(0, current)
        current = parent[current]
    return path

def bfs_with_priority(startNode, endNode, pellet_group, priority_direction=None):
    """
    BFS với ưu tiên hướng di chuyển (để Pacman di chuyển mượt mà hơn)
    
    Args:
        startNode: Node bắt đầu
        endNode: Node đích cụ thể
        pellet_group: Nhóm pellets
        priority_direction: Hướng ưu tiên (UP, DOWN, LEFT, RIGHT)
    
    Returns:
        List các nodes tạo thành đường đi
    """
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None

    if endNode is not None and endNode in pellet_nodes:
        return bfs_to_target_with_priority(startNode, endNode, priority_direction)
    
    return bfs_to_nearest_pellet_with_priority(startNode, pellet_nodes, priority_direction)

def bfs_to_target_with_priority(startNode, targetNode, priority_direction=None):
    """
    BFS đến target với ưu tiên hướng
    """
    if startNode == targetNode:
        return [startNode]
    
    queue = deque([startNode])
    parent = {startNode: None}
    visited = {startNode}

    while queue:
        current_node = queue.popleft()

        if current_node == targetNode:
            return trace_path(parent, current_node)
        
        # Sắp xếp các hướng theo độ ưu tiên
        directions = get_prioritized_directions(priority_direction)
        
        for direction in directions:
            neighbor = current_node.neighbors.get(direction)
            
            if (neighbor and neighbor not in visited and 
                can_move_to(current_node, direction)):
                visited.add(neighbor)
                parent[neighbor] = current_node
                queue.append(neighbor)

    return None

def bfs_to_nearest_pellet_with_priority(startNode, pellet_nodes, priority_direction=None):
    """
    BFS đến pellet gần nhất với ưu tiên hướng
    """
    if startNode in pellet_nodes:
        return [startNode]
    
    queue = deque([startNode])
    parent = {startNode: None}
    visited = {startNode}

    while queue:
        current_node = queue.popleft()

        if current_node in pellet_nodes:
            return trace_path(parent, current_node)
        
        directions = get_prioritized_directions(priority_direction)
        
        for direction in directions:
            neighbor = current_node.neighbors.get(direction)
            
            if (neighbor and neighbor not in visited and 
                can_move_to(current_node, direction)):
                visited.add(neighbor)
                parent[neighbor] = current_node
                queue.append(neighbor)

    return None

def get_prioritized_directions(priority_direction):
    """
    Sắp xếp các hướng theo độ ưu tiên
    """
    all_directions = [UP, DOWN, LEFT, RIGHT, PORTAL]
    
    if priority_direction is None:
        return all_directions
    
    # Đưa hướng ưu tiên lên đầu
    if priority_direction in all_directions:
        all_directions.remove(priority_direction)
        return [priority_direction] + all_directions
    
    return all_directions
