#!/usr/bin/env python3

from tornado.web import authenticated

from galaxy.handlers.web import WebHandler
from galaxy.tasks.pinnable import check_account, check_website, pin_website


class PinnableWebsitesHandler(WebHandler):
    @authenticated
    def get(self):
        self.values["theme_color"] = "#c5c5c5"
        self.values["websites"] = self.get_websites(self.current_user.id)
        self.finalize("pinnable/websites.html")


class PinnableWebsitesAddHandler(WebHandler):
    @authenticated
    def get(self):
        self.values["theme_color"] = "#c5c5c5"
        self.finalize("pinnable/websites_add.html")

    @authenticated
    def post(self):
        self.verify_website_name()
        if self.ok():
            self.create_website(self.values["website_name"])
            self.redirect("/websites")
        else:
            self.values["theme_color"] = "#c5c5c5"
            self.finalize("pinnable/websites_add.html")


class PinnableWebsitesPinHandler(WebHandler):
    @authenticated
    def get(self, website_id):
        self.q.enqueue(check_account, self.current_user.id)
        website = self.get_website_by_id(website_id)
        ipfs_path = website.ipfs_path
        if website and ipfs_path:
            self.write("pinning website: %s" % ipfs_path)
            self.q.enqueue(check_website, website.id)
            self.q.enqueue(pin_website, website.id)


pinnable_handlers = [
    (r"/websites/?$", PinnableWebsitesHandler),
    (r"/websites/add/?$", PinnableWebsitesAddHandler),
    (r"/websites/pin/([0-9]+)?$", PinnableWebsitesPinHandler),
]
