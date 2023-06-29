#!/usr/bin/env python3

import os.path

import galaxy
from galaxy.handlers import BaseHandler


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
