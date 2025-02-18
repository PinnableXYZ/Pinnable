#!/usr/bin/env python3

import hashlib
import os.path
import re
import tempfile
import time
import uuid

import magic
import requests
from PIL import Image

import config
import galaxy
from galaxy.handlers import BaseHandler
from galaxy.models.pinnable import CIDObject

IPNS_RE = re.compile(r"^k51[0-9a-z]{59}$")


class WebHandler(BaseHandler):
    def breadcrumb(self, paths, theme_color=None):
        o = '<div id="breadcrumb" style="background-color: ' + theme_color + '">'
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

    def process_object_upload(self):
        if "file" not in self.request.files:
            self.add_error("No file uploaded.")
            return
        file = self.request.files["file"][0]
        original_filename = file["filename"]
        size = len(file["body"])
        file_path = tempfile.mkstemp()[1]
        cid_object = None
        cid_thumb = None
        with open(file_path, "wb") as f:
            f.write(file["body"])
            file_sha256 = self.sha256(file_path)
            # get type via libmagic
            mime = magic.Magic(mime=True)
            file_type = mime.from_file(file_path)
            if file_type.startswith("image"):
                # create thumbnail
                thumb_path = tempfile.mkstemp()[1]
                self.create_thumbnail(file_path, thumb_path, file_type)
                # upload to IPFS
                try:
                    cid = self.ipfs_add(thumb_path)
                    if cid:
                        cid_thumb = cid
                except Exception as e:
                    self.add_error(f"Failed to upload thumbnail to IPFS: {e}")
            try:
                cid = self.ipfs_add(file_path)
                if cid:
                    cid_object = cid
            except Exception as e:
                self.add_error(f"Failed to upload file to IPFS: {e}")
                return
        o = {}
        o["original_filename"] = original_filename
        o["content_type"] = file_type
        o["size"] = size
        o["sha256"] = file_sha256
        o["cid_object"] = cid_object
        o["cid_thumb"] = cid_thumb
        co = CIDObject()
        co.object_uuid = str(uuid.uuid4())
        co.account_id = self.current_user.id
        co.filename = original_filename
        co.content_type = file_type
        co.size = size
        co.cid = cid_object
        co.cid_thumb = cid_thumb
        co.sha256 = file_sha256
        co.created = int(time.time())
        co.last_modified = int(time.time())
        self.session.add(co)
        self.session.commit()

    def create_thumbnail(self, file_path, thumb_path, file_type):
        img = Image.open(file_path)
        img.thumbnail((256, 256))
        # Extract format from MIME type (e.g., 'image/jpeg' -> 'JPEG')
        img_format = file_type.split("/")[-1].upper()
        img.save(thumb_path, format=img_format, quality=95)
        return thumb_path

    def ipfs_add(self, file_path):
        api_request = f"{config.ipfs_server}/api/v0/add?pin=true"
        files = {"file": open(file_path, "rb")}
        try:
            resp = requests.post(api_request, files=files, timeout=30)
            o = resp.json()
            if "Hash" in o:
                return o["Hash"]
        except Exception as e:
            self.logger.exception("Failed to add file to IPFS: %s", repr(e))
        return None

    def sha256(self, file_path):
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                data = f.read(65536)
                if not data:
                    break
                sha256.update(data)
        return sha256.hexdigest()

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
