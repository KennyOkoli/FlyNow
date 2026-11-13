resource "aws_ecr_repository" "flynow-repo" {
    name = "flynow-repo-${var.env}"
    image_tag_mutability = "IMMUTABLE"
}