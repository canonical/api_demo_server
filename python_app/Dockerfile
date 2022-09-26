from ubuntu:22.04
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip
COPY ./pyproject.toml .
RUN python3 -m pip install .

# copy code only after install deps to avoid img rebuilding
COPY ./api_demo_server ./api_demo_server
ENTRYPOINT ["uvicorn", "api_demo_server.app:app", "--reload", "--host=0.0.0.0"]
