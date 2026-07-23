# VPC dedicada, enxuta: 1 subnet pública (EC2) + 2 subnets privadas (RDS
# exige subnets em pelo menos 2 AZs no db_subnet_group, mesmo em Single-AZ).
# Sem NAT Gateway de propósito: nada na subnet privada precisa de saída
# para a internet (RDS não depende disso para funcionar), então economizamos
# o custo fixo do NAT (~US$32/mês) sem abrir mão de isolamento - o Aurora/RDS
# continua sem IP público, só acessível pelo Security Group da EC2.

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "${var.name_prefix}-vpc"
  }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-igw"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = var.public_subnet_cidr
  availability_zone       = var.azs[0]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.name_prefix}-public"
  }
}

resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnet_cidr
  availability_zone = var.azs[0]

  tags = {
    Name = "${var.name_prefix}-private-a"
  }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.private_subnet_cidr_b
  availability_zone = var.azs[1]

  tags = {
    Name = "${var.name_prefix}-private-b"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = {
    Name = "${var.name_prefix}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

# Subnets privadas ficam só com a route table default da VPC (tráfego local
# apenas, sem rota 0.0.0.0/0) - não precisam de uma route table dedicada
# nem de NAT, já que o RDS não faz chamadas de saída para a internet.
