"""
Handles extracting and retrieving authenticated user profile data
from an auth gateway service using an external
authentication service client.
"""

from typing import Optional, Dict, Any
from services.auth_service.client import get_profile_info, get_user_info


class ProfileInfoHelper:
    """Encapsulates logic for extracting and fetching profile information."""

    @staticmethod
    def _extract_token(request) -> Optional[str]:
        """
        Extracts the Bearer token from the Authorization header.

        Returns:
            str or None: Token string if present, otherwise None.
        """
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return None
        return auth_header.split("Bearer ")[-1].strip()

    @classmethod
    def get_profile_id_from_request(cls, request) -> Optional[int]:
        """
        Returns the profile ID from the authenticated request.

        Uses `get_profile_info` to decode the token and extract the profile ID.
        """
        token = cls._extract_token(request)
        if not token:
            return None

        try:
            profile_data = get_profile_info(token)
            return profile_data.get("id")
        except Exception:
            return None

    @classmethod
    def get_profile_data_from_request(cls, request, profile_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Returns the full user data based on token and profile ID.

        Args:
            request: DRF request object.
            profile_id (int, optional): Specific profile ID, otherwise derived from token.
        """
        token = cls._extract_token(request)
        if not token:
            return None

        if not profile_id:
            profile_id = cls.get_profile_id(request)
            if not profile_id:
                return None

        try:
            return get_user_info(profile_id, token)
        except Exception:
            return None
