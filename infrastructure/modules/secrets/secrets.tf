terraform {
  required_providers {
     aws = {
        source = "hashicorp/aws"
        version = "~>6.0"
    }
  }
}


variable env{}

resource "aws_secretsmanager_secret" "flynow-db-secrets" {
    name = "flynow-db-secrets${var.env}"
}

/*resource "aws_secretsmanager_secret_version" "db-secrets" {
    secret_id = aws_secretsmanager_secret.flynow-db-secrets.id
    secret_string = jsonencode(var.db-credentials)
}

variable "db-credentials" {
  default = {
    username = "Kenny"
    password = "kenny2007"
  }
  sensitive = true
} */