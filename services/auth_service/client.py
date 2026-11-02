import httpx
from django.conf import settings


def get_user_info(profile_id, token):
    url = f"{settings.AUTH_SERVICE_URL}/user-info/{profile_id}/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        response = httpx.get(url, headers=headers, timeout=20)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Non-200 response from auth service: {response.status_code}")
    except httpx.RequestError as e:
        print(f"Error contacting auth service: {e}")
    except Exception as e:
        print(f"Unexpected error in get_user_info: {e}")
    return {}

def get_profile_info(token):
    url = f"{settings.AUTH_SERVICE_URL}/profile/"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    try:
        response = httpx.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
    except httpx.RequestError as e:
        #log the error here
        print(f"Error contacting auth service: {e}")
    return None
