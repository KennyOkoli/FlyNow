# Ensure that the name of the container has also been updated in the CI/CD pipeline

variable "db_port" {
    default = "3306"
}
variable "db_host" {
    default = "mysql"
}
variable "db_name" {}
variable "db_username" {}
variable "db_password" {}
variable "s3_bucket" {}
variable "env" {}

resource "aws_ecs_task_definition" "frontend-task-def" {
    network_mode = "awsvpc"
    requires_compatibilities = ["EC2"]
    family = "frontend-web-${var.env}"
    execution_role_arn = aws_iam_role.task-def-role.arn
    task_role_arn = aws_iam_role.task-role.arn

    container_definitions = jsonencode([
        {
        name = "frontend-${var.env}"
        image = "nginx:latest"
        cpu = 256
        memory = 512
        portMappings = [{
            containerPort = 4000
        }]
        environment = [
            {
                name = ENDPOINT
                value = var.backend
            }
            ]
        }
    ])
}

variable "backend" {
    default = aws_ecs_service.backend
}

resource "aws_ecs_task_definition" "backend-task-def" {
    network_mode = "awsvpc"
    requires_compatibilities = ["EC2"]
    family = "backend-web-${var.env}"
    execution_role_arn = aws_iam_role.task-def-role.arn
    task_role_arn = aws_iam_role.task-role.arn

    container_definitions = jsonencode([
        {
        name = "backend-${var.env}"
        image = "nginx:latest"
        cpu = 256
        memory = 512
        portMappings = [{
            containerPort = 4000
        }]
        environment = [
            {   
                name = "DB_NAME"
                value = var.db_name
            },
            {
                name = "DB_USERNAME"
                value = var.db_username
            },
            {
                name = "DB_PASSWORD"
                value = var.db_password
            },
            {
                name = "DB_PORT"
                value = var.db_port
            },
            {
                name = "DB_HOST"
                value = var.db_host
            },
            ]
        }
    ])
}

