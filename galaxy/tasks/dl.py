import pylibmc
import requests
from defusedxml import ElementTree as ET

import config


def check_update(app, appcast):
    mc_key = "dl:" + app + ":latest:link"
    # Read appcast.xml
    r = requests.get(appcast, timeout=30)
    if r.status_code != 200:
        print("Error: Failed to read appcast.xml")
        return
    # Parse appcast.xml
    root = ET.fromstring(r.text)
    namespaces = {"sparkle": "http://www.andymatuschak.org/xml-namespaces/sparkle"}

    # Get latest version
    latest_version = root.find("channel/item/sparkle:version", namespaces).text
    # Get latest short version
    latest_short_version = root.find(
        "channel/item/sparkle:shortVersionString", namespaces
    ).text
    version = latest_short_version + " (" + latest_version + ")"
    # Get latest download link
    latest_link = root.find("channel/item/enclosure").attrib["url"]
    if latest_link is not None and len(latest_link) > 0:
        mc_value = latest_link
        mc = pylibmc.Client(
            [config.memcached_host],
            binary=True,
            behaviors={"tcp_nodelay": True, "ketama": True},
        )
        mc.set(mc_key, mc_value, 600)
        print("Updated " + app + " to " + version)
