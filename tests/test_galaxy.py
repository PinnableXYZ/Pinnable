#!/usr/bin/env python3

from tornado.testing import AsyncHTTPTestCase

import ivalice


class TestGalaxyApp(AsyncHTTPTestCase):
    def get_app(self):
        return ivalice.Application()

    def test_homepage(self):
        response = self.fetch("/")
        assert response.code == 200
