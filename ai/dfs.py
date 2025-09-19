from config import *


def dfs(startNode, endNode, pellet_group):
    """Depth-first search tailored for Pacman grid.

    - Respects tile access constraints
    - Avoids immediately returning to parent within expansion (reduces ping-pong paths)
    - If endNode is valid pellet, prefer it; otherwise stop at first pellet reached
    Returns a node path list or None.
    """
    if not pellet_group or not pellet_group.pelletList:
        return None

    pellet_nodes = {pellet.node for pellet in pellet_group.pelletList if pellet.node is not None}
    if not pellet_nodes:
        return None

    goal_nodes = pellet_nodes.copy()
    goal_hint = None
    if endNode is not None and endNode in pellet_nodes:
        goal_nodes = {endNode}
        goal_hint = endNode

    stack = [(startNode, None)]  # (node, parent)
    parent = {startNode: None}
    visited = {startNode}

    while stack:
        current_node, from_node = stack.pop()
        if current_node in goal_nodes:
            return _trace_path(parent, current_node)

        # Build neighbors list with access filtering and avoid immediate parent
        neighbors = []
        for direction in [UP, LEFT, DOWN, RIGHT, PORTAL]:
            neighbor = current_node.neighbors.get(direction)
            if not neighbor or neighbor in visited:
                continue
            if direction != PORTAL and PACMAN not in current_node.access[direction]:
                continue
            if from_node is not None and neighbor is from_node:
                continue
            neighbors.append(neighbor)

        # If we have a goal hint, bias DFS to move closer to it to avoid edge ping-pong
        if goal_hint is not None:
            gx, gy = goal_hint.position.x, goal_hint.position.y
            neighbors.sort(key=lambda n: abs(n.position.x - gx) + abs(n.position.y - gy))

        for neighbor in neighbors:
            visited.add(neighbor)
            parent[neighbor] = current_node
            stack.append((neighbor, current_node))

    return None


def _trace_path(parent, goalNode):
    path = []
    current = goalNode
    while current is not None:
        path.insert(0, current)
        current = parent[current]
    return path


