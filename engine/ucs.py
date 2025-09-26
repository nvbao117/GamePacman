from queue import PriorityQueue
from constants import *

def ucs(startNode, endNode, pellet_group):
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None

    if endNode is not None and endNode in pellet_nodes:
        return ucs_to_target(startNode, endNode)
    
    return ucs_to_nearest_pellet(startNode, pellet_nodes)

def ucs_to_target(startNode, targetNode):
    if startNode == targetNode:
        return [startNode]
    
    queue = PriorityQueue()
    queue.put((0, startNode))
    parent = {startNode: None}
    costs = {startNode: 0}
    
    while not queue.empty():
        cost, current_node = queue.get()
        
        if current_node == targetNode:
            return trace_path(parent, current_node)
        
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)
            
            if neighbor and can_move_to(current_node, direction):
                new_cost = cost + get_cost(current_node, neighbor, direction)
                
                if new_cost < costs.get(neighbor, float('inf')):
                    costs[neighbor] = new_cost
                    parent[neighbor] = current_node
                    queue.put((new_cost, neighbor))
    
    return None

def ucs_to_nearest_pellet(startNode, pellet_nodes):
    if startNode in pellet_nodes:
        return [startNode]
    
    queue = PriorityQueue()
    queue.put((0, startNode))
    parent = {startNode: None}
    costs = {startNode: 0}
    while not queue.empty():
        cost, current_node = queue.get()
        
        if current_node in pellet_nodes:
            return trace_path(parent, current_node)
        
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)
            
            if neighbor and can_move_to(current_node, direction):
                new_cost = cost + get_cost(current_node, neighbor, direction)
                
                if new_cost < costs.get(neighbor, float('inf')):
                    costs[neighbor] = new_cost
                    parent[neighbor] = current_node
                    queue.put((new_cost, neighbor))
    return None

def ucs_with_priority(startNode, endNode, pellet_group, priority_direction=None):
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None

    if endNode is not None and endNode in pellet_nodes:
        return ucs_to_target_with_priority(startNode, endNode, priority_direction)
    
    return ucs_to_nearest_pellet_with_priority(startNode, pellet_nodes, priority_direction)

def ucs_to_target_with_priority(startNode, targetNode, priority_direction=None):
    if startNode == targetNode:
        return [startNode]
    
    queue = PriorityQueue()
    queue.put((0, startNode))
    parent = {startNode: None}
    costs = {startNode: 0}
    
    while not queue.empty():
        cost, current_node = queue.get()
        
        if current_node == targetNode:
            return trace_path(parent, current_node)
        
        directions = get_prioritized_directions(priority_direction)
        
        for direction in directions:
            neighbor = current_node.neighbors.get(direction)
            
            if neighbor and can_move_to(current_node, direction):
                new_cost = cost + get_cost(current_node, neighbor, direction)
                
                if new_cost < costs.get(neighbor, float('inf')):
                    costs[neighbor] = new_cost
                    parent[neighbor] = current_node
                    queue.put((new_cost, neighbor))
    
    return None

def ucs_to_nearest_pellet_with_priority(startNode, pellet_nodes, priority_direction=None):
    if startNode in pellet_nodes:
        return [startNode]
    
    queue = PriorityQueue()
    queue.put((0, startNode))
    parent = {startNode: None}
    costs = {startNode: 0}
    
    while not queue.empty():
        cost, current_node = queue.get()
        
        if current_node in pellet_nodes:
            return trace_path(parent, current_node)
        
        directions = get_prioritized_directions(priority_direction)
        
        for direction in directions:
            neighbor = current_node.neighbors.get(direction)
            
            if neighbor and can_move_to(current_node, direction):
                new_cost = cost + get_cost(current_node, neighbor, direction)
                
                if new_cost < costs.get(neighbor, float('inf')):
                    costs[neighbor] = new_cost
                    parent[neighbor] = current_node
                    queue.put((new_cost, neighbor))
    
    return None

def get_cost(current_node, neighbor, direction):
    base_cost = 1
    
    if direction == PORTAL:
        return base_cost + 2
    
    # if hasattr(current_node, 'last_direction'):
    #     if current_node.last_direction == direction:
    #         return base_cost - 0.1 
    #     elif is_opposite_direction(current_node.last_direction, direction):
    #         return base_cost + 0.5
    
    return base_cost

def is_opposite_direction(dir1, dir2):
    opposites = {
        UP: DOWN,
        DOWN: UP,
        LEFT: RIGHT,
        RIGHT: LEFT
    }
    return opposites.get(dir1) == dir2

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
