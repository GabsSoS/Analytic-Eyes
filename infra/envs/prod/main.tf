module "network" {
  source = "../../modules/network"

  name_prefix             = var.name_prefix
  azs                     = var.azs
  enable_network_firewall = var.enable_network_firewall
}

module "security" {
  source = "../../modules/security"

  name_prefix       = var.name_prefix
  vpc_id            = module.network.vpc_id
  app_allowed_cidrs = var.app_allowed_cidrs
}

module "s3" {
  source = "../../modules/s3"

  bucket_name = var.s3_bucket_name
}

module "rds" {
  source = "../../modules/rds"

  name_prefix         = var.name_prefix
  private_subnet_ids  = module.network.private_subnet_ids
  security_group_id   = module.security.rds_security_group_id
  instance_class      = var.db_instance_class
  db_name             = var.db_name
  master_username     = var.db_master_username
  skip_final_snapshot = var.db_skip_final_snapshot
}

module "iam" {
  source = "../../modules/iam"

  name_prefix   = var.name_prefix
  db_secret_arn = module.rds.secret_arn
  s3_bucket_arn = module.s3.bucket_arn
}

module "compute" {
  source = "../../modules/compute"

  name_prefix           = var.name_prefix
  subnet_id             = module.network.app_subnet_id
  security_group_id     = module.security.ec2_security_group_id
  instance_profile_name = module.iam.instance_profile_name
  instance_type         = var.ec2_instance_type
}

module "alb" {
  source = "../../modules/alb"

  name_prefix             = var.name_prefix
  vpc_id                  = module.network.vpc_id
  public_subnet_ids       = module.network.public_subnet_ids
  alb_security_group_id   = module.security.alb_security_group_id
  instance_id             = module.compute.instance_id
  domain_name             = var.domain_name
  domain_alt_names        = var.domain_alt_names
  alb_deletion_protection = var.alb_deletion_protection
}

# AWS Shield Advanced (desligado por padrao - var.enable_shield_advanced).
# So cria de fato se a conta ja tiver assinatura ATIVA do Shield Advanced -
# sem isso, o apply falha (a API rejeita aws_shield_protection sem
# assinatura). Assinar e uma decisao comercial (US$3.000/mes, 1 ano de
# compromisso) feita manualmente no Console/CLI, nunca via Terraform.
resource "aws_shield_protection" "alb" {
  count        = var.enable_shield_advanced ? 1 : 0
  name         = "${var.name_prefix}-alb-shield"
  resource_arn = module.alb.alb_arn
}

resource "aws_shield_protection" "nat_eip" {
  count        = var.enable_shield_advanced ? 1 : 0
  name         = "${var.name_prefix}-nat-eip-shield"
  resource_arn = module.network.nat_eip_arn
}

# Detecta acesso nao intencional (publico/cross-account) em recursos IAM/S3
# desta conta. Gratis, escopo de conta unica (nao precisa de AWS Organizations).
resource "aws_accessanalyzer_analyzer" "account" {
  analyzer_name = "${var.name_prefix}-access-analyzer"
  type          = "ACCOUNT"

  tags = {
    Name = "${var.name_prefix}-access-analyzer"
  }
}
