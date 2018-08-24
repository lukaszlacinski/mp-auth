import logging
import time
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import exceptions
from ..models import Provider, UserAssociation, AccessToken
from .base import MultiproviderBaseAuthentication

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class GlobusAuthentication(MultiproviderBaseAuthentication):
    name = "globus"
    INTROSPECTION_URL = "https://auth.globus.org/v2/oauth2/token/introspect"
    DEPENDENT_TOKEN_URL = "https://auth.globus.org/v2/oauth2/token"

    def authenticate(self, request):
        # Extract a token from HTTP Authorization header
        bearer_token = self.get_token(request)

        # Authenticate against the database where access tokens are cached
        user, token = self.check_cache(bearer_token, self.__class__.name)
        if user:
            logger.info("{} successfully authenticated".format(user.username))
            return user, token

        # Introspect the token
        user, token = self.introspect_token(bearer_token)
        logger.info("{} successfully authenticated".format(user.username))
        return user, token

    def introspect_token(self, bearer_token):
        """
        Introspect the token and, if the token is valid:
        1) store the token with user information in the database
        2) associate the token with an existing user or create a user
           if it does not exist
        """

        resp = requests.post(
                GlobusAuthentication.INTROSPECTION_URL,
                data={"token": bearer_token},
                auth=(settings.GLOBUS_CLIENT_ID, settings.GLOBUS_CLIENT_SECRET)
        )

        try:
            content = resp.json()
        except Exception as e:
            logger.warn("Error when introspecting a bearer token: {}".format(e))

        logger.debug("Introspection response: {}".format(content))

        username = content.get("username")
        active = content.get("active")
        sub = content.get("sub")
        aud = content.get("aud")
        email = content.get("email")
        scope = content.get("scope")
        exp = content.get("exp")
        nbf = content.get("nbf")
        name = content.get("name")

        # Check if the token is active
        if not active:
            msg = "Token not active"
            raise exceptions.AuthenticationFailed(msg)

        unix_time = int(time.time())
        # Check if the 'exp' (Expiration Time) claim applies
        if exp and int(exp) < unix_time:
            msg = "Token expired"
            raise exceptions.AuthenticationFailed(msg)

        # Check if the 'nbf' (Not Before) claim applies
        if nbf and int(nbf) > unix_time:
            msg = "Token cannot be used before {}".format(nbf)
            raise exceptions.AuthenticationFailed(msg)

        # Check if the 'aud' (Audience) claim applies
        if aud and not self.opaque_token_idps.get("globus").get("aud") in aud:
            msg = "Wrong audience of the token"
            raise exceptions.AuthenticationFailed(msg)

        # Check if the 'scope' (Scope) claim applies
        if scope and self.opaque_token_idps.get("globus").get("scope") in scope.split():
            msg = "Wrong scope of the token"
            raise exceptions.AuthenticationFailed(msg)

        if not sub:
            msg = "Invalid introspection response"
            raise exceptions.AuthenticationFailed(msg)

        provider, _created = Provider.objects.get_or_create(iss="globus")

        try:
            user_association = UserAssociation.objects.get(provider=provider, uid=sub)
            user = user_association.user
        except UserAssociation.DoesNotExist:
            fullname, firstname, lastname = self.get_user_names(name)
            user = UserModel.objects.create(
                    first_name=firstname,
                    last_name=lastname,
                    email=email,
                    username=username,
            )
            logger.debug("New user '{}' created".format(user.username))
            user_association = UserAssociation.objects.create(
                    user=user, uid=sub, provider=provider)
            AccessToken.objects.create(
                user_association=user_association, access_token=bearer_token, scope=scope, exp=exp)
            logger.debug("New access token (Globus) {} added to the database".format(bearer_token))

        return user, None

    def get_user_names(self, fullname="", first_name="", last_name=''):
        # Avoid None values
        fullname = fullname or ""
        first_name = first_name or ""
        last_name = last_name or ""
        if fullname and not (first_name or last_name):
            try:
                first_name, last_name = fullname.split(" ", 1)
            except ValueError:
                first_name = first_name or fullname or ""
                last_name = last_name or ""
        fullname = fullname or ' '.join((first_name, last_name))
        return fullname.strip(), first_name.strip(), last_name.strip()
