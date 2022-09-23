from ubuntu:22.04
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip
COPY api_demo_server ./api_demo_server
COPY pyproject.toml .
RUN python3 -m pip install .
ENTRYPOINT ["uvicorn", "api_demo_server.app:app", "--reload", "--host=0.0.0.0"]
