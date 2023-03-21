#!/usr/bin/env python3

import json

import pylibmc
import redis

class PinnableMixin(object):
    mc: pylibmc.Client
    r: redis.Redis