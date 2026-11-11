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

variable "sabre_user_id" {
    default = "V1:j5wo3fibee9oowp3:DEVCENTER:EXT"
}

variable "sabre-client-id" {
    default = "V1:j5wo3fibee9oowp3:DEVCENTER:EXT"
}

variable "sabre-base-url" {
    default = "https://api.cert.platform.sabre.com/v2/auth/token"
}

variable "PCC" {
    default = "S5OM"
}

variable "use_mock" {
    default = "false"
}