# SG da EC2: 22 (SSH, restrito ao seu IP), 80/443 (HTTP/HTTPS, público -
# é o site + a validação HTTP-01 do certbot).
resource "aws_security_group" "ec2" {
  name        = "${var.name_prefix}-ec2-sg"
  description = "EC2 do backend/nginx - SSH restrito, HTTP/HTTPS publico"
  vpc_id      = var.vpc_id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_allowed_cidr]
  }

  # Porta 80 continua publica de proposito: o Certbot usa o desafio HTTP-01
  # do Let's Encrypt para emitir/renovar o certificado, e isso exige que os
  # servidores da Let's Encrypt (IPs arbitrarios, fora do nosso controle)
  # consigam alcancar essa porta. O nginx so responde a validacao do
  # certificado e redireciona pra HTTPS aqui - nao serve conteudo real da
  # aplicacao em texto plano, entao nao ha dado sensivel exposto.
  ingress {
    description = "HTTP (so validacao Lets Encrypt + redirect pra HTTPS)"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Aqui sim fica restrito: e onde a aplicacao de verdade e servida.
  ingress {
    description = "HTTPS (uso interno - IPs da empresa/VPN)"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.app_allowed_cidrs
  }

  egress {
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
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.name_prefix}-rds-sg"
  }
}
