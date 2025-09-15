from collections import deque
from config import * 
from core.nodes import Node

def bfs( startNode, endNode, pellet_group):
    if not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList if pellet.node is not None}
    if not pellet_nodes:
        return None

    queue = deque([startNode])
    parent = {startNode: None}
    visited = {startNode}

    while queue:
        current_node = queue.popleft()

        if current_node == endNode:
            return trace_path(parent, current_node)

        for direction in [UP, DOWN, LEFT, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)

            if (neighbor and neighbor not in visited
                and (direction == PORTAL or PACMAN in current_node.access[direction])):
                visited.add(neighbor)
                parent[neighbor] = current_node
                queue.append(neighbor)

    return None
def trace_path(parent, goalNode):
    path = []
    current = goalNode
    while current is not None:
        path.insert(0, current)
        current = parent[current]
    for node in path :
        print(node.position,end = " ")
    print(" ")
    return path