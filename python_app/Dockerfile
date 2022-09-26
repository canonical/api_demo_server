from ubuntu:22.04
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip
COPY ./pyproject.toml .
COPY ./api_demo_server ./api_demo_server
RUN python3 -m pip install .
EXPOSE 8000
ENTRYPOINT ["uvicorn", "api_demo_server.app:app", "--host=0.0.0.0"]
