# =============================================================================
# STATS_LOGGER.PY - HỆ THỐNG GHI LOG THỐNG KÊ GAME
# =============================================================================
# File này chứa StatsLogger - ghi thống kê game vào CSV sau mỗi lần chơi
# Sử dụng để phân tích performance và so sánh các thuật toán

import os
import csv
import datetime


class StatsLogger:
    """
    StatsLogger - Ghi log thống kê game vào file CSV
    
    Chức năng:
    - Ghi thống kê sau mỗi ván game (khi game over hoặc win)
    - Lưu thông tin: thời gian, thuật toán, heuristic, điểm, steps, pellets, etc.
    - Tự động tạo thư mục và file CSV nếu chưa tồn tại
    - Thêm header nếu file mới
    """
    
    CSV_PATH = os.path.join("stats", "game_stats.csv")
    
    HEADERS = [
        "timestamp",           # Thời điểm chơi (ISO format)
        "time_formatted",      # Thời gian chơi (MM:SS)
        "duration_sec",        # Thời lượng (giây)
        "algorithm",           # Thuật toán sử dụng
        "heuristic",           # Heuristic sử dụng
        "ai_mode",             # ONLINE/OFFLINE
        "score",               # Điểm số
        "total_steps",         # Tổng số bước
        "ai_steps",            # Số bước AI
        "player_steps",        # Số bước Player
        "pellets_total",       # Tổng số pellets
        "pellets_eaten",       # Số pellets đã ăn
        "pellets_remaining",   # Số pellets còn lại
        "level_reached",       # Level đạt được
        "few_pellets_mode",    # Chế độ few pellets (True/False)
        "few_pellets_count",   # Số pellets trong chế độ few
        "ghost_mode",          # Chế độ ghost (True/False)
        "result",              # Kết quả (GAME_OVER, WIN, QUIT)
    ]
    
    @classmethod
    def log(cls, stats: dict):
        """
        Ghi thống kê vào file CSV
        
        Args:
            stats: Dictionary chứa thống kê game
        """
        try:
            # Tạo thư mục stats nếu chưa tồn tại
            os.makedirs(os.path.dirname(cls.CSV_PATH), exist_ok=True)
            
            # Kiểm tra xem file có tồn tại và có dữ liệu không
            is_new_file = not os.path.exists(cls.CSV_PATH) or os.path.getsize(cls.CSV_PATH) == 0
            
            # Mở file ở chế độ append
            with open(cls.CSV_PATH, "a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=cls.HEADERS)
                
                # Ghi header nếu file mới
                if is_new_file:
                    writer.writeheader()
                
                # Chuẩn bị row data
                row = {key: stats.get(key, "") for key in cls.HEADERS}
                
                # Ghi row
                writer.writerow(row)
                
        except Exception as e:
            # Silent fail - không làm crash game
            print(f"Warning: Failed to log stats: {e}")
    
    @classmethod
    def load_recent(cls, max_rows=20):
        """
        Đọc các thống kê gần nhất từ CSV
        
        Args:
            max_rows: Số lượng rows tối đa để đọc
            
        Returns:
            List of dictionaries chứa thống kê
        """
        rows = []
        
        if not os.path.exists(cls.CSV_PATH):
            return rows
        
        try:
            with open(cls.CSV_PATH, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                all_rows = list(reader)
                # Lấy max_rows rows cuối cùng (mới nhất)
                rows = all_rows[-max_rows:] if len(all_rows) > max_rows else all_rows
        except Exception as e:
            print(f"Warning: Failed to load stats: {e}")
        
        return rows
    
    @classmethod
    def get_stats_summary(cls):
        """
        Lấy tóm tắt thống kê từ tất cả games với phân tích chi tiết
        
        Returns:
            Dictionary chứa thống kê tổng hợp và phân tích
        """
        rows = cls.load_recent(max_rows=1000)  # Load nhiều hơn để tính toán
        
        if not rows:
            return {
                "total_games": 0,
                "total_score": 0,
                "avg_score": 0,
                "total_steps": 0,
                "avg_steps": 0,
                "algorithms": {},
                "heuristics": {},
                "algorithm_performance": {},
                "heuristic_performance": {},
                "time_trends": [],
                "score_distribution": [],
                "efficiency_metrics": {},
            }
        
        # Tính toán thống kê cơ bản
        total_score = sum(int(r.get("score", 0) or 0) for r in rows)
        total_steps = sum(int(r.get("total_steps", 0) or 0) for r in rows)
        
        # Đếm algorithms và heuristics
        algorithms = {}
        heuristics = {}
        for r in rows:
            algo = r.get("algorithm", "UNKNOWN")
            heur = r.get("heuristic", "NONE")
            algorithms[algo] = algorithms.get(algo, 0) + 1
            heuristics[heur] = heuristics.get(heur, 0) + 1
        
        # Phân tích performance theo algorithm
        algorithm_performance = cls._analyze_algorithm_performance(rows)
        
        # Phân tích performance theo heuristic
        heuristic_performance = cls._analyze_heuristic_performance(rows)
        
        # Time trends (10 games gần nhất)
        time_trends = cls._get_time_trends(rows[-10:])
        
        # Score distribution
        score_distribution = cls._get_score_distribution(rows)
        
        # Efficiency metrics
        efficiency_metrics = cls._calculate_efficiency_metrics(rows)
        
        return {
            "total_games": len(rows),
            "total_score": total_score,
            "avg_score": total_score // len(rows) if rows else 0,
            "total_steps": total_steps,
            "avg_steps": total_steps // len(rows) if rows else 0,
            "algorithms": algorithms,
            "heuristics": heuristics,
            "algorithm_performance": algorithm_performance,
            "heuristic_performance": heuristic_performance,
            "time_trends": time_trends,
            "score_distribution": score_distribution,
            "efficiency_metrics": efficiency_metrics,
        }
    
    @classmethod
    def _analyze_algorithm_performance(cls, rows):
        """Phân tích performance của từng algorithm"""
        algo_stats = {}
        
        for row in rows:
            algo = row.get("algorithm", "UNKNOWN")
            if algo not in algo_stats:
                algo_stats[algo] = {
                    "count": 0,
                    "scores": [],
                    "steps": [],
                    "times": [],
                    "win_rate": 0,
                }
            
            algo_stats[algo]["count"] += 1
            algo_stats[algo]["scores"].append(int(row.get("score", 0) or 0))
            algo_stats[algo]["steps"].append(int(row.get("total_steps", 0) or 0))
            algo_stats[algo]["times"].append(int(row.get("duration_sec", 0) or 0))
            
            if "COMPLETE" in row.get("result", ""):
                algo_stats[algo]["win_rate"] += 1
        
        # Tính toán metrics
        for algo, stats in algo_stats.items():
            if stats["count"] > 0:
                stats["avg_score"] = sum(stats["scores"]) // stats["count"]
                stats["avg_steps"] = sum(stats["steps"]) // stats["count"]
                stats["avg_time"] = sum(stats["times"]) // stats["count"]
                stats["win_rate"] = (stats["win_rate"] / stats["count"]) * 100
                stats["max_score"] = max(stats["scores"])
                stats["min_score"] = min(stats["scores"])
                # Efficiency = score per step
                stats["efficiency"] = stats["avg_score"] / max(1, stats["avg_steps"])
        
        return algo_stats
    
    @classmethod
    def _analyze_heuristic_performance(cls, rows):
        """Phân tích performance của từng heuristic"""
        heur_stats = {}
        
        for row in rows:
            heur = row.get("heuristic", "NONE")
            if heur not in heur_stats:
                heur_stats[heur] = {
                    "count": 0,
                    "scores": [],
                    "steps": [],
                    "algorithms": {},
                }
            
            heur_stats[heur]["count"] += 1
            heur_stats[heur]["scores"].append(int(row.get("score", 0) or 0))
            heur_stats[heur]["steps"].append(int(row.get("total_steps", 0) or 0))
            
            algo = row.get("algorithm", "UNKNOWN")
            if algo not in heur_stats[heur]["algorithms"]:
                heur_stats[heur]["algorithms"][algo] = 0
            heur_stats[heur]["algorithms"][algo] += 1
        
        # Tính toán metrics
        for heur, stats in heur_stats.items():
            if stats["count"] > 0:
                stats["avg_score"] = sum(stats["scores"]) // stats["count"]
                stats["avg_steps"] = sum(stats["steps"]) // stats["count"]
                stats["max_score"] = max(stats["scores"])
                stats["min_score"] = min(stats["scores"])
                stats["efficiency"] = stats["avg_score"] / max(1, stats["avg_steps"])
        
        return heur_stats
    
    @classmethod
    def _get_time_trends(cls, recent_rows):
        """Lấy xu hướng thời gian của 10 games gần nhất"""
        trends = []
        for i, row in enumerate(recent_rows):
            trends.append({
                "game_num": i + 1,
                "score": int(row.get("score", 0) or 0),
                "steps": int(row.get("total_steps", 0) or 0),
                "time": int(row.get("duration_sec", 0) or 0),
                "algorithm": row.get("algorithm", "UNKNOWN"),
                "result": row.get("result", "UNKNOWN"),
            })
        return trends
    
    @classmethod
    def _get_score_distribution(cls, rows):
        """Phân phối điểm số theo ranges"""
        scores = [int(r.get("score", 0) or 0) for r in rows]
        if not scores:
            return []
        
        max_score = max(scores)
        ranges = [
            (0, 200, "0-200"),
            (200, 400, "200-400"),
            (400, 600, "400-600"),
            (600, 800, "600-800"),
            (800, 1000, "800-1000"),
            (1000, float('inf'), "1000+"),
        ]
        
        distribution = []
        for min_val, max_val, label in ranges:
            count = sum(1 for s in scores if min_val <= s < max_val)
            percentage = (count / len(scores)) * 100 if scores else 0
            distribution.append({
                "range": label,
                "count": count,
                "percentage": percentage,
            })
        
        return distribution
    
    @classmethod
    def _calculate_efficiency_metrics(cls, rows):
        """Tính toán các metrics hiệu quả"""
        if not rows:
            return {}
        
        scores = [int(r.get("score", 0) or 0) for r in rows]
        steps = [int(r.get("total_steps", 0) or 0) for r in rows]
        times = [int(r.get("duration_sec", 0) or 0) for r in rows]
        
        # Best performance
        best_score_idx = scores.index(max(scores)) if scores else 0
        best_game = rows[best_score_idx] if rows else {}
        
        # Worst performance
        worst_score_idx = scores.index(min(scores)) if scores else 0
        worst_game = rows[worst_score_idx] if rows else {}
        
        # Consistency (standard deviation)
        avg_score = sum(scores) / len(scores) if scores else 0
        score_variance = sum((s - avg_score) ** 2 for s in scores) / len(scores) if scores else 0
        score_std = score_variance ** 0.5
        
        return {
            "best_score": max(scores) if scores else 0,
            "worst_score": min(scores) if scores else 0,
            "score_consistency": 100 - (score_std / max(1, avg_score)) * 100,
            "best_game": {
                "score": best_game.get("score", 0),
                "algorithm": best_game.get("algorithm", "UNKNOWN"),
                "heuristic": best_game.get("heuristic", "NONE"),
            },
            "worst_game": {
                "score": worst_game.get("score", 0),
                "algorithm": worst_game.get("algorithm", "UNKNOWN"),
                "heuristic": worst_game.get("heuristic", "NONE"),
            },
            "avg_efficiency": sum(scores) / max(1, sum(steps)) if steps else 0,
        }

