This is a demo Python server written with FastAPI. The server connects to PostgreSQL and exposes Prometheus metrics.

The server is packaged as a "rock" using Canonical's OCI-compliant format for container images.

# Build and run the container image

You'll need [Rockcraft](https://documentation.ubuntu.com/rockcraft/stable/) and [Docker](https://docs.docker.com/).

1. Build the container image from source:

    ```text
    rockcraft pack
    ```

    This creates a `.rock` file. The name of the `.rock` file depends on your system architecture.

2. Make the container image available to Docker:

    ```text
    rockcraft.skopeo --insecure-policy \
        copy "oci-archive:<rock>" "docker-daemon:api-demo-server:integration"
    ```

    Where `<rock>` is the path to the `.rock` file.

3. Run the container image alongside PostgreSQL:

    ```text
    docker compose up
    ```

4. In a separate terminal, check that the server is available:

    ```text
    curl http://localhost:8000/version
    ```

    This returns a JSON object that contains the server's version number.

The server has several other API endpoints, including:

- API docs - http://localhost:8000/docs
- Prometheus metrics - http://localhost:8000/metrics

# Deploy the container image as a Juju charm

See [From zero to hero: Write your first Kubernetes charm](https://documentation.ubuntu.com/ops/latest/tutorial/from-zero-to-hero-write-your-first-kubernetes-charm/)

# Server environment variables

- `DEMO_SERVER_LOGFILE` - Path to the file where logs should be written
- `DEMO_SERVER_DB_HOST` - IP address of the database host
- `DEMO_SERVER_DB_PORT` - Port of the database host
- `DEMO_SERVER_DB_USER` - Username that has access to the database
- `DEMO_SERVER_DB_PASSWORD` - Password for the `DEMO_SERVER_DB_USER` user
