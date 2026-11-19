terraform {
   required_providers {
      aws = {
         source = "hashicorp/aws"
         version = "~>6"
      }
   }
}

provider "aws" {
    region = "af-south-1"
}