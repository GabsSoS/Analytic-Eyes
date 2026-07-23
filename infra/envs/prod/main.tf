module "network" {
  source = "../../modules/network"

  name_prefix = var.name_prefix
  azs         = var.azs
}

module "security" {
  source = "../../modules/security"

  name_prefix       = var.name_prefix
  vpc_id            = module.network.vpc_id
  ssh_allowed_cidr  = var.ssh_allowed_cidr
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
  subnet_id             = module.network.public_subnet_id
  security_group_id     = module.security.ec2_security_group_id
  instance_profile_name = module.iam.instance_profile_name
  instance_type         = var.ec2_instance_type
  ssh_public_key        = var.ssh_public_key
}
