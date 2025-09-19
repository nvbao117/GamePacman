from config import *
from core.nodes import Node
def iterative_deepening_dfs(startNode, endNode, pellet_group, max_depth=50):
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

    for depth in range(1, max_depth + 1):
        result = depth_limited_dfs(startNode, target, pellet_nodes, depth)
        if result is not None:
            return result
    
    return None

def depth_limited_dfs(startNode, target, pellet_nodes, max_depth, visited=None):
    if visited is None:
        visited = set()
    
    if startNode in visited:
        return None
    
    if startNode in pellet_nodes and (target is None or startNode == target):
        return [startNode]
    
    if max_depth <= 0:
        return None
    
    visited.add(startNode)
    
    for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
        neighbor = startNode.neighbors.get(direction)
        
        if (neighbor and neighbor not in visited and can_move_to(startNode, direction)):
            result = depth_limited_dfs(neighbor, target, pellet_nodes, max_depth - 1, visited.copy())
            if result is not None:
                return [startNode] + result
    
    return None

def can_move_to(current_node, direction):
    if direction == PORTAL:
        return True  
    else:
        return PACMAN in current_node.access[direction]