output "target" {
    value = aws_alb_target_group.flynow-target-group.arn
}

output "alb-sg" {
    value = aws_security_group.alb-sg.id
}