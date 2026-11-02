"""
Plan Registry - Maps plan types to their models and source data builders.
Provides a centralized way to configure different plan types.
"""

from typing import Dict, Type, Tuple
from apps.tasks.helpers.source_data_builder import (
    TextSourceDataBuilder,
    ImageSourceDataBuilder,
)


class PlanRegistry:
    """Registry for all plan types and their configurations."""

    _registry: Dict[str, Tuple[Type, Type]] = {}

    @classmethod
    def register(cls, plan_type: str, plan_model: Type, source_data_builder: Type) -> None:
        """
        Register a plan type with its model and source data builder.

        Args:
            plan_type: Type identifier (e.g., 'text', 'image')
            plan_model: The Django model class for this plan type
            source_data_builder: The source data builder class for this plan type
        """
        cls._registry[plan_type] = (plan_model, source_data_builder)

    @classmethod
    def get(cls, plan_type: str) -> Tuple[Type, Type]:
        """
        Retrieve plan model and builder for a given plan type.

        Args:
            plan_type: Type identifier (e.g., 'text', 'image')

        Returns:
            Tuple of (plan_model, source_data_builder)

        Raises:
            ValueError: If plan_type is not registered
        """
        if plan_type not in cls._registry:
            available = ", ".join(cls._registry.keys())
            raise ValueError(
                f"Plan type '{plan_type}' not found in registry. "
                f"Available types: {available}"
            )
        return cls._registry[plan_type]

    @classmethod
    def get_available_types(cls) -> list:
        """Get list of available plan types."""
        return list(cls._registry.keys())

    @classmethod
    def is_registered(cls, plan_type: str) -> bool:
        """Check if a plan type is registered."""
        return plan_type in cls._registry


# Register default plan types
def register_default_plans():
    """Register all default plan types."""
    from apps.project_management.models import TextPlan, ImagePlan

    PlanRegistry.register("text", TextPlan, TextSourceDataBuilder)
    PlanRegistry.register("image", ImagePlan, ImageSourceDataBuilder)


# Auto-register default plans on import
register_default_plans()
