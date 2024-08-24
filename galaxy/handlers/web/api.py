#!/usr/bin/env python3

import json

import requests

import config
from galaxy.handlers.web import WebHandler


class APIIPFSPeersHandler(WebHandler):
    def ipfs_name_resolve(self, name: str):
        api_request = f"{config.ipfs_server}/api/v0/name/resolve?arg={name}"
        try:
            resp = requests.post(api_request, timeout=30)
            o = resp.json()
            if "Path" in o:
                return o["Path"][6:]
        except Exception:
            message = "Failed to resolve IPFS name: " + name
            self.logger.exception(message)
            return None

    def ipfs_findprovs(self, cid: str):
        peers = []
        api_request = (
            f"{config.ipfs_server}/api/v0/routing/findprovs?arg={cid}&num-providers=100"
        )
        try:
            resp = requests.post(api_request, timeout=30)
            t = resp.text.strip()
            for line in t.split("\n"):
                try:
                    o = json.loads(line)
                    if "Responses" in o:
                        responses = o["Responses"]
                        if responses is None or len(responses) == 0:
                            continue
                        peer = o["Responses"][0]["ID"]
                        if peer not in peers:
                            peers.append(peer)
                except Exception:
                    self.logger.exception("Failed to parse IPFS findprovs response")
        except Exception:
            message = "Failed to find IPFS providers for CID: " + cid
            self.logger.exception(message)
        return peers

    def get(self, query):
        cid = None
        if query.startswith("k51"):
            name = query
            cid = self.ipfs_name_resolve(name)
        elif query.startswith("Qm"):
            cid = query
        elif query.startswith("baf"):
            cid = query
        elif query.endswith(".eth"):
            name = query
            cid = self.ipfs_name_resolve(name)
        peers = []
        if cid is not None:
            peers = self.ipfs_findprovs(cid)
        self.set_header("Content-Type", "application/json")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Methods", "GET")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header("Access-Control-Max-Age", "86400")
        self.set_header("Cache-Control", "public, max-age=600")
        self.set_header("CDN-Cache-Control", "public, max-age=600")
        self.write({"peers": peers})


api_handlers = [(r"/api/v0/ipfs/peers/([a-zA-Z0-9\.]+)/?$", APIIPFSPeersHandler)]
