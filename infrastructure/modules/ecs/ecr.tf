resource "aws_ecr_repository" "flynow-repo" {
    name = "flynow-repo-${var.env}"
    image_tag_mutability = "IMMUTABLE_WITH_EXCLUSION"

    image_tag_mutability_exclusion_filter {
      filter_type = "WILDCARD"
      filter = "buildcache"
    }
}