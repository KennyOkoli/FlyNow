terraform {
  required_providers {
     aws = {
        source = "hashicorp/aws"
        version = "~>6.0"
    }
  }
}

variable "env" {}

resource "aws_ecs_cluster" "flynow-cluster" {
    name = "flynow-cluster-${var.env}"
    setting {
        name = "containerInsights"
        value = "enabled"
    }
    service_connect_defaults {
        namespace = aws_service_discovery_http_namespace.flynow-cloudmap.name
    }
}