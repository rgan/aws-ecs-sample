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
        "memory": 8,
        "cpu": 1
    }
    api_container = {
        "name": "api",
        "image": "%s/api" % docker_user,
        "cpu": 1,
        "memory": 8,
        "essential": True,
        "portMappings": [
            {
              "containerPort": 8080,
              "hostPort": 8080
            }
        ]
    }
    return [nginx_container, api_container]

def stop_and_delete_service(client, svc_name):
    services_response = client.list_services()
    print services_response
    # {'ResponseMetadata':
    # { u'serviceArns': [u'arn:aws:ecs:us-west-2:958237526296:service/sample-webapp']}
    svc_arns = services_response["serviceArns"]
    svc_exists = svc_arns and [svc_name in svc_arn for svc_arn in svc_arns][0]
    if svc_exists:
        client.update_service(
            service=svc_name,
            desiredCount=0
        )
        client.delete_service(service=svc_name)

def deploy_to_ecs(config, docker_user):
    client = boto3.client('ecs', region_name="us-west-2",
                              aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                              aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"]
                              )
    stop_and_delete_service(client, "ecs-sample")
    task_def = client.register_task_definition(family="api",
                                               containerDefinitions=create_container_defs(docker_user))
    print task_def
    taskdef_arn = task_def["taskDefinition"]["taskDefinitionArn"]
    service_response = client.create_service(serviceName='ecs-sample',
                                        taskDefinition= taskdef_arn, desiredCount=1)
    print service_response

def deploy_locally(config):
    api_containers = []
    for i in range(0,config["no_of_backends"]):
       api_containers.append("api_%s" % i)
    local("docker rm -f %s nginx || true " % " ".join(api_containers))
    api_container_cmds = []
    api_links = []
    for i in range(0,config["no_of_backends"]):
        api_container_cmds.append("docker run --name api_%s -d api && " % i)
        api_links.append("--link api_{0}:api_{0}".format(i))
    local("%s docker run --name nginx %s -p 8080:8080 -d nginx" % \
          (" ".join(api_container_cmds), " ".join(api_links)))

@task
def start_consul():
    local("docker run -p 8400:8400 -p 8500:8500 -p 8600:53/udp -h node1 progrium/consul -server -bootstrap")

@task
def deploy(docker_user, aws_ecs="n", do_build="y"):
    config = json.load(file("config.json"))
    if do_build == 'y':
        local("rm -rf build && mkdir -p build")
        local("tar -czf build/api.tar.gz main.py api/")
        configure(config)
        build_containers(docker_user)
        local("rm -rf build")
    if aws_ecs == 'y':
        deploy_to_ecs(config, docker_user)
    else:
        deploy_locally(config)

