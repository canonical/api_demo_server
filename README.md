# Description
This is a demo server based on Python FastAPI.
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

# Configuration via environment variables
You can configure application by applying following environment variables:

| Environment Variable    	| Value             	| Description                                     	|
|-------------------------	|-------------------	|-------------------------------------------------	|
| DEMO_SERVER_LOGFILE     	| \<path/to/log.log> 	| Path to the file where logs should be written   	|
| DEMO_SERVER_DB_HOST     	| \<Host IP>         	| IP address of the host where Database is hosted 	|
| DEMO_SERVER_DB_PORT     	| \<Host Port>       	| Port of the host where Database is hosted       	|
| DEMO_SERVER_DB_USER     	| \<Username>        	| Username that has access to `names` Database    	|
| DEMO_SERVER_DB_PASSWORD 	| \<Password>        	| Password to the `DEMO_SERVER_DB_USER` user      	|

# Publish to registry

```
docker buildx build -t ghrc.io/canonical/api_demo_server:1.0.0 --platform linux/amd64,linux/arm64,linux/ppc64le --push  .
```