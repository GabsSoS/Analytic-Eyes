# Certificado ACM com validacao via DNS (nao via HTTP-01 como o Certbot) -
# nao depende de nenhuma porta publica na aplicacao pra ser emitido/renovado.
# Renovacao e automatica enquanto os registros de validacao continuarem
# publicados no DNS.
resource "aws_acm_certificate" "this" {
  domain_name               = var.domain_name
  subject_alternative_names = var.domain_alt_names
  validation_method         = "DNS"

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Name = "${var.name_prefix}-cert"
  }
}

# O DNS deste projeto não é gerenciado pelo Terraform (ver infra/README.md) -
# por isso este apply precisa ser feito em duas etapas: primeiro só o
# certificado (`terraform apply -target=module.alb.aws_acm_certificate.this`),
# depois adicionar os registros do output `acm_validation_records` no seu
# provedor de DNS, e só então rodar o `terraform apply` completo (que fica
# esperando a validação terminar antes de criar o listener HTTPS).
resource "aws_acm_certificate_validation" "this" {
  certificate_arn = aws_acm_certificate.this.arn
}

resource "aws_lb" "this" {
  name               = "${var.name_prefix}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [var.alb_security_group_id]
  subnets            = var.public_subnet_ids

  tags = {
    Name = "${var.name_prefix}-alb"
  }
}

resource "aws_lb_target_group" "app" {
  name        = "${var.name_prefix}-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = var.vpc_id
  target_type = "instance"

  health_check {
    path                = "/health/"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
  }

  tags = {
    Name = "${var.name_prefix}-tg"
  }
}

resource "aws_lb_target_group_attachment" "app" {
  target_group_arn = aws_lb_target_group.app.arn
  target_id        = var.instance_id
  port             = 80
}

# HTTP so redireciona pra HTTPS - nunca serve conteudo (o ingress do SG do
# ALB ja restringe as duas portas aos CIDRs internos, ver modules/security).
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.this.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate_validation.this.certificate_arn

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}
