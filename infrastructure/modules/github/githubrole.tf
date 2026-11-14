# Configure the trust policy
# Reference the appropraite task definition and ecs service arns
data "aws_iam_openid_connect_provider" "github-id" {
    arn = "arn:aws:iam::247670276320:oidc-provider/token.actions.githubusercontent.com"
}

locals {
  oidc_arn = data.aws_iam_openid_connect_provider.github-id.arn
}


data "aws_iam_policy_document" "oidc_policy_doc" {
    statement {
        effect = "Allow"
        principals {
            type = "Federated"
            identifiers = [local.oidc_arn]
        }
        actions = ["sts:AssumeRoleWithWebIdentity"]
        condition {
            test = "StringEquals"
            variable = "token.actions.githubusercontent.com:aud"
            values = ["sts.amazonaws.com"]
        }
        condition {
            test = "StringLike"
            variable = "token.actions.githubusercontent.com:sub"
            values = ["repo:KennyOkoli@334668853/FlyNow@1446781227:*"] 
        }
        
    }
}

variable "env" {}

resource "aws_iam_role" "github-role" {
    name = "github-role-${var.env}"
    assume_role_policy = data.aws_iam_policy_document.oidc_policy_doc.json
}

data "aws_iam_policy_document" "github-policy-doc" {
    statement {
      effect = "Allow"
      actions = [
        "ecr:GetAuthorizationToken"
      ]
      resources = ["*"] # Similar to ecr login
    }
    statement {
      effect = "Allow"
      actions = [
        "ecr:BatchCheckLayerAvailability",
        "ecr:CompleteLayerUpload",
        "ecr:InitiateLayerUpload",
        "ecr:PutImage",
        "ecr:UploadLayerPart",
        "ecr:BatchGetImage"
      ]
      resources = [var.ecr-arn]
    }
    statement {
      effect = "Allow"
      actions = [
        "ecs:RegisterTaskDefinition",
        "ecs:DescribeTaskDefinition",
        "ecs:UpdateService",
        "ecs:DescribeServices"     
      ]
      resources = [var.frontend-ecs-arn, var.backend-ecs-arn, var.frontend-task-def-arn, var.backend-task-def-arn]
    }
    statement {
      effect = "Allow"
      actions = ["iam:PassRole"]
      resources = [
        var.task-role,
        var.task-def-role
      ] 
    }
}

variable "task-role" {}
variable "task-def-role" {}
resource "aws_iam_role_policy" "github-role-attachment" {
   role = aws_iam_role.github-role.id
   policy = data.aws_iam_policy_document.github-policy-doc.json
}