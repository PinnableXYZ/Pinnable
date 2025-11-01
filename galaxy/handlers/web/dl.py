#!/usr/bin/env python3

from galaxy.handlers.web import APIHandler
from galaxy.tasks.dl import check_update


class DLPlanetHandler(APIHandler):
    def get(self):
        default_address = "https://opensource.planetable.xyz/planet/release-0.20.2/Planet.zip"  # noqa: E501
        mc_key = "dl:planet:latest:link"
        mc_value = self.mc.get(mc_key)
        if mc_value is not None:
            self.redirect(mc_value)
        else:
            check_update(
                "planet", "https://opensource.planetable.xyz/planet/appcast.xml"
            )  # noqa: E501
            self.redirect(default_address)


class DLPlanetInsiderHandler(APIHandler):
    def get(self):
        default_address = "https://opensource.planetable.xyz/planet-insider/insider-20250821-1/Planet-Insider.zip"  # noqa: E501
        mc_key = "dl:planet-insider:latest:link"
        mc_value = self.mc.get(mc_key)
        if mc_value is not None:
            self.redirect(mc_value)
        else:
            check_update(
                "planet-insider",
                "https://opensource.planetable.xyz/planet-insider/appcast.xml",
            )  # noqa: E501
            self.redirect(default_address)


class DLCroptopHandler(APIHandler):
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
    (r"/dl/insider/?$", DLPlanetInsiderHandler),
    (r"/dl/croptop/?$", DLCroptopHandler),
]
