class RewardCalculator:
    """Handles calculation of rewards (datcoins) for user contributions"""
    
    DEFAULT_COINS_PER_TASK = 5.0
    SPEED_BONUS_COINS = 2.0
    
    @classmethod
    def calculate_task_reward(cls, plan_config) -> float:
        """Calculate reward for a single task based on plan configuration"""
        try:
            if plan_config and hasattr(plan_config, 'reward_per_task'):
                return float(plan_config.reward_per_task)
        except (ValueError, TypeError):
            pass
        return cls.DEFAULT_COINS_PER_TASK
    
    @classmethod
    def calculate_speed_bonus(cls, early_completion_count: int) -> float:
        """Calculate bonus rewards for early task completions"""
        return early_completion_count * cls.SPEED_BONUS_COINS