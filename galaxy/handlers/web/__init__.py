#!/usr/bin/env python3

import os.path
import re

import galaxy
from galaxy.handlers import BaseHandler

IPNS_RE = re.compile(r"^k51[0-9a-z]{59}$")


class WebHandler(BaseHandler):
    def breadcrumb(self, paths):
        o = '<div id="breadcrumb">'
        i = 0
        for path in paths:
            if ":" in path:
                parts = path.split(":")
                o = o + '<a href="' + parts[1] + '">' + parts[0] + "</a>"
            else:
                o = o + "<span>" + path + "</span>"
            i = i + 1
            if i < len(paths):
                o = o + '<i class="chevron-right"></i> '
        o = o + "</div>"
        return o

    def web_session_message(self):
        o = ""
        if "message" in self.web_session:
            o = (
                o
                + '<div id="web-session-message"'
                + " onclick=\"this.style.display = 'none';\">"
            )
            o = o + self.web_session["message"]
            o = o + "</div>"
            del self.web_session["message"]
        return o

    def flash(self, message: str):
        self.web_session["message"] = message

    def verify_website_name(self):
        if "name" in self.request.arguments:
            name = self.get_argument("name").strip()
            name_length = len(name)
        else:
            name = None
            name_length = 0
            self.add_error("Name is required.")
        name = name.lower()
        self.values["website_name"] = name
        if name_length == 62 and name.startswith("k51"):
            if not IPNS_RE.match(name):
                self.add_error("Invalid IPNS provided.")
            return
        if name.endswith(".eth"):
            existing_name = self.get_website(name, account_id=self.current_user.id)
            if existing_name:
                self.add_error(
                    "Website is already added: <a href='/websites/%d'>%s</a>"
                    % (existing_name.id, name)
                )
        if name_length > 200:
            self.add_error("Name must be less than 200 characters.")

    def verify_website_subname(self, website_id: int | None = None):
        self.values["website_subname"] = None
        if "subname" in self.request.arguments:
            subname = self.get_argument("subname").strip()
            subname_length = len(subname)
        else:
            subname = None
            subname_length = 0
            self.add_error("Subname is required.")
            return
        self.values["website_subname"] = subname
        if subname_length > 64:
            self.add_error("Subname must be less than 64 characters.")
            return
        if subname_length == 0:
            self.add_error("Subname is required.")
            return
        # Regular Expression:
        # - lower case letters and numbers
        # - dash (-) is allowed, but not at the beginning or end, not consecutively
        pattern = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
        if not pattern.match(subname):
            self.add_error("Subname must be lower case letters and numbers only.")
            return
        # Check if subname is already used
        if website_id:
            website = self.get_website_by_id(website_id)
            if (
                website.subname == subname
                and website.account_id != self.current_user.id
            ):
                self.add_error("Subname is used by another website.")
                return
        else:
            website = self.get_website_by_subname(subname=subname)
            if website:
                self.add_error("Subname is used by another website.")
                return

    def finalize(
        self, template_name, write_static=False, static_key="", output_string=False
    ):
        template_file_desktop = "desktop" + "/" + template_name
        template_file_mobile = "mobile" + "/" + template_name

        if "now" not in self.values:
            self.values["now"] = self.now()

        prefix = os.path.dirname(__file__)[:-12]
        if self.is_mobile:
            template_mobile_path = prefix + "templates/" + template_file_mobile
            if os.path.exists(template_mobile_path):
                t = template_file_mobile
            else:
                t = template_file_desktop
        else:
            t = template_file_desktop
        template = self.env.get_template(t)
        self.set_header("Server", "Galaxy/" + str(galaxy.__version__))
        self.set_header("X-Frame-Options", "SAMEORIGIN")
        latency = int(self.request.request_time() * 1000.0)
        self.values["request_time"] = latency
        self.set_marker("finish_page")
        self.values["markers"] = self.markers
        o = template.render(self.values)
        if output_string:
            return o
        else:
            self.write(o)
        if write_static:
            self.mc.set(static_key, o, 3600)
