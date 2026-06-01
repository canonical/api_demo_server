FROM ubuntu:26.04
LABEL org.opencontainers.image.source=https://github.com/canonical/api_demo_server

RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip
COPY ./pyproject.toml .
COPY ./LICENSE .

# create dummy project folder just to keep the layer with dependencies untouched until pyproject is changed
RUN mkdir -p src/api_demo_server && echo "__version__ = '0.0.1.dev0'" > src/api_demo_server/__init__.py
RUN python3 -m pip install .
COPY ./src/api_demo_server ./src/api_demo_server
WORKDIR /src
EXPOSE 8000
ENTRYPOINT ["uvicorn", "api_demo_server.app:app", "--host=0.0.0.0"]
