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
        local("docker push %s/api" % docker_user)
    local("cp nginx/Dockerfile nginx.conf build")
    with(lcd("build")):
        local("docker build -t nginx .")
        local("docker push %s/nginx" % docker_user)

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

def create_service_def(task_def_arn):
    return {
        "serviceName": "ecs-sample",
        "taskDefinition": task_def_arn,
        "desiredCount": 1,
        "clientToken": "secret"
    }

@task
def deploy(docker_user):
    config = json.load(file("config.json"))
    local("rm -rf build && mkdir -p build")
    configure(config)
    build_containers(docker_user)
    client = boto3.client('ecs', region_name="us-west-2",
                          aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                          aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"]
                          )
    task_def = client.register_task_definition(family="api",
                                               containerDefinitions=create_container_defs(docker_user))
    service_def = create_service_def(task_def["ResponseMetadata"]["taskDefinitionArn"])
