# Multiprovider Authentication

Multiprovider Authentication is an easy to setup authentication middleware with support for
[Django REST Framework][drf] and multiple OAuth2/OIDC Identity Providers that issue opaque
or JWT access tokens, e.g. [Auth0][auth0], [Globus][globus], etc.

## Rationale

Many authentication middleware packages have been writted for Django REST Framework with
support for OAuth2 opaque or JWT token. Most popular ones are listed with a short description
on [Django REST Framework - Authentication][drf_auth]. But all of them that support opaque tokens
require access to the Identity Provider database to verify the access tokens. Or they cannot be
stack up with other authentication classes to authenticate a bearer token against multiple
Identity Providers. The Multiprovider Authentication middleware fills up the gap. It supports all
Identity Providers that issue JWT tokens and [Globus][globus] that issues opaque access tokens. Support
for other Identity Providers can easily be added by creating a new backend in `mp_auth/backends`.
Each backend can be used separately as an Django REST Framework authentication class, or can be a part of
list of authentication class that Django REST Framework will go through to authenticate an HTTP request.
`mp_auth.backend.mp.MultiproviderAuthentication` is a special authentication class that calls all
authentication classes configured in `settings.py`.

## Setup

Install the Multiprovider Authentication middleware for Django REST Framework
```shell
pip install git+git://github.com/lukaszlacinski/mp_auth.git
```
and in `settings.py` set the following:
```python
INSTALLED_APPS [
    ...
    'MP_AUTH',
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'mp_auth.backends.mp.MultiproviderAuthentication',
    )
}

MULTIPROVIDER_AUTH = {
    "BearerTokens": {
        "globus": {
            "scope": [<scopes>],
            "aud": <audience>
        }
    },
    "JWT": {
        <issuer>": {
            "aud": <audience>
        }
    }
}

GLOBUS_CLIENT_ID = <OAuth2 client id>
GLOBUS_CLIENT_SECRET = <OAuth2 client secret>
```
Then any view can be protected by `JWTAuthentication` or `GlobusAuthentication`, or, if you want to
authenticate an HTTP request against both `JWTAuthentication` or `GlobusAuthentication`, by
 `MultiproviderAuthentication` class.
```
from mp_auth.backends.mp import MultiproviderAuthentication

class MyAPIView(APIView):
    authentication_classes = (MultiproviderAuthentication,)
    renderer_classes = (JSONRenderer,)

    def get(self, request, format=None):
        user = request.user
        return Response({"username": user.username})
```

[drf]: http://www.django-rest-framework.org/
[auth0]: https://auth0.com/
[globus]: https://globus.org/
[drf_auth]: http://www.django-rest-framework.org/api-guide/authentication/#third-party-packages

