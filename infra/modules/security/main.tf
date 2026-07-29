# SG do ALB: unico ponto de entrada publico da aplicacao. Restrito aos CIDRs
# de app_allowed_cidrs (escritorio/VPN) - a app e de uso interno, nunca deve
# aceitar 0.0.0.0/0. A porta 80 so existe pra redirecionar pra 443 (o
# certificado agora e emitido via ACM com validacao DNS, entao nao precisa
# mais ficar aberta pro desafio HTTP-01 do Let's Encrypt).
resource "aws_security_group" "alb" {
  name        = "${var.name_prefix}-alb-sg"
  description = "ALB - HTTP/HTTPS restritos aos CIDRs internos da aplicacao"
  vpc_id      = var.vpc_id

  ingress {
    description = "HTTP (redirect pra HTTPS)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = var.app_allowed_cidrs
  }

  ingress {
    description = "HTTPS (uso interno - IPs da empresa/VPN)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.app_allowed_cidrs
  }

  egress {
    description = "Trafego pro SG da EC2 (target group do ALB)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-alb-sg"
  }
}

# SG da EC2: sem nenhuma porta publica - a instancia nao tem IP publico e so
# recebe trafego do ALB (porta 80, HTTP puro - o TLS ja foi terminado no
# ALB). Acesso administrativo e via SSM Session Manager (modules/iam), que
# nao depende de nenhuma porta de ingress aqui.
resource "aws_security_group" "ec2" {
  name        = "${var.name_prefix}-ec2-sg"
  description = "EC2 do backend/nginx - so aceita trafego do ALB"
  vpc_id      = var.vpc_id

  ingress {
    description     = "HTTP a partir do ALB"
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    description = "Todo trafego de saida permitido (NAT Gateway pra internet + RDS)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-ec2-sg"
  }
}

# SG do RDS: só aceita Postgres (5432) vindo do SG da EC2 - nunca da internet.
resource "aws_security_group" "rds" {
  name        = "${var.name_prefix}-rds-sg"
  description = "RDS PostgreSQL - acesso somente do SG da EC2"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL a partir da EC2"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
  }

  egress {
    description = "Todo trafego de saida permitido (RDS so inicia conexoes, nunca recebe)"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-rds-sg"
  }
}
