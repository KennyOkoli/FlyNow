resource "aws_cloudwatch_log_group" "flynow-log-group" {
    name = "flynow-logs-${var.env}"
}