# =============================================================================
# A_STAR.PY - THUẬT TOÁN A* CHO PAC-MAN AI
# =============================================================================
# File này chứa thuật toán A* (A-star) để tìm đường đi tối ưu
# cho Pac-Man đến pellet gần nhất hoặc mục tiêu cụ thể
# A* sử dụng heuristic để tìm đường đi ngắn nhất một cách hiệu quả

from queue import PriorityQueue
from constants import *
from objects.nodes import Node

def a_star(startNode, endNode, pellet_group):
    """
    Thuật toán A* tìm đường đi từ startNode đến pellet gần nhất hoặc endNode cụ thể
    
    A* (A-star):
    - Kết hợp BFS với heuristic function
    - f(n) = g(n) + h(n) với g(n) là cost thực tế, h(n) là heuristic
    - Đảm bảo tìm được đường đi tối ưu nếu heuristic admissible
    - Hiệu quả hơn BFS thuần túy
    
    Args:
        startNode: Node bắt đầu
        endNode: Node đích cụ thể (có thể None để tìm pellet gần nhất)
        pellet_group: Nhóm pellets còn lại trong game
    
    Returns:
        List các nodes tạo thành đường đi, hoặc None nếu không tìm thấy
    """
    # Kiểm tra có pellet nào không
    if not pellet_group or not pellet_group.pelletList:
        return None

    # Lấy danh sách các node có pellet
    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList 
                   if pellet.node is not None and pellet.visible}
    
    if not pellet_nodes:
        return None

    # Nếu có endNode cụ thể và nó có pellet, tìm đường đến đó
    if endNode is not None and endNode in pellet_nodes:
        return a_star_to_target(startNode, endNode)
    
    # Ngược lại, tìm đường đến pellet gần nhất
    return a_star_to_nearest_pellet(startNode, pellet_nodes)

def a_star_to_target(startNode, targetNode):
    """
    A* tìm đường đi đến target cụ thể
    
    Args:
        startNode: Node bắt đầu
        targetNode: Node đích
    
    Returns:
        List các nodes tạo thành đường đi, hoặc None nếu không tìm thấy
    """
    if startNode == targetNode:
        return [startNode]
    
    # Priority queue với f_cost làm priority
    queue = PriorityQueue()
    queue.put((0, startNode))
    parent = {startNode: None}      # Lưu parent để trace path
    g_cost = {startNode: 0}         # Cost thực tế từ start
    f_cost = {startNode: heuristic(startNode, targetNode)}  # f = g + h
    
    while not queue.empty():
        current_f, current_node = queue.get()
        
        # Tìm thấy target
        if current_node == targetNode:
            return trace_path(parent, current_node)
        
        # Duyệt tất cả neighbors
        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)
            
            if (neighbor and neighbor not in g_cost and 
                can_move_to(current_node, direction)):
                
                # Tính tentative g cost
                tentative_g = g_cost[current_node] + get_cost(current_node, neighbor, direction)
                
                # Cập nhật nếu tìm được đường tốt hơn
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
    """
    Heuristic function cho A* - Manhattan distance
    - Admissible: không bao giờ overestimate cost thực tế
    - Consistent: đảm bảo A* tìm được đường đi tối ưu
    
    Args:
        node1, node2: Hai nodes cần tính khoảng cách
    
    Returns:
        Manhattan distance giữa hai nodes
    """
    if node1 is None or node2 is None:
        return float('inf')
    
    # Manhattan distance: |x1-x2| + |y1-y2|
    dx = abs(node1.position.x - node2.position.x)
    dy = abs(node1.position.y - node2.position.y)
    return dx + dy

def get_cost(current_node, neighbor, direction):
    """
    Tính cost di chuyển từ current_node đến neighbor
    
    Args:
        current_node: Node hiện tại
        neighbor: Node kế tiếp
        direction: Hướng di chuyển
    
    Returns:
        Cost di chuyển (số nguyên)
    """
    base_cost = 1
    
    # Portal có cost cao hơn để ưu tiên đường đi bình thường
    if direction == PORTAL:
        return base_cost + 2
    
    return base_cost

def can_move_to(current_node, direction):
    """
    Kiểm tra xem có thể di chuyển theo hướng direction từ current_node không
    
    Args:
        current_node: Node hiện tại
        direction: Hướng di chuyển
    
    Returns:
        True nếu có thể di chuyển, False nếu không
    """
    if direction == PORTAL:
        return True  # Portal luôn có thể sử dụng
    else:
        return PACMAN in current_node.access[direction]

def trace_path(parent, goalNode):
    """
    Trace đường đi từ goal node ngược về start node
    
    Args:
        parent: Dictionary lưu parent của mỗi node
        goalNode: Node đích
    
    Returns:
        List các nodes tạo thành đường đi từ start đến goal
    """
    path = []
    current = goalNode
    while current is not None:
        path.insert(0, current)  # Thêm vào đầu để có thứ tự đúng
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