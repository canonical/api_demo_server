docker run --rm -e DEMO_SERVER_DB_HOST=172.17.0.2 -p 8000:8000 api_demo_server
# where 172.17.0.2 is an IP of a docker container with postgres
# sudo docker inspect <postgres container ID> | grep IPAddress