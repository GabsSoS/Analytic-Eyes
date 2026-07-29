data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Sem key pair/SSH: a instancia fica em subnet privada, sem IP publico -
# acesso administrativo e so via SSM Session Manager (modules/iam ja tem a
# policy AmazonSSMManagedInstanceCore anexada), que autentica via IAM em vez
# de chave SSH.
resource "aws_instance" "this" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  iam_instance_profile   = var.instance_profile_name
  user_data              = file("${path.module}/user_data.sh")
  monitoring             = true

  root_block_device {
    volume_size = var.root_volume_size_gb
    volume_type = "gp3"
    encrypted   = true
  }

  # Exige IMDSv2 (token obrigatorio) - IMDSv1 e vulneravel a SSRF que
  # exfiltra as credenciais da instance profile.
  metadata_options {
    http_endpoint               = "enabled"
    http_tokens                 = "required"
    http_put_response_hop_limit = 1
  }

  tags = {
    Name = "${var.name_prefix}-ec2"
  }
}
