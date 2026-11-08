terraform {
  required_providers {
     aws = {
        source = "hashicorp/aws"
        version = "~>6.0"
    }
  }
}

variable "identity_center_region" {
    default = "us-east-1"
}

variable "ec2-arn" {}

variable "jeff_email" {
    default = "jahbuchimokoli3@gmail.com"
    sensitive = true
}

variable "aws_region"{
    type = string
    default = "af-south-1"
}

variable "s3-arn" {}
variable "secret-arn" {}

data "aws_ssoadmin_instances" "center" {} 

locals {
    idStore_id = tolist(data.aws_ssoadmin_instances.center.identity_store_ids)[0]
    Account_arn = tolist(data.aws_ssoadmin_instances.center.arns)[0]
}
variable "aws_provider" {}
resource "aws_identitystore_user" "jeff" {
    identity_store_id = local.idStore_id
    user_name = "Jeff"
    display_name = "Jeff"
    #provider = var.aws_provider
    name {
        given_name = "Jeff"
        family_name = "Okoli"
    }
    emails{
        value = var.jeff_email
    }
}

resource "aws_ssoadmin_permission_set" "use_s3" {
    name = "use-s3"
    instance_arn = local.Account_arn
    #provider = var.aws_provider
}

data "aws_iam_policy_document" "use_s3_policy" {
    statement {
        effect = "Allow"
        actions = [
            "secretsmanager:GetSecretValue"
        ]
        resources = [var.secret-arn]
    }
    statement {
       effect= "Allow"
       actions = [
        "ssm:StartSession"
         ]
       resources= [
        var.ec2-arn,
        "arn:aws:ssm:af-south-1:247670276320:document/SSM-SessionManagerRunShell",
        "arn:aws:ssm:af-south-1::document/AWS-StartPortForwardingSessionToRemoteHost"
      ]
    }
    statement {
       effect= "Allow"
       actions = [
        "ssm:TerminateSession",
        "ssm:ResumeSession"
      ]
      resources = ["*"]
    }
}



resource "aws_ssoadmin_permission_set_inline_policy" "use_s3_attachcment" {
    permission_set_arn = aws_ssoadmin_permission_set.use_s3.arn
    inline_policy = data.aws_iam_policy_document.use_s3_policy.json
    instance_arn = local.Account_arn
    #provider = var.aws_provider
}

variable "account"{
    type = string
    default = "247670276320"
}

resource "aws_ssoadmin_account_assignment" "jeff-account-permission" {
    instance_arn = local.Account_arn
    permission_set_arn = aws_ssoadmin_permission_set.use_s3.arn
    #provider = var.aws_provider

    principal_type = "USER"
    principal_id = aws_identitystore_user.jeff.user_id

    target_id = var.account
    target_type = "AWS_ACCOUNT"
}