output "secret-manager-arn" {
    value = aws_secretsmanager_secret.flynow-db-secrets.arn
}

output "secret-id" {
    value = aws_secretsmanager_secret.flynow-db-secrets.id
}