provider "aws" {
  region = "us-east-1"
}

resource "aws_vpc" "prod_vpc" {
  cidr_block = "10.0.0.0/16"
  tags = { Name = "autojobapply-prod-vpc" }
}

resource "aws_security_group" "api_sg" {
  name        = "api-security-group"
  vpc_id      = aws_vpc.prod_vpc.id
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
