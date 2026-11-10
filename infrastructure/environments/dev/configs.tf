terraform {
    backend "s3" {
        bucket = "flynow-dev-tfstate"
        key = "dev/terraform.tfstate"
        region = "af-south-1"
      }
   required_providers{
      aws = {
          source = "hashicorp/aws"
          version = "~>6"
      }
   }
}

provider "aws" {
    region = "af-south-1"
}

provider "aws" {
    alias = "sso-region"
    region = "us-east-1"
}

variable "env" {
    default = "dev"
}