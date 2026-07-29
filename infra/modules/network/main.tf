# VPC dedicada: 2 subnets publicas (ALB, que exige >= 2 AZs mesmo com 1 so
# target) + 2 subnets privadas de RDS (exige >= 2 AZs no db_subnet_group,
# mesmo em Single-AZ) + 1 subnet privada de app (EC2, sem IP publico - sai
# pra internet via NAT Gateway pra poder puxar imagens Docker/pip/npm).
# O RDS nao usa o NAT (nunca precisa de saida pra internet), so a subnet de
# app tem rota 0.0.0.0/0 via NAT.

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

# A AWS cria um security group "default" em toda VPC nova, sem nenhum
# recurso anexado a ele, mas com uma regra de ingress permissiva (todo
# trafego entre membros do proprio SG) - gerencia-lo aqui so pra zerar as
# regras, satisfazendo o check de "SG default nao deve ser usado/permissivo"
# sem afetar nenhum recurso (nada usa este SG, tudo usa modules/security).
resource "aws_default_security_group" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-default-sg-locked"
  }
}

resource "aws_subnet" "public" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.public_subnet_cidr
  availability_zone = var.azs[0]

  # Desligado de proposito: nada nesta subnet precisa de IP publico proprio
  # (o ALB usa IPs geridos pela AWS, o NAT Gateway usa o EIP dedicado dele).
  map_public_ip_on_launch = false

  tags = {
    Name = "${var.name_prefix}-public-a"
  }
}

# So existe pra satisfazer o requisito do ALB de subnets em >= 2 AZs -
# nenhum outro recurso e criado nela.
resource "aws_subnet" "public_b" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.public_subnet_cidr_b
  availability_zone = var.azs[1]

  map_public_ip_on_launch = false

  tags = {
    Name = "${var.name_prefix}-public-b"
  }
}

# Subnet privada da EC2 (app) - sem IP publico, sai pra internet (Docker Hub,
# apt, pip, npm) via NAT Gateway. Separada das subnets privadas do RDS pra
# nao misturar (RDS nunca precisa de rota 0.0.0.0/0).
resource "aws_subnet" "app" {
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.app_subnet_cidr
  availability_zone = var.azs[0]

  tags = {
    Name = "${var.name_prefix}-app"
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

resource "aws_route_table_association" "public_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

# NAT Gateway (na subnet publica A) - unica saida pra internet da subnet de
# app. Custo fixo (~US$32/mes + processamento) aceito de proposito pra
# poder tirar o IP publico da EC2 (ver infra/README.md).
resource "aws_eip" "nat" {
  domain = "vpc"

  tags = {
    Name = "${var.name_prefix}-nat-eip"
  }
}

resource "aws_nat_gateway" "this" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public.id

  tags = {
    Name = "${var.name_prefix}-nat"
  }

  depends_on = [aws_internet_gateway.this]
}

resource "aws_route_table" "app" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.this.id
  }

  tags = {
    Name = "${var.name_prefix}-app-rt"
  }
}

resource "aws_route_table_association" "app" {
  subnet_id      = aws_subnet.app.id
  route_table_id = aws_route_table.app.id
}

# Subnets privadas do RDS ficam só com a route table default da VPC (tráfego
# local apenas, sem rota 0.0.0.0/0) - não precisam de NAT, já que o RDS não
# faz chamadas de saída para a internet.

# Flow logs da VPC (todo o tráfego, aceito e rejeitado) para o CloudWatch -
# rastro de auditoria mínimo esperado para um cliente regulado (FGC).
resource "aws_cloudwatch_log_group" "vpc_flow_log" {
  name              = "/aws/vpc/${var.name_prefix}-flow-logs"
  retention_in_days = 90

  tags = {
    Name = "${var.name_prefix}-vpc-flow-log-group"
  }
}

data "aws_iam_policy_document" "flow_log_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["vpc-flow-logs.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "flow_log" {
  name               = "${var.name_prefix}-vpc-flow-log-role"
  assume_role_policy = data.aws_iam_policy_document.flow_log_assume_role.json

  tags = {
    Name = "${var.name_prefix}-vpc-flow-log-role"
  }
}

data "aws_iam_policy_document" "flow_log_permissions" {
  statement {
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
    ]
    resources = ["${aws_cloudwatch_log_group.vpc_flow_log.arn}:*"]
  }
}

resource "aws_iam_role_policy" "flow_log" {
  name   = "${var.name_prefix}-vpc-flow-log-policy"
  role   = aws_iam_role.flow_log.id
  policy = data.aws_iam_policy_document.flow_log_permissions.json
}

resource "aws_flow_log" "this" {
  iam_role_arn    = aws_iam_role.flow_log.arn
  log_destination = aws_cloudwatch_log_group.vpc_flow_log.arn
  traffic_type    = "ALL"
  vpc_id          = aws_vpc.this.id

  tags = {
    Name = "${var.name_prefix}-vpc-flow-log"
  }
}
