#!/usr/bin/env python3

from galaxy.handlers.web import WebHandler


class SystemHomeHandler(WebHandler):
    def get(self):
        #self.values["theme_color"] = "#ffd659"
        self.values['theme_color'] = "#ffcc33"
        self.finalize("system/home.html")


class SystemPricingHandler(WebHandler):
    def get(self):
        #self.values["theme_color"] = "#a3b18a"
        self.values['theme_color'] = "#a0bd6c"
        self.finalize("system/pricing.html")


class SystemPlanetHandler(WebHandler):
    def get(self):
        #self.values["theme_color"] = "#c0c0c0"
        self.values["theme_color"] = "#c5c5c5"
        self.finalize("system/planet.html")


class System404Handler(WebHandler):
    def get(self, path):
        self.write(path)
        self.set_status(404)
        self.finalize("system/404.html")


system_handlers = [
    (r"/", SystemHomeHandler),
    (r"/pricing", SystemPricingHandler),
    (r"/planet", SystemPlanetHandler),
    (r"/(.*)$", System404Handler),
]
