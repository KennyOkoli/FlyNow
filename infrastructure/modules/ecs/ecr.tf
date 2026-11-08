resource "aws_ecr_repository" "flynow-repo" {
    name = "flynow-repo"
    image_tag_mutability = "IMMUTABLE"
}