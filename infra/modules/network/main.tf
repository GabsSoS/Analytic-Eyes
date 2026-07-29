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

# Sem o firewall (padrao): rota direto pro NAT Gateway - comportamento
# identico ao de antes do modulo de Network Firewall existir. Com o
# firewall habilitado (var.enable_network_firewall = true), o trafego de
# saida passa primeiro pelo endpoint do firewall (que so libera os
# dominios em var.network_firewall_allowed_domains) antes de ir pro NAT.
resource "aws_route_table" "app" {
  vpc_id = aws_vpc.this.id

  dynamic "route" {
    for_each = var.enable_network_firewall ? [] : [1]
    content {
      cidr_block     = "0.0.0.0/0"
      nat_gateway_id = aws_nat_gateway.this.id
    }
  }

  dynamic "route" {
    for_each = var.enable_network_firewall ? [1] : []
    content {
      cidr_block      = "0.0.0.0/0"
      vpc_endpoint_id = local.firewall_endpoint_id
    }
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

# KMS key dedicada pro log group dos flow logs (key gerenciada pela AWS,
# tipo alias/aws/dynamodb, nao cobre CloudWatch Logs - precisa de key
# propria com policy liberando o servico de logs).
data "aws_caller_identity" "current_network" {}

data "aws_iam_policy_document" "cloudwatch_logs_kms" {
  statement {
    sid       = "AllowCloudWatchLogsUseOfKey"
    effect    = "Allow"
    actions   = ["kms:Encrypt*", "kms:Decrypt*", "kms:ReEncrypt*", "kms:GenerateDataKey*", "kms:Describe*"]
    resources = ["*"]

    principals {
      type        = "Service"
      identifiers = ["logs.${data.aws_region.network_current.name}.amazonaws.com"]
    }

    condition {
      test     = "ArnLike"
      variable = "kms:EncryptionContext:aws:logs:arn"
      values   = ["arn:aws:logs:${data.aws_region.network_current.name}:${data.aws_caller_identity.current_network.account_id}:log-group:*"]
    }
  }

  statement {
    sid       = "AllowAccountKeyAdministration"
    effect    = "Allow"
    actions   = ["kms:*"]
    resources = ["*"]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current_network.account_id}:root"]
    }
  }
}

data "aws_region" "network_current" {}

resource "aws_kms_key" "cloudwatch_logs" {
  description             = "Criptografa o log group dos VPC Flow Logs"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  policy                  = data.aws_iam_policy_document.cloudwatch_logs_kms.json

  tags = {
    Name = "${var.name_prefix}-cloudwatch-logs-kms"
  }
}

resource "aws_kms_alias" "cloudwatch_logs" {
  name          = "alias/${var.name_prefix}-cloudwatch-logs"
  target_key_id = aws_kms_key.cloudwatch_logs.key_id
}

# Flow logs da VPC (todo o tráfego, aceito e rejeitado) para o CloudWatch -
# rastro de auditoria mínimo esperado para um cliente regulado (FGC).
resource "aws_cloudwatch_log_group" "vpc_flow_log" {
  name              = "/aws/vpc/${var.name_prefix}-flow-logs"
  retention_in_days = 90
  kms_key_id        = aws_kms_key.cloudwatch_logs.arn

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

# --- AWS Network Firewall (desligado por padrao - var.enable_network_firewall) ---
#
# Inspeciona o trafego de saida da subnet de app (Docker Hub/apt/pip/npm)
# antes de chegar no NAT Gateway, liberando so os dominios em
# var.network_firewall_allowed_domains (allowlist) - qualquer outro destino
# e derrubado. Fica todo pronto/configurado mas com custo real (~US$395/mes
# + processamento) - so e criado de fato se var.enable_network_firewall for
# true. Com a variavel no default (false), nao muda nada na rota atual
# (subnet de app continua indo direto pro NAT, ver aws_route_table.app acima).
#
# Antes de habilitar em produção: rode `terraform plan` com atenção e
# valide os domínios permitidos (a lista abaixo cobre o que os
# Dockerfiles/user_data.sh usam hoje - Docker Hub, PyPI, npm, apt do
# Ubuntu/Debian, GitHub, endpoints da AWS). Domínio faltando na lista =
# download bloqueado, o build da aplicação pode quebrar.

resource "aws_subnet" "firewall" {
  count             = var.enable_network_firewall ? 1 : 0
  vpc_id            = aws_vpc.this.id
  cidr_block        = var.firewall_subnet_cidr
  availability_zone = var.azs[0]

  tags = {
    Name = "${var.name_prefix}-firewall"
  }
}

resource "aws_networkfirewall_rule_group" "egress_allowlist" {
  count    = var.enable_network_firewall ? 1 : 0
  name     = "${var.name_prefix}-egress-allowlist"
  type     = "STATEFUL"
  capacity = 200

  rule_group {
    rules_source {
      rules_source_list {
        generated_rules_type = "ALLOWLIST"
        target_types         = ["TLS_SNI", "HTTP_HOST"]
        targets              = var.network_firewall_allowed_domains
      }
    }

    # Rule groups baseados em lista de dominio (HTTP_HOST/TLS_SNI) exigem
    # avaliacao em ordem estrita - e um requisito da API do Network
    # Firewall, nao uma escolha nossa.
    stateful_rule_options {
      rule_order = "STRICT_ORDER"
    }
  }

  tags = {
    Name = "${var.name_prefix}-egress-allowlist"
  }
}

resource "aws_networkfirewall_firewall_policy" "this" {
  count = var.enable_network_firewall ? 1 : 0
  name  = "${var.name_prefix}-fw-policy"

  firewall_policy {
    # Encaminha todo trafego (inclusive fragmentos) pro stateful engine -
    # e a regra de dominio (acima) que decide passar ou derrubar.
    stateless_default_actions          = ["aws:forward_to_sfe"]
    stateless_fragment_default_actions = ["aws:forward_to_sfe"]

    # STRICT_ORDER exige stateful_default_actions "_strict" (nao
    # "_established") - derruba por padrao qualquer trafego que nao bateu
    # em nenhuma regra da allowlist.
    stateful_default_actions = ["aws:drop_strict"]

    stateful_engine_options {
      rule_order = "STRICT_ORDER"
    }

    stateful_rule_group_reference {
      resource_arn = aws_networkfirewall_rule_group.egress_allowlist[0].arn
      priority     = 1
    }
  }

  tags = {
    Name = "${var.name_prefix}-fw-policy"
  }
}

resource "aws_networkfirewall_firewall" "this" {
  count               = var.enable_network_firewall ? 1 : 0
  name                = "${var.name_prefix}-fw"
  vpc_id              = aws_vpc.this.id
  firewall_policy_arn = aws_networkfirewall_firewall_policy.this[0].arn

  subnet_mapping {
    subnet_id = aws_subnet.firewall[0].id
  }

  tags = {
    Name = "${var.name_prefix}-fw"
  }
}

# ID do endpoint VPC do firewall na AZ da subnet de app - e o alvo da rota
# 0.0.0.0/0 da aws_route_table.app quando o firewall esta habilitado.
locals {
  firewall_endpoint_id = var.enable_network_firewall ? [
    for s in aws_networkfirewall_firewall.this[0].firewall_status[0].sync_states :
    s.attachment[0].endpoint_id
    if s.availability_zone == var.azs[0]
  ][0] : null
}

# Subnet do firewall sai direto pro NAT (depois de inspecionado, o trafego
# segue o mesmo caminho de antes: NAT Gateway -> Internet Gateway).
resource "aws_route_table" "firewall" {
  count  = var.enable_network_firewall ? 1 : 0
  vpc_id = aws_vpc.this.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.this.id
  }

  tags = {
    Name = "${var.name_prefix}-firewall-rt"
  }
}

resource "aws_route_table_association" "firewall" {
  count          = var.enable_network_firewall ? 1 : 0
  subnet_id      = aws_subnet.firewall[0].id
  route_table_id = aws_route_table.firewall[0].id
}
