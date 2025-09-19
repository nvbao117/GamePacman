import heapq
from config import *


def ucs(startNode, endNode, pellet_group):
    """Uniform Cost Search using unit step costs between nodes.

    Returns path list or None. Prefers specified endNode if it's a pellet, else nearest pellet.
    """
    if not pellet_group or not pellet_group.pelletList:
        return None
    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList if pellet.node is not None}
    if not pellet_nodes:
        return None

    goal_nodes = pellet_nodes.copy()
    if endNode is not None and endNode in pellet_nodes:
        goal_nodes = {endNode}

    frontier = [(0, startNode)]
    parent = {startNode: None}
    cost_so_far = {startNode: 0}

    while frontier:
        cost, current = heapq.heappop(frontier)
        if current in goal_nodes:
            return _trace_path(parent, current)

        for direction in [UP, LEFT, DOWN, RIGHT, PORTAL]:
            neighbor = current.neighbors.get(direction)
            if neighbor and (direction == PORTAL or PACMAN in current.access[direction]):
                new_cost = cost + 1  # unit cost per edge
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    parent[neighbor] = current
                    heapq.heappush(frontier, (new_cost, neighbor))

    return None


def _trace_path(parent, goalNode):
    path = []
    current = goalNode
    while current is not None:
        path.insert(0, current)
        current = parent[current]
    return path


