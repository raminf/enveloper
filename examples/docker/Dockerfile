# Example: run app inside Docker with env from enveloper (no .env file in image).
# Install enveloper from PyPI; entrypoint pulls from AWS and runs export, then the app.

FROM python:3.12-slim

RUN pip install --no-cache-dir enveloper[aws]

ENV ENVELOPER_PROJECT=myproject
ENV ENVELOPER_DOMAIN=mydomain

WORKDIR /app

COPY examples/docker/entrypoint.sh /app/entrypoint.sh
COPY examples/docker/app.sh /app/app.sh
RUN chmod +x /app/entrypoint.sh /app/app.sh

# Default: pull from AWS, export, then run app.sh
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["/app/app.sh"]
