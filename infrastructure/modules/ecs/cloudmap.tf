resource "aws_service_discovery_http_namespace" "flynow-cloudmap"{
    name = "flynow_backend.local"
}

resource "aws_service_discovery_http_namespace" "flynow-cloudmap-fn"{
    name = "flynow_backend_${var.env}.local"
}