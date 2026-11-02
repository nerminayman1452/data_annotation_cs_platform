from dataclasses import dataclass

@dataclass
class UserStats:
    """Container for user's gamification stats"""
    xp_points: int = 0
    datcoins: float = 0.0
    level: int = 1
    accuracy: float = 0.0
    # level_progress: float = 0.0  # percentage progress towards next level

    all_tasks: int = 0
    all_submitted: int = 0
    all_approved: int = 0
    all_rejected: int = 0

    @property
    def next_level_xp(self) -> int:
        """XP needed for next level, using a simple progression"""
        return self.level * 1000  # each level needs level*1000 XP

    @property
    def level_progress(self) -> float:
        """Progress towards next level as percentage"""
        next_xp = self.next_level_xp
        current_level_xp = (self.level - 1) * 1000
        level_xp = self.xp_points - current_level_xp
        return min(100.0, (level_xp / (next_xp - current_level_xp)) * 100)