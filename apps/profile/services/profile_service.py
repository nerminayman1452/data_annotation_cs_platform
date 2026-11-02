import logging
from ..models.profile import Profile, Role
from services.auth_service.client import get_user_info, get_profile_info

logger = logging.getLogger(__name__)

class ProfileSyncService:
    def __init__(self, user, token):
        self.user = user
        self.token = token

    def sync(self):
        """
        Orchestrates fetching data and updating the local Profile model.
        """
        try:

            # 1. Fetch extended profile data (optional, fallback to empty)
            ext_profile_data = get_profile_info(self.token) or {}

            # 2. Fetch data from Auth Service
            user_data = get_user_info(ext_profile_data.get('id'), self.token)
            
            # If we can't get basic user data, we likely can't create a valid profile
            if not user_data:
                logger.warning(f"Could not fetch user data for {self.user.id}, aborting sync.")
                return None

            # 3. Determine Role
            role = self._determine_role(user_data.get('roles', []))

            # 4. Update or Create local Profile
            profile, created = Profile.objects.update_or_create(
                user_id=self.user.id,
                defaults={
                    'profile_auth_id': user_data.get('id', ext_profile_data.get('id', '')),
                    'email': user_data.get('user', {}).get('email', self.user.email),
                    'first_name': ext_profile_data.get('first_name', user_data.get('first_name', '')),
                    'last_name': ext_profile_data.get('last_name', user_data.get('last_name', '')),
                    'role': role
                }
            )
            logger.info(f"{'Created' if created else 'Updated'} profile for user {self.user.id}")
            return profile

        except Exception as e:
            logger.error(f"Error syncing profile for user {self.user.id}: {e}", exc_info=True)
            return None

    def _determine_role(self, roles_list):
        """Maps Auth Service roles to local Role choices."""
        role_map = {
            'admin': Role.MANAGER,
            'manager': Role.MANAGER,
            'reviewer': Role.REVIEWER,
            'annotator': Role.ANNOTATOR
        }
        
        for r in roles_list:
            r_lower = str(r).lower()
            if r_lower in role_map:
                return role_map[r_lower]
        return Role.ANNOTATOR

def get_or_sync_profile(user, token):
    """
    Checks if profile exists locally. If not, triggers synchronization.
    """
    # 1. Check local DB (Fast)
    try:
        return Profile.objects.get(user_id=user.id)
    except Profile.DoesNotExist:
        # 2. Not found locally, Sync from Auth Service (Slow)
        logger.info(f"Profile not found locally for {user.id}. Syncing...")
        service = ProfileSyncService(user, token)
        return service.sync()