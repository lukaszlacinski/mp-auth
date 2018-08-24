import logging
import time
from django.conf import settings
from rest_framework import exceptions
from rest_framework.authentication import get_authorization_header, BaseAuthentication
from ..models import AccessToken

logger = logging.getLogger(__name__)


class MultiproviderBaseAuthentication(BaseAuthentication):
    """
    The base class with methods that are common for all types of Identity Providers:

    All provider authentication classes should derive from this class instead of
    rest_framework.authentication.BaseAuthentication

    """

    def __init__(self):
        self.jwt_idps = settings.MULTIPROVIDER_AUTH.get("JWT")
        self.opaque_token_idps = settings.MULTIPROVIDER_AUTH.get("BearerTokens")

    def get_token(self, request):
        """Extract a bearer token from the HTTP header"""

        auth = get_authorization_header(request)
        if not auth:
            msg = "No authorization header."
            raise exceptions.AuthenticationFailed(msg)

        auth = auth.split()
        len_auth = len(auth)
        if len_auth == 0:
            msg = "Empty authorization header."
            raise exceptions.AuthenticationFailed(msg)
        elif len_auth == 1:
            msg = "Invalid bearer header."
            raise exceptions.AuthenticationFailed(msg)
        elif len_auth > 2:
            msg = "Invalid bearer header. Token string must not contain any spaces."
            raise exceptions.AuthenticationFailed(msg)
        elif auth[0].lower() != b'bearer':
            msg = "Invalid bearer header. Missing Bearer."
            raise exceptions.AuthenticationFailed(msg)

        return auth[1]

    def check_cache(self, access_token, providers):
        """Look for the access token cached in the database

        Parameters
        ----------
        access_token : str
            access token
        providers : str|list
             string or list of strings with providers specified
             in MULTIPROVIDER_AUTH dict in settings.py
        """
        if isinstance(providers, str):
            providers = [providers]

        try:
            access_token = AccessToken.objects.get(access_token=access_token)
            unix_time = int(time.time())
            if (access_token.exp >= unix_time and
                    access_token.user_association.provider.iss in providers):
                user = access_token.user_association.user
                return user, access_token
        except AccessToken.DoesNotExist:
            pass

        return None, None
