class Heuristic:
    @staticmethod
    def get_heuristic_function(config):
        heuristic_name = "NONE"
    
        if hasattr(config, "get"):
            heuristic_name = config.get("algorithm_heuristic", "NONE")
        elif isinstance(config, dict):
            heuristic_name = config.get("algorithm_heuristic", "NONE")
        
        heuristic_name = heuristic_name.upper()
        if heuristic_name == "MANHATTAN":
            return Heuristic.manhattan
        elif heuristic_name == "EUCLIDEAN":
            return Heuristic.euclidean
        elif heuristic_name == "MAZEDISTANCE":
            return Heuristic.mazedistance     
        else:
            return Heuristic.none

    @staticmethod
    def none(node1, node2):
        """
        Heuristic mặc định: không sử dụng heuristic (trả về 0).
        """
        return 0

    @staticmethod
    def manhattan(node1, node2):
        return (abs(node1.position.x - node2.position.x) + abs(node1.position.y - node2.position.y)) / 16

    @staticmethod
    def euclidean(node1, node2):

        dx = (node1.position.x - node2.position.x) / 16
        dy = (node1.position.y - node2.position.y) / 16
        return (dx * dx + dy * dy) ** 0.5
    
    @staticmethod
    def mazedistance(node1, node2):
        """
        Maze distance heuristic - tính khoảng cách thực tế trong maze bằng BFS
        """
        from collections import deque
        visited = set()
        queue = deque([(node1, 0)])
        while queue:
            current, dist = queue.popleft()
            if current == node2:
                return dist
            visited.add(current)
            for neighbor in current.neighbors.values():
                if neighbor and neighbor not in visited:
                    queue.append((neighbor, dist + 1))
        return float('inf')