# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class Provider(models.Model):
    iss = models.CharField(max_length=1024, unique=True)


class JsonWebKey(models.Model):
    iss = models.ForeignKey(Provider, on_delete=models.CASCADE)
    kid = models.CharField(max_length=256, unique=True)
    kty = models.CharField(max_length=256)
    alg = models.CharField(max_length=256)
    x5c = models.CharField(max_length=8192)


class UserAssociation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    uid = models.CharField(max_length=255, unique=True)
    provider = models.ForeignKey(Provider, on_delete=models.CASCADE)


class AccessToken(models.Model):
    user_association = models.ForeignKey(UserAssociation, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=8192)
    scope = models.CharField(max_length=1024)
    exp = models.IntegerField()


class AccessTokenAudience(models.Model):
    access_token = models.ForeignKey(AccessToken, on_delete=models.CASCADE)
    aud = models.CharField(max_length=1024)
