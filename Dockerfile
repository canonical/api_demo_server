from --platform=$BUILDPLATFORM ubuntu:22.04
LABEL org.opencontainers.image.source=https://github.com/canonical/api_demo_server

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip
COPY ./pyproject.toml .

# create dummy project folder just to keep the layer with dependencies untouched until pyproject is changed
RUN mkdir api_demo_server && echo "__version__ = '1.0.0.dev0'" > api_demo_server/__init__.py
RUN python3 -m pip install .
COPY ./api_demo_server ./api_demo_server
EXPOSE 8000
ENTRYPOINT ["uvicorn", "api_demo_server.app:app", "--host=0.0.0.0"]
