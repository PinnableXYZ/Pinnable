#!/usr/bin/env python3

import requests

import config
from galaxy.handlers.web import APIHandler


class CIDPreviewHandler(APIHandler):
    def get(self, cid):
        obj = self.get_object_by_cid_any(cid)
        if not obj:
            self.set_header("Cache-Control", "public, max-age=120")
            self.set_status(404)
            self.write("CID is outside of the scope of this service")
            return
        url = f"{config.cid_ssot}/ipfs/{cid}"
        try:
            resp = requests.head(url, timeout=30)
        except Exception as e:
            self.set_status(500)
            self.write("Failed to fetch CID preview: " + str(e))
            return
        if resp.status_code == 200:
            headers = dict(resp.headers)
            content_type = headers.get("Content-Type", "application/octet-stream")
            if content_type.startswith("image/"):
                self.set_header("Content-Type", content_type)
                self.set_header("Cache-Control", "public, max-age=31536000")
                self.set_header("Access-Control-Allow-Origin", "*")
                self.set_header("Access-Control-Allow-Methods", "GET")
                self.set_header("Access-Control-Allow-Headers", "Content-Type")
                self.set_header("Access-Control-Max-Age", "86400")
                if "Content-Length" in headers:
                    size = int(headers.get("Content-Length"))
                else:
                    self.set_status(400)
                    self.write("Missing Content-Length header for CID preview")
                    return
                if size > (1024 * 1024 * 100):
                    self.set_status(400)
                    self.write("File too large for preview")
                    return
                try:
                    binary = requests.get(url, timeout=30).content
                    self.write(binary)
                except Exception as e:
                    self.set_header("Cache-Control", "public, max-age=60")
                    self.set_status(500)
                    self.write(f"Failed to fetch CID preview: {e}")
            else:
                self.set_status(400)
                self.write("This endpoint only supports image previews")
        else:
            self.set_status(404)
            self.write("CID not available")


cid_handlers = [(r"/cid-preview/([a-zA-Z0-9\.]+)/?$", CIDPreviewHandler)]
