#!/usr/bin/env python3

from galaxy.handlers.web import WebHandler


class DLPlanetHandler(WebHandler):
    def get(self):
        default_address = "https://github.com/Planetable/Planet/releases/download/release-0.14.1/Planet.zip"  # noqa: E501
        mc_key = "dl:planet:latest"
        mc_value = self.mc.get(mc_key)
        if mc_value is not None:
            self.redirect(mc_value)
        else:
            self.redirect(default_address)


class DLCroptopHandler(WebHandler):
    def get(self):
        default_address = "https://github.com/Planetable/Planet/releases/download/croptop-20230831-1/Croptop.zip"  # noqa: E501
        mc_key = "dl:croptop:latest"
        mc_value = self.mc.get(mc_key)
        if mc_value is not None:
            self.redirect(mc_value)
        else:
            self.redirect(default_address)


dl_handlers = [
    (r"/dl/planet/?$", DLPlanetHandler),
    (r"/dl/croptop/?$", DLCroptopHandler),
]
