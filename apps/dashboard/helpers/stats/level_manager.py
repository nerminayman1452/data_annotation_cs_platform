class LevelManager:
    """Manages user level progression and XP calculations"""
    
    BASE_XP_PER_LEVEL = 1000
    ACCURACY_THRESHOLD = 90
    
    @classmethod
    def calculate_level(cls, xp_points: int) -> int:
        """Calculate user level based on XP points"""
        return max(1, (xp_points // cls.BASE_XP_PER_LEVEL) + 1)
    
    @classmethod
    def calculate_xp_for_tasks(cls, task_count: int, accuracy: float, base_xp: int, accuracy_bonus: int) -> int:
        """Calculate XP points for completed tasks considering accuracy bonus"""
        total_xp = task_count * base_xp
        if accuracy > cls.ACCURACY_THRESHOLD:
            total_xp += task_count * accuracy_bonus
        return total_xp