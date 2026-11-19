terraform {
  required_providers {
     aws = {
        source = "hashicorp/aws"
        version = "~>6.0"
    }
  }
}

data "aws_availability_zones" "africa_az"{
    state = "available"
}

resource "aws_vpc" "FlyNow" {
    cidr_block = var.cidr_block
    enable_dns_hostnames = true
    enable_dns_support = true
}

resource "aws_subnet" "fl_public_subnet"{
    count = 2
    vpc_id = aws_vpc.FlyNow.id
    cidr_block = "32.0.${count.index}.0/24"
    availability_zone = data.aws_availability_zones.africa_az.names[count.index]
    map_public_ip_on_launch = true

    tags ={
        name = var.public_subnet_tags[count.index]
    }
}

resource "aws_internet_gateway" "fl_gateway"{
    vpc_id = aws_vpc.FlyNow.id
}

resource "aws_route_table" "fl_public_route"{
    vpc_id = aws_vpc.FlyNow.id
    route {
        cidr_block = var.public_ip
        gateway_id = aws_internet_gateway.fl_gateway.id
    }
}

resource "aws_network_acl" "fl_public_acl"{
    vpc_id = aws_vpc.FlyNow.id
    subnet_ids = aws_subnet.fl_public_subnet[*].id
    ingress{
        rule_no = 1
        protocol = "tcp"
        cidr_block = var.public_ip
        action = "allow"
        from_port = 0
        to_port = 65535
    }
    egress{
        rule_no = 1
        protocol = "tcp"
        cidr_block = var.public_ip
        action = "allow"
        from_port = 0
        to_port = 65535
    }   
}

resource "aws_route_table_association" "fl_route_public_subnet" {
    count = 2
    route_table_id = aws_route_table.fl_public_route.id
    subnet_id = aws_subnet.fl_public_subnet[count.index].id
}

resource "aws_network_acl_association" "fl_nacl_association" {
    count = 2
    network_acl_id = aws_network_acl.fl_public_acl.id
    subnet_id = aws_subnet.fl_public_subnet[count.index].id
}

# ---------------------------- Private Resources ---------------------------
resource "aws_subnet" "fl_private_subnet"{
    count = 2
    vpc_id = aws_vpc.FlyNow.id
    cidr_block = "32.0.${count.index + 100}.0/24"
    availability_zone = data.aws_availability_zones.africa_az.names[count.index]

    tags ={
        name = var.private_subnets_tags[count.index]
    }
}

resource "aws_eip" "fl_eip" {
    count = 2
}

resource "aws_nat_gateway" "fl_nat_gateway" {
    count = 2
    allocation_id = aws_eip.fl_eip[count.index].id
    subnet_id = aws_subnet.fl_public_subnet[count.index].id

    tags ={
        name = var.nat_tags[count.index]
    }
}

resource "aws_route_table" "fl_private-route"{
    count = 2
    vpc_id = aws_vpc.FlyNow.id
    route{
        cidr_block = var.public_ip
        nat_gateway_id = aws_nat_gateway.fl_nat_gateway[count.index].id
    }
}

resource "aws_network_acl" "fl_acl_private" {
    vpc_id = aws_vpc.FlyNow.id
    subnet_ids = aws_subnet.fl_private_subnet[*].id
    ingress {
        rule_no = 1
        cidr_block = var.public_ip
        action = "allow"
        protocol = "tcp"
        from_port = 0
        to_port = 65535
    }
    egress {
        rule_no = 1
        cidr_block = var.public_ip
        action = "allow"
        protocol = "tcp"
        from_port = 0
        to_port = 65535
    }
}

resource "aws_route_table_association" "route_private_subnet" {
    count = 2
    route_table_id = aws_route_table.fl_private-route[count.index].id
    subnet_id = aws_subnet.fl_private_subnet[count.index].id
}

resource "aws_network_acl_association" "nacls_private"{
    count = 2
    network_acl_id = aws_network_acl.fl_acl_private.id
    subnet_id = aws_subnet.fl_private_subnet[count.index].id
}
