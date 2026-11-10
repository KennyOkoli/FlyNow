# Confirm the container ports

resource "aws_ecs_service" "backend-service"{
    name = "backend-service-${var.env}"
    cluster = aws_ecs_cluster.flynow-cluster.id
    task_definition = aws_ecs_task_definition.backend-task-def.arn
    desired_count = 0
    launch_type = "EC2"

    service_connect_configuration {

       enabled = true
       service {
         port_name = "http"
         discovery_name = "backend-tasks"
         client_alias {
           dns_name = "backend"
           port = 8080
         }
       }
    }
    
    network_configuration {
       subnets = var.private-subnets
       security_groups = [aws_security_group.backend-sg.id]
    }

    ordered_placement_strategy {
       type = "spread"
       field = "instanceId"
    }

    lifecycle {
      ignore_changes = [task_definition]
    }
}

resource "aws_security_group" "backend-sg" {
    name = "backend-sg-${var.env}"
    vpc_id = var.vpc
}

resource "aws_security_group_rule" "backend-sg-rule-1" {
    type = "ingress"
    security_group_id = aws_security_group.backend-sg.id
    source_security_group_id = aws_security_group.task-sg-frontend.id
    protocol = "tcp"
    from_port = 8080
    to_port = 8080
}

resource "aws_security_group_rule" "backend-sg-rule-2" {
    type = "egress"
    security_group_id = aws_security_group.backend-sg.id
    cidr_blocks = [var.public]
    protocol = "tcp"
    from_port = 0
    to_port = 65535
}

