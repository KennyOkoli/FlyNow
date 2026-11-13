variable "sabre-user-id" {}

variable "sabre-client-id" {}

variable "sabre-base-url" {}

variable "PCC" {}

variable "use_mock" {}


output "ecs-sg-frontend" {
    value = aws_security_group.task-sg-frontend.id
}

# output "ecs-sg-backend" {
#     value = aws_security_group.backend-sg.id
# }

output "f-end-task-def" {
    value = aws_ecs_task_definition.frontend-task-def.arn
}

output "b-end-task-def" {
    value = aws_ecs_task_definition.backend-task-def.arn
}

output "f-end-ecs" {
    value = aws_ecs_service.flynow-ecs-frontend.arn
}

output "b-end-ecs" {
    value = aws_ecs_service.backend-service.arn
}

output "ecr-arn" {
    value = aws_ecr_repository.flynow-repo.arn
}