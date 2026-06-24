import requests

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from misago.users.models import User as MisagoUser

User = get_user_model()

class VerpriseAuthBackend(ModelBackend):
    def authenticate(self, request, username= None, password= None, **kwargs):

        # Call the web layer API
        api_url = "http://127.0.0.1:3000/api"
        params = {
            "gamepass": "coolpass",
            "keycode": 11,
            "username": username,
            "password": password,
        }

        try:
            response = requests.get(api_url, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()

        except (requests.RequestException, ValueError) as e:
            # The API call failed here, so authentication also fails
            return None

        if not data.get("success", False):
            return None

        # Login was successful from the API, now need to find or create the user in Misago
        try:
            user = MisagoUser.objects.get_by_natural_key(username)

        except MisagoUser.DoesNotExist:
            # Misago user was not found, create a new one.

            user = MisagoUser.objects.create_user(
                username=username,
                email=None, # Set this to None because we do not want to store this # TODO Is this a security risk?
                password=None, # Set this to None because we do not want to store this
            )

            user.is_active = True
            user.save()

            # TODO Signal here

            pass

        return user

    def get_user(self, user_id):
        try:
            return MisagoUser.objects.get(pk=user_id)
        except MisagoUser.DoesNotExist:
            return None