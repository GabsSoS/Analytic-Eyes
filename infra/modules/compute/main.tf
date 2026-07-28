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

resource "aws_key_pair" "this" {
  key_name   = "${var.name_prefix}-key"
  public_key = var.ssh_public_key

  tags = {
    Name = "${var.name_prefix}-key"
  }
}

resource "aws_instance" "this" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [var.security_group_id]
  key_name               = aws_key_pair.this.key_name
  iam_instance_profile   = var.instance_profile_name
  user_data              = file("${path.module}/user_data.sh")
  monitoring             = true

  root_block_device {
    volume_size = var.root_volume_size_gb
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name = "${var.name_prefix}-ec2"
  }
}

# IP fixo - sem isso, o IP publico muda a cada stop/start (ruim pra apontar
# DNS). Custo: gratis enquanto associado a uma instancia rodando; so cobra
# se ficar "sobrando" sem instancia (mais um motivo pra sempre destruir
# tudo junto via terraform destroy, nunca so parar a EC2 e deixar o EIP solto).
resource "aws_eip" "this" {
  instance = aws_instance.this.id
  domain   = "vpc"

  tags = {
    Name = "${var.name_prefix}-eip"
  }
}
