A youtube-dl web interface, written in python3 with flask.

Warning: this project currently uses the integrated flask web server to serve pages.
Because of this, and for various other reasons, this server should NOT be accessible from outside a trusted
local network.

Currently, this program listens on 127.0.0.1:5000 and serves a user interface, allowing users to download
live streams and videos to the current directory. In the future, this will be configurable through a config file.

Run `python3 -m ytdlweb` after cloning this repo to run the server.
