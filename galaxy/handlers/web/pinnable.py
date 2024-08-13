#!/usr/bin/env python3

import json

from tornado import gen
from tornado.iostream import StreamClosedError
from tornado.web import authenticated

from galaxy.handlers.web import WebHandler
from galaxy.tasks.pinnable import check_account, check_website, pin_website


class PinnableWebsitesHandler(WebHandler):
    @authenticated
    def get(self):
        self.values["theme_color"] = "#c5c5c5"
        order_options = ["name", "created", "pinned", "size"]
        order = "name"
        if "o" in self.request.arguments:
            order = self.get_argument("o")
            if order not in order_options:
                order = "name"
        self.values["order_options"] = order_options
        self.values["order"] = order
        self.values["websites"] = self.get_websites(self.current_user.id, order)
        self.finalize("pinnable/websites.html")


class PinnableWebsitesAddHandler(WebHandler):
    @authenticated
    def get(self):
        if not self.current_user.can_add_more:
            self.values["add_disabled"] = True
        else:
            self.values["add_disabled"] = False
        self.values["theme_color"] = "#c5c5c5"
        self.finalize("pinnable/websites_add.html")

    @authenticated
    def post(self):
        if not self.current_user.can_add_more:
            self.redirect("/websites/add")
            return
        self.verify_website_name()
        if self.ok():
            website = self.create_website(self.values["website_name"])
            self.q.enqueue(check_website, website.id)
            self.redirect(f"/websites/{website.id}")
        else:
            self.values["theme_color"] = "#c5c5c5"
            self.finalize("pinnable/websites_add.html")


class PinnableWebsitesInfoHandler(WebHandler):
    @authenticated
    def get(self, website_id):
        website = self.get_website_by_id(website_id)
        if website and website.account_id == self.current_user.id:
            if website.seconds_since(website.last_checked) > 60:
                self.q.enqueue(check_website, website.id)
            self.values["website"] = website
            self.values["theme_color"] = "#c5c5c5"
            self.finalize("pinnable/websites_info.html")
        else:
            self.redirect("/websites")


class PinnableWebsitesInfoJSONHandler(WebHandler):
    @authenticated
    def get(self, website_id):
        website = self.get_website_by_id(website_id)
        if website and website.account_id == self.current_user.id:
            self.write(json.dumps(website.to_dict()))
        else:
            self.set_status(404)


class PinnableWebsitesLogsHandler(WebHandler):
    @authenticated
    @gen.coroutine
    def get(self, website_id):
        website = self.get_website_by_id(website_id)
        if website and website.account_id == self.current_user.id:
            self.set_header("content-type", "text/event-stream")
            self.set_header("cache-control", "no-cache")
            self.set_header("x-accel-buffering", "no")
            last_log_id = 0
            if len(website.tasklogs) > 0:
                last_log_id = website.tasklogs[0].id
            if "last_log_id" in self.request.arguments:
                last_log_id = int(self.get_argument("last_log_id"))
            self.logger.info(
                "Website {website_id} - last_log_id: {last_log_id}",
                website_id=website_id,
                last_log_id=last_log_id,
            )
            while True:
                a_log = self.get_website_tasklog_later_than_id(website.id, last_log_id)
                if a_log:
                    if a_log.cid is None:
                        cid = "null"
                    else:
                        cid = f'"{a_log.cid}"'
                    if a_log.ipns is None:
                        ipns = "null"
                    else:
                        ipns = f'"{a_log.ipns}"'
                    if a_log.size is None:
                        size = "null"
                    else:
                        size = f"{a_log.size}"
                    payload = f'data: {{"icon":"{a_log.icon}","created":{a_log.created},"event":"{a_log.event}","cid":{cid},"ipns":{ipns},"size":{size}}}\n\n'  # noqa
                    try:
                        self.write(payload)
                        yield self.flush()
                    except StreamClosedError:
                        pass
                    last_log_id = a_log.id
                else:
                    self.session.close()
                    yield gen.sleep(1)
        else:
            return self.finish()


class PinnableWebsitesPinHandler(WebHandler):
    @authenticated
    def get(self, website_id):
        self.q.enqueue(check_account, self.current_user.id)
        website = self.get_website_by_id(website_id)
        ipfs_path = website.ipfs_path
        if website and ipfs_path:
            session_message = "Pinning website: %s" % ipfs_path
            self.web_session["message"] = session_message
            self.logger.info("Pinning website: {ipfs_path}", ipfs_path=ipfs_path)
            self.q.enqueue(check_website, website.id)
            self.q.enqueue(pin_website, website.id)
        self.redirect("/websites/%s" % website_id)


class PinnableWebsitesPinUUIDHandler(WebHandler):
    def get(self, pin_api_uuid: str):
        website = self.get_website_by_pin_api_uuid(pin_api_uuid)
        if website:
            account = self.get_account_by_id(website.account_id)
            if account.dwb_balance > 0:
                self.q.enqueue(pin_website, website.id)
                self.set_status(202)
                o = {}
                o["status"] = "ok"
                o["message"] = "website is being pinned"
            else:
                self.set_status(402)
                o = {}
                o["status"] = "error"
                o["message"] = "insufficient dwb balance"
            self.write(json.dumps(o))
        else:
            self.set_status(404)
            o = {}
            o["status"] = "error"
            o["message"] = "website not found"
            self.write(json.dumps(o))


class PinnableWebsitesPinUUIDStatusHandler(WebHandler):
    def get(self, pin_api_uuid: str):
        website = self.get_website_by_pin_api_uuid(pin_api_uuid)
        if website:
            o = {}
            o["status"] = "ok"
            o["last_known_cid"] = website.last_known_cid
            o["last_known_ipns"] = website.last_known_ipns
            o["size"] = website.size
            o["created"] = website.created
            o["last_pinned"] = website.last_pinned
            o["last_checked"] = website.last_checked
            self.write(json.dumps(o))
        else:
            self.set_status(404)
            o = {}
            o["status"] = "error"
            o["message"] = "website not found"


class PinnableWebsitesRemoveHandler(WebHandler):
    @authenticated
    def post(self, website_id: int):
        website = self.get_website_by_id(website_id)
        if website and website.account_id == self.current_user.id:
            self.delete_website_tasklogs_by_website_id(website.id)
            self.delete_website_by_id(website.id)
            self.redirect("/websites")
        else:
            self.redirect("/websites")


pinnable_handlers = [
    (r"/websites/?$", PinnableWebsitesHandler),
    (r"/websites/([0-9]+)/?$", PinnableWebsitesInfoHandler),
    (r"/websites/([0-9]+).json$", PinnableWebsitesInfoJSONHandler),
    (r"/websites/([0-9]+)/logs/?$", PinnableWebsitesLogsHandler),
    (r"/websites/remove/([0-9]+)/?$", PinnableWebsitesRemoveHandler),
    (r"/websites/add/?$", PinnableWebsitesAddHandler),
    (r"/websites/pin/([0-9]+)/?$", PinnableWebsitesPinHandler),
    (
        r"/pin/([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})/?$",  # noqa
        PinnableWebsitesPinUUIDHandler,
    ),
    (
        r"/pin/([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})/status/?$",  # noqa
        PinnableWebsitesPinUUIDStatusHandler,
    ),
]
