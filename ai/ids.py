from config import *


def ids(startNode, endNode, pellet_group, max_depth=2000):
    """Iterative Deepening Search to the nearest pellet or specified end node.

    Returns path list or None.
    """
    if not pellet_group or not pellet_group.pelletList:
        return None
    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList if pellet.node is not None}
    if not pellet_nodes:
        return None

    goal_nodes = pellet_nodes.copy()
    if endNode is not None and endNode in pellet_nodes:
        goal_nodes = {endNode}

    for depth_limit in range(1, max_depth + 1):
        found, parent, goal = _dls(startNode, goal_nodes, depth_limit)
        if found:
            return _trace_path(parent, goal)
    return None


def _dls(startNode, goal_nodes, depth_limit):
    stack = [(startNode, 0)]
    parent = {startNode: None}
    visited_at_depth = {startNode: 0}

    while stack:
        current_node, depth = stack.pop()
        if current_node in goal_nodes:
            return True, parent, current_node
        if depth >= depth_limit:
            continue

        for direction in [UP, LEFT, DOWN, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)
            if neighbor and (direction == PORTAL or PACMAN in current_node.access[direction]):
                nd = depth + 1
                if neighbor not in visited_at_depth or nd < visited_at_depth[neighbor]:
                    visited_at_depth[neighbor] = nd
                    parent[neighbor] = current_node
                    stack.append((neighbor, nd))
    return False, None, None


def _trace_path(parent, goalNode):
    path = []
    current = goalNode
    while current is not None:
        path.insert(0, current)
        current = parent[current]
    return path


