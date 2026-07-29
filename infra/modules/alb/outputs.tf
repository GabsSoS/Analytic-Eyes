output "alb_dns_name" {
  description = "Aponte um CNAME/ALIAS do seu domínio para este endereço (substitui o antigo A record pro IP da EC2)."
  value       = aws_lb.this.dns_name
}

output "alb_zone_id" {
  description = "Hosted zone ID do ALB - necessário se o seu provedor de DNS suportar ALIAS/ANAME (ex: Route53)."
  value       = aws_lb.this.zone_id
}

output "acm_certificate_arn" {
  description = "ARN do certificado ACM (referenciado pelo listener HTTPS)."
  value       = aws_acm_certificate.this.arn
}

output "acm_validation_records" {
  description = "Registros CNAME que precisam existir no seu provedor de DNS para o ACM validar o certificado (ver infra/README.md)."
  value = [
    for o in aws_acm_certificate.this.domain_validation_options : {
      name  = o.resource_record_name
      type  = o.resource_record_type
      value = o.resource_record_value
    }
  ]
}
