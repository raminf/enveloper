#!/bin/sh
# When the host injects env (eval export then docker run -e VAR ...), the container
# just runs the command. No enveloper needed in the image.
exec "$@"
