from config import *
from core.nodes import Node

def dfs(startNode, endNode, pellet_group):
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

def can_move_to(current_node, direction):
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

def get_prioritized_directions(priority_direction):
    all_directions = [UP, DOWN, LEFT, RIGHT, PORTAL]
    
    if priority_direction is None:
        return all_directions
    
    if priority_direction in all_directions:
        all_directions.remove(priority_direction)
        return [priority_direction] + all_directions
    
    return all_directions

def smart_dfs_for_pacman(startNode, endNode, pellet_group, max_depth=10):
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None

    if endNode is not None and endNode in pellet_nodes:
        target = endNode
    else:
        target = None
    return limited_dfs(startNode, target, pellet_nodes, max_depth)

def limited_dfs(startNode, target, pellet_nodes, max_depth, visited=None):
    if visited is None:
        visited = set()
    
    if startNode in visited:
        return None
    
    if startNode in pellet_nodes and (target is None or startNode == target):
        return [startNode]
    
    if max_depth <= 0:
        return None
    visited.add(startNode)
    directions = [UP, DOWN, LEFT, RIGHT, PORTAL]
    for direction in directions:
        neighbor = startNode.neighbors.get(direction)
        
        if (neighbor and neighbor not in visited and can_move_to(startNode, direction)):
            result = limited_dfs(neighbor, target, pellet_nodes, max_depth - 1, visited.copy())
            if result is not None:
                return [startNode] + result
    return None

