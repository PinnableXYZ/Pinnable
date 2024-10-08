#!/usr/bin/env python3

from galaxy.handlers.web import WebHandler
from galaxy.tasks.dl import check_update


class DLPlanetHandler(WebHandler):
    def get(self):
        default_address = "https://github.com/Planetable/Planet/releases/download/release-0.18.3/Planet.zip"  # noqa: E501
        mc_key = "dl:planet:latest:link"
        mc_value = self.mc.get(mc_key)
        if mc_value is not None:
            self.redirect(mc_value)
        else:
            check_update(
                "planet", "https://opensource.planetable.xyz/planet/appcast.xml"
            )  # noqa: E501
            self.redirect(default_address)


class DLCroptopHandler(WebHandler):
    def get(self):
        default_address = "https://opensource.planetable.xyz/croptop/croptop-20240711-1/Croptop.zip"  # noqa: E501
        mc_key = "dl:croptop:latest:link"
        mc_value = self.mc.get(mc_key)
        if mc_value is not None:
            self.redirect(mc_value)
        else:
            check_update(
                "croptop", "https://opensource.planetable.xyz/croptop/appcast.xml"
            )  # noqa: E501
            self.redirect(default_address)


dl_handlers = [
    (r"/dl/planet/?$", DLPlanetHandler),
    (r"/dl/croptop/?$", DLCroptopHandler),
]
