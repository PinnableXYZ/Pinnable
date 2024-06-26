# CID Manager

Easy-to-use web interface for interacting with an IPFS server.

Each row in the database represents a CID and should include the following information:

- CID
- version: 0 or 1
- account_id: required
- website_id: optional, if it is associated with a website
- length: byte length, the upper limit is currently 100M per object
- content_type: string, can be detected with libmagic
- has_preview: default 0, if 1, it should load a visual preview from an URL like this: /cid/:cid/preview (content-type: image/png). Preview can be generated with a remote worker for image types.
