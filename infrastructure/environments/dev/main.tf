module "vpc" {
    source = "../../modules/vpc"
} 

module "rds" {
    source = "../../modules/rds"   
    secret-manager-id = module.secrets.secret-id
    private_subnets = module.vpc.private-subnets
    az = module.vpc.azones
    vpc-id = module.vpc.vpc-id
    env = var.env
}

module "secrets" {
    source = "../../modules/secrets"
    env = var.env
}

module "github" {
    source = "../../modules/github"
    ecr-arn = module.ecs.ecr-arn
    frontend-ecs-arn = module.ecs.f-end-ecs
    backend-ecs-arn = module.ecs.b-end-ecs
    frontend-task-def-arn = module.ecs.f-end-task-def
    backend-task-def-arn = module.ecs.b-end-task-def
    env = var.env
}

module "ecs" {
    source = "../../modules/ecs"
    secrets = module.secrets.secret-manager-arn
    vpc = module.vpc.vpc-id
    db-sg = module.rds.db_sg
    private-subnets = module.vpc.private-subnets
    nacl = module.vpc.vpc-nacls
    public = module.vpc.public-cidr
    target-arn = module.ec2.target
    alb_sg = module.ec2.alb-sg
    db_name = module.rds.db_name
    db_username = module.rds.db_username
    db_password = module.rds.db_password
    env = var.env
    sabre-base-url = var.sabre-base-url
    sabre-client-id = var.sabre-client-id
    sabre-user-id = var.sabre_user_id
    use_mock = var.use_mock
    PCC = var.PCC
    secret-manager = module.secrets.secret-id
    db_host = module.rds.db_endpoint
}

module "ec2" {
    source = "../../modules/ec2"
    vpc_id = module.vpc.vpc-id
    public-cidr = module.vpc.public-cidr
    vpc-prv-subnets = module.vpc.private-subnets
    public-subnet = module.vpc.vpc-public-subnet
    ecs-sg-var = module.ecs.ecs-sg-frontend
    env = var.env
}
