#!/usr/bin/env python3

from galaxy.handlers.web import WebHandler


class PinnableNamesHandler(WebHandler):
    def get(self):
        self.finalize("pinnable/names.html")



pinnable_handlers = [
    (r"/names$", PinnableNamesHandler),
]
