import json
import boto3
from jinja2.environment import Template
import os
from fabric.decorators import task
from fabric.api import local, lcd

def generate_from_template(template_file, output_file, config):
    with open(output_file, "w+") as output_file:
        with open(template_file) as template_file:
            output_file.write(Template(template_file.read()).render(config=config))

def configure(config):
    generate_from_template("nginx.conf.tmpl", "build/nginx_site", config)

def build_containers(docker_user):
    local("cp tornado/Dockerfile requirements.txt config.json build")
    with(lcd("build")):
        local("docker build -t api .")
        local("IMAGE_ID=$(docker images -q api) && docker tag -f $IMAGE_ID {0}/api:latest && docker push {0}/api".format(docker_user))
    local("cp nginx/Dockerfile nginx.conf build")
    with(lcd("build")):
        local("docker build -t nginx .")
        local("IMAGE_ID=$(docker images -q nginx) && docker tag -f $IMAGE_ID {0}/nginx:latest && docker push {0}/nginx".format(docker_user))

def create_container_defs(docker_user):
    nginx_container = {
        "name": "nginx",
        "links": ["api"],
        "image": "%s/nginx" % docker_user,
        "essential": True,
        "portMappings": [
            {
              "containerPort": 80,
              "hostPort": 80
            }
        ],
        "memory": 500,
        "cpu": 10
    }
    api_container = {
        "name": "api",
        "image": "%s/api" % docker_user,
        "cpu": 10,
        "memory": 500,
        "essential": True,
        "portMappings": [
            {
              "containerPort": 8080,
              "hostPort": 8080
            }
        ]
    }
    return [nginx_container, api_container]

def create_service_def(svc_name, task_def_arn):
    return {
        "serviceName": svc_name,
        "taskDefinition": task_def_arn,
        "desiredCount": 1,
        "clientToken": "secret"
    }

def stop_and_delete_service(client, svc_name):
    client.update_service(
        service=svc_name,
        desiredCount=0
    )
    client.delete_service(service=svc_name)

@task
def deploy(docker_user, aws_ecs=False):
    config = json.load(file("config.json"))
    local("rm -rf build && mkdir -p build")
    configure(config)
    build_containers(docker_user)
    if aws_ecs:
        client = boto3.client('ecs', region_name="us-west-2",
                              aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                              aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"]
                              )
        stop_and_delete_service(client, "ecs-sample")
        task_def = client.register_task_definition(family="api",
                                                   containerDefinitions=create_container_defs(docker_user))
        service_def = create_service_def("ecs-sample", task_def["ResponseMetadata"]["taskDefinitionArn"])
    else:
        api_containers = []
        for i in range(0,config["no_of_backends"]):
           api_containers.append("api_%s" % i)
        local("docker rm -f %s nginx || true " % api_containers)
        api_container_cmds = []
        api_links = []
        for i in range(0,config["no_of_backends"]):
            api_container_cmds.append("docker run --name api_%s -d api" % i)
            api_links.append("--link api_{0}:api_{0}".format(i))
        local("%s && docker run --name nginx %s -p 8080:8080 -d nginx".\
                format(" ".join(api_container_cmds), " ".join(api_links)))

