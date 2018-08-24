import logging
from rest_framework.exceptions import AuthenticationFailed
from .base import MultiproviderBaseAuthentication
from .globus import GlobusAuthentication
from .jwt import JWTAuthentication

logger = logging.getLogger(__name__)


class MultiproviderAuthentication(MultiproviderBaseAuthentication):

    def authenticate(self, request):
        """Authenticate the request against the database with cached access tokens
        received with previous successfully authenticated requests. If the requests
        contains a new access toke, introspect the token in a sequence by provider
        specific authentication classes.
        """

        bearer_token = self.get_token(request)
        user, token = self.check_cache(
                bearer_token,
                list(self.jwt_idps.keys()) + list(self.opaque_token_idps.keys()))
        if user:
            return user, token

        exception_list = []

        if self.jwt_idps:
            try:
                jwt_authentication = JWTAuthentication()
                user, token = jwt_authentication.introspect_token(bearer_token)
                return user, None
            except AuthenticationFailed as e:
                exception_list.append(e)

        if self.opaque_token_idps:
            if self.opaque_token_idps.get("globus"):
                try:
                    globus_authentication = GlobusAuthentication()
                    user, token = globus_authentication.introspect_token(bearer_token)
                    return user, None
                except AuthenticationFailed as e:
                    exception_list.append(e)

        msg = '. Or: '.join([str(ex) for ex in exception_list])
        raise AuthenticationFailed(msg)
