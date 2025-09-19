from queue import PriorityQueue
from config import *
from core.nodes import Node

def a_star(startNode, endNode, pellet_group):
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None

    if endNode is not None and endNode in pellet_nodes:
        return a_star_to_target(startNode, endNode)
    
    return a_star_to_nearest_pellet(startNode, pellet_nodes)

def a_star_to_target(startNode, targetNode):
    if startNode == targetNode:
        return [startNode]
    
    queue = PriorityQueue()
    queue.put((0, startNode))
    parent = {startNode: None}
    g_cost = {startNode: 0}
    f_cost = {startNode: heuristic(startNode, targetNode)}
    
    while not queue.empty():
        current_f, current_node = queue.get()
        
        if current_node == targetNode:
            return trace_path(parent, current_node)
        
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)
            
            if (neighbor and neighbor not in g_cost and 
                can_move_to(current_node, direction)):
                
                tentative_g = g_cost[current_node] + get_cost(current_node, neighbor, direction)
                
                if neighbor not in g_cost or tentative_g < g_cost[neighbor]:
                    g_cost[neighbor] = tentative_g
                    f_cost[neighbor] = tentative_g + heuristic(neighbor, targetNode)
                    queue.put((f_cost[neighbor], neighbor))
                    parent[neighbor] = current_node
    
    return None

def a_star_to_nearest_pellet(startNode, pellet_nodes):
    if startNode in pellet_nodes:
        return [startNode]
    
    queue = PriorityQueue()
    queue.put((0, startNode))
    parent = {startNode: None}
    g_cost = {startNode: 0}
    f_cost = {startNode: 0}
    
    while not queue.empty():
        current_f, current_node = queue.get()
        
        if current_node in pellet_nodes:
            return trace_path(parent, current_node)
        
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)
            
            if (neighbor and neighbor not in g_cost and 
                can_move_to(current_node, direction)):
                
                tentative_g = g_cost[current_node] + get_cost(current_node, neighbor, direction)
                
                if neighbor not in g_cost or tentative_g < g_cost[neighbor]:
                    g_cost[neighbor] = tentative_g
                    # Tìm pellet gần nhất từ neighbor
                    min_heuristic = min(heuristic(neighbor, pellet) for pellet in pellet_nodes)
                    f_cost[neighbor] = tentative_g + min_heuristic
                    queue.put((f_cost[neighbor], neighbor))
                    parent[neighbor] = current_node
    
    return None

def a_star_with_priority(startNode, endNode, pellet_group, priority_direction=None):
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None

    if endNode is not None and endNode in pellet_nodes:
        return a_star_to_target_with_priority(startNode, endNode, priority_direction)
    
    return a_star_to_nearest_pellet_with_priority(startNode, pellet_nodes, priority_direction)

def a_star_to_target_with_priority(startNode, targetNode, priority_direction=None):
    if startNode == targetNode:
        return [startNode]
    
    queue = PriorityQueue()
    queue.put((0, startNode))
    parent = {startNode: None}
    g_cost = {startNode: 0}
    f_cost = {startNode: heuristic(startNode, targetNode)}
    
    while not queue.empty():
        current_f, current_node = queue.get()
        
        if current_node == targetNode:
            return trace_path(parent, current_node)
        
        directions = get_prioritized_directions(priority_direction)
        
        for direction in directions:
            neighbor = current_node.neighbors.get(direction)
            
            if (neighbor and neighbor not in g_cost and 
                can_move_to(current_node, direction)):
                
                tentative_g = g_cost[current_node] + get_cost(current_node, neighbor, direction)
                
                if neighbor not in g_cost or tentative_g < g_cost[neighbor]:
                    g_cost[neighbor] = tentative_g
                    f_cost[neighbor] = tentative_g + heuristic(neighbor, targetNode)
                    queue.put((f_cost[neighbor], neighbor))
                    parent[neighbor] = current_node
    
    return None

def a_star_to_nearest_pellet_with_priority(startNode, pellet_nodes, priority_direction=None):
    if startNode in pellet_nodes:
        return [startNode]
    
    queue = PriorityQueue()
    queue.put((0, startNode))
    parent = {startNode: None}
    g_cost = {startNode: 0}
    f_cost = {startNode: 0}
    
    while not queue.empty():
        current_f, current_node = queue.get()
        
        if current_node in pellet_nodes:
            return trace_path(parent, current_node)
        
        directions = get_prioritized_directions(priority_direction)
        
        for direction in directions:
            neighbor = current_node.neighbors.get(direction)
            
            if (neighbor and neighbor not in g_cost and 
                can_move_to(current_node, direction)):
                
                tentative_g = g_cost[current_node] + get_cost(current_node, neighbor, direction)
                
                if neighbor not in g_cost or tentative_g < g_cost[neighbor]:
                    g_cost[neighbor] = tentative_g
                    min_heuristic = min(heuristic(neighbor, pellet) for pellet in pellet_nodes)
                    f_cost[neighbor] = tentative_g + min_heuristic
                    queue.put((f_cost[neighbor], neighbor))
                    parent[neighbor] = current_node
    
    return None

def heuristic(node1, node2):
    if node1 is None or node2 is None:
        return float('inf')
    
    dx = abs(node1.position.x - node2.position.x)
    dy = abs(node1.position.y - node2.position.y)
    return dx + dy

def get_cost(current_node, neighbor, direction):
    base_cost = 1
    
    if direction == PORTAL:
        return base_cost + 2
    
    return base_cost

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