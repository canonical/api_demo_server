# Description
This is a demo server that serves multiple API endpoints.
Server is used to show connections to PostgreSQL and Prometheus.

To see API reference start the server and open: http://127.0.0.1:8000/docs
To get prometheus metrics: http://127.0.0.1:8000/metrics

# Usage
Download and start PostgreSQL container:
```
docker run --name postgres -e POSTGRES_PASSWORD=mysecretpassword -d postgres
```

Get psql container IP:
```
docker ps  # get postgres container ID
docker inspect <postgres container ID> | grep IPAddress
```

Build a docker container via:
```
docker build -t api_demo_server .
```

Start demo server:
```
docker run --rm -e DEMO_SERVER_DB_HOST=<postgres container IP> -p 8000:8000 api_demo_server
```