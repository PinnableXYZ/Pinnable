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

## Storage Backend

The project should be backed by a new storage backend with at least 1TB of space.

## URL Inventory

GET /objects: list all objects
GET /objects/upload: interface for uploading
POST /objects/upload: Upload a single object

## API Inventory

## Preview

The object for preview can be a CID too.

## Must Have

- [x] Preview for video and audio
- [x] Preview for PDF
- [ ] Generic square icons for other types
- [ ] Pagination
- [x] Prewarm with a list of public gateways
- [ ] Drag-n-drop upload interface
- [ ] API for upload, list, and unpin
- [x] /cid-preview/ for safe and fast preview

## Nice to Have

- [x] A button to download the file (Content-Disposition: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Disposition)
- [ ] Support GIF resizing for previewing
- [ ] Support for large file (>1G)
- [ ] Text meta info, save as CID
- [ ] Projects, like folders, for organzing uploads
