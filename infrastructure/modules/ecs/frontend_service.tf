# Confirm the container ports
# Update ECS lifecycle

variable "private-subnets" {}
variable "nacl" {}
variable "db-sg" {}
variable "public" {}
variable "secrets" {}
variable "vpc" {}
variable "target-arn" {}

resource "aws_ecs_service" "flynow-ecs-frontend"{
    name = "flynow-web-${var.env}"
    cluster = aws_ecs_cluster.flynow-cluster.id
    task_definition = aws_ecs_task_definition.frontend-task-def.arn
    desired_count = 2
    launch_type = "EC2"

    load_balancer {
       target_group_arn = var.target-arn
       container_name = "web-app-${var.env}"
       container_port = 4000
    }

    network_configuration {
       subnets = var.private-subnets
       security_groups = [aws_security_group.task-sg-frontend.id]
    }
    
    ordered_placement_strategy {
       type = "spread"
       field = "instanceId"
    }
    /*lifecycle {
      ignore_changes = [task_definition]
    }*/
}

resource "aws_security_group" "task-sg-frontend" {
    name = "task-sg-frontend-${var.env}"
    vpc_id = var.vpc
}

variable "alb_sg" {}

resource "aws_security_group_rule" "task-rule-1" {
    type = "ingress"
    security_group_id = aws_security_group.task-sg-frontend.id
    source_security_group_id = var.alb_sg
    protocol = "tcp"
    from_port = 4000
    to_port = 4000
}

resource "aws_security_group_rule" "task-rule-3" {
    type = "egress"
    security_group_id = aws_security_group.task-sg-frontend.id
    cidr_blocks = [var.public]
    protocol = "tcp"
    from_port = 0
    to_port = 65535
}

resource "aws_network_acl_association" "task-subnet-nacl" {
    count = 2
    network_acl_id = var.nacl
    subnet_id = var.private-subnets[count.index]
}
