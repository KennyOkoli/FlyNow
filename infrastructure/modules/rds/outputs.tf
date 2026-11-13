output "db_sg"{
    value = aws_security_group.db_sg.id
}
/*
output "ec2_arn" {
    value = aws_instance.db_ec2_jumphost.arn
}
*/
output "db_name" {
    value = aws_db_instance.flynow_db.db_name
}

output "db_username" {
    value = local.db_credentials.username
}

output "db_password" {
    value = local.db_credentials.password
}

output "db_endpoint" {
    value = aws_db_instance.flynow_db.address
}