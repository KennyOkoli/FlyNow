# Remote s3
resource "aws_s3_bucket" "flynow_dev_state" {
    bucket = "flynow-dev-tfstate"
}

resource "aws_s3_bucket" "flynow_prod_state" {
    bucket = "flynow-prod-tfstate"
}

resource "aws_s3_bucket_versioning" "flynow-prod-version" {
    bucket = aws_s3_bucket.flynow_prod_state.id
    versioning_configuration {
      status = "Enabled"
    }
}

resource "aws_s3_bucket_lifecycle_configuration" "flynow-prod-lifecycle" {
    bucket = aws_s3_bucket.flynow_prod_state.id

    rule{
        id = "Delete < 3 old versions"
        status = "Enabled"
        noncurrent_version_expiration {
          noncurrent_days = 6
        }
    }
}


#-------------------------- Creating github admin role -----------------------------
resource "aws_iam_openid_connect_provider"  "github" {
    url = "https://token.actions.githubusercontent.com"
    client_id_list = ["sts.amazonaws.com"]
}

data "aws_iam_policy_document" "github-trust-policy" {
    statement {
        effect = "Allow"
        principals {
            type = "Federated"
            identifiers = [aws_iam_openid_connect_provider.github.arn]
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
        }/*
        condition {
            test = "StringLike"
            variable = "token.actions.githubusercontent.com:job_workflow_ref"
            values = [
                "KennyOkoli/FlyNow/.github/workflows/deploy_cloud_dev.yaml@*"]
                #"KennyOkoli/FlyNow/.github/workflows/deploy_cloud_prod.yaml@*"
        }*/
    }
}

resource "aws_iam_role" "github-role" {
    name = "github-admin-role"
    assume_role_policy = data.aws_iam_policy_document.github-trust-policy.json
}

resource "aws_iam_role_policy_attachment" "github-role-policy" {
    role = aws_iam_role.github-role.id
    policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}