import logging
import time
import requests
import jwt
from cryptography.x509 import load_pem_x509_certificate
from cryptography.hazmat.backends import default_backend
from django.contrib.auth import get_user_model
from rest_framework import exceptions
from ..models import Provider, UserAssociation, AccessToken, JsonWebKey
from .base import MultiproviderBaseAuthentication

logger = logging.getLogger(__name__)

UserModel = get_user_model()


class JWTAuthentication(MultiproviderBaseAuthentication):
    name = "jwt"

    def authenticate(self, request):
        # Extract token from HTTP Authorization header
        bearer_token = self.get_token(request)

        # Authenticate against the database where old access tokens were stored
        user, token = self.check_cache(bearer_token, self.jwt_idps.keys())
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

        try:
            jwt_header = jwt.get_unverified_header(bearer_token)
        except Exception as e:
            msg = "Error when decoding the JWT header: {}".format(e)
            raise exceptions.AuthenticationFailed(msg)

        try:
            jwt_payload = jwt.decode(bearer_token, verify=False)
        except Exception as e:
            msg = "Error when decoding the JWT token payload: {}".format(e)
            raise exceptions.AuthenticationFailed(msg)

        typ = jwt_header.get("typ")
        alg = jwt_header.get("alg")
        kid = jwt_header.get("kid")

        if typ != "JWT":
            msg = "Unsupported JWT token type"
            raise exceptions.AuthenticationFailed(msg)

        if alg != "RS256":
            msg = "Unsupported JWT token algorithm"
            raise exceptions.AuthenticationFailed(msg)

        iss = jwt_payload.get("iss")
        sub = jwt_payload.get("sub")
        aud = jwt_payload.get("aud")
        exp = jwt_payload.get("exp")
        nbf = jwt_payload.get("nbf")

        idp = self.jwt_idps.get(iss)
        if not idp:
            msg = "Prohibited JWT token issuer"
            raise exceptions.AuthenticationFailed(msg)

        if idp.get("aud") != aud:
            msg = "Invalid audience"
            raise exceptions.AuthenticationFailed(msg)

        if not sub:
            msg = "No sub claim in the JWT token"
            raise exceptions.AuthenticationFailed(msg)

        unix_time = int(time.time())
        # Check if the 'exp' (Expiration Time) claim applies
        if exp and int(exp) < unix_time:
            msg = "Token expired"
            raise exceptions.AuthenticationFailed(msg)

        # Check if the 'nbf' (Not Before) claim applies
        if nbf and int(nbf) > unix_time:
            msg = "Token is not valid yet"
            raise exceptions.AuthenticationFailed(msg)

        provider, _created = Provider.objects.get_or_create(iss=iss)

        # Try to get JWKS from the issuer server and update keys in the database
        try:
            resp = requests.get(iss + ".well-known/jwks.json")
            jwks = resp.json()

            for jwk in jwks.get("keys"):
                kid = jwk.get("kid")
                alg = jwk.get("alg")
                kty = jwk.get("kty")
                x5c = jwk.get("x5c")[0]
                key, _created = JsonWebKey.objects.update_or_create(
                    iss=provider,
                    kid=kid,
                    defaults={"alg": alg, "kty": kty, "x5c": x5c}
                )
        except Exception:
            logger.warn("Could not download JWKS from {}".format(iss))

        # Try to get a corresponding key from the database
        try:
            key = JsonWebKey.objects.get(kid=kid)
        except JsonWebKey.DoesNotExist:
            msg = "Could not obtain a corresponding JWK"
            raise exceptions.AuthenticationFailed(msg)

        # Verify the JWT token
        cert_str = "-----BEGIN CERTIFICATE-----\n" + key.x5c + "\n-----END CERTIFICATE-----"
        cert_obj = load_pem_x509_certificate(cert_str.encode(), default_backend())
        try:
            jwt.decode(bearer_token, cert_obj.public_key(),
                       audience=idp.get("aud"), algorithms=key.alg)
        except Exception as e:
            logger.debug("Error when verifying the JWT token: {}".format(e))
            raise exceptions.AuthenticationFailed(e)

        try:
            user_association = UserAssociation.objects.get(provider=provider, uid=sub)
            user = user_association.user
        except UserAssociation.DoesNotExist:
            user = UserModel.objects.create(
                    username=sub,
            )
            logger.debug("New user '{}' created".format(user.username))
            user_association = UserAssociation.objects.create(
                    user=user, uid=sub, provider=provider)
            AccessToken.objects.create(
                user_association=user_association, access_token=bearer_token, exp=exp)
            logger.debug("New access token (JWT) '{}' added to the database".format(bearer_token))

        return user, None
