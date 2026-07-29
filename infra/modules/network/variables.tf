variable "name_prefix" {
  description = "Prefixo usado no nome de todos os recursos de rede (ex: analytic-eyes-prod)."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR da VPC."
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidr" {
  description = "CIDR da subnet pública A (ALB + NAT Gateway)."
  type        = string
  default     = "10.20.1.0/24"
}

variable "public_subnet_cidr_b" {
  description = "CIDR da subnet pública B - o ALB exige subnets em >= 2 AZs mesmo com um unico target."
  type        = string
  default     = "10.20.4.0/24"
}

variable "private_subnet_cidr" {
  description = "CIDR da subnet privada (RDS)."
  type        = string
  default     = "10.20.2.0/24"
}

variable "private_subnet_cidr_b" {
  description = "CIDR da segunda subnet privada (RDS exige >= 2 AZs no db_subnet_group, mesmo em Single-AZ)."
  type        = string
  default     = "10.20.3.0/24"
}

variable "app_subnet_cidr" {
  description = "CIDR da subnet privada da EC2 (app) - sai para a internet via NAT Gateway, nunca recebe IP publico."
  type        = string
  default     = "10.20.5.0/24"
}

# --- AWS Network Firewall (opcional, desligado por padrao) ---

variable "enable_network_firewall" {
  description = "true = cria o AWS Network Firewall (~US$395/mes + processamento) inspecionando a saida da subnet de app. false (padrao) = trafego vai direto pro NAT Gateway, como hoje."
  type        = bool
  default     = false
}

variable "firewall_subnet_cidr" {
  description = "CIDR da subnet dedicada ao endpoint do Network Firewall (só usada se enable_network_firewall = true)."
  type        = string
  default     = "10.20.6.0/24"
}

variable "network_firewall_allowed_domains" {
  description = "Allowlist de dominios liberados na saida da subnet de app quando o Network Firewall esta habilitado (qualquer outro destino e derrubado). Ajuste conforme os Dockerfiles/user_data.sh passarem a usar outros registries/repositorios."
  type        = list(string)
  default = [
    # Docker Hub (pull de imagens base e da imagem etls:latest)
    ".docker.io",
    ".docker.com",
    # PyPI (pip install)
    ".pypi.org",
    "pypi.org",
    "files.pythonhosted.org",
    # npm (frontend)
    "registry.npmjs.org",
    # apt do host Ubuntu (user_data.sh) e das imagens base Debian/Ubuntu
    ".ubuntu.com",
    ".debian.org",
    # Instalacao do Docker Engine (user_data.sh)
    "download.docker.com",
    # Driver ODBC do SQL Server (etls/Dockerfile)
    "packages.microsoft.com",
    # git clone / deploy.sh
    ".github.com",
    "github.com",
    "codeload.github.com",
    ".githubusercontent.com",
    # APIs da AWS (Secrets Manager, S3, SSM, STS etc - sem VPC endpoints hoje)
    ".amazonaws.com",
  ]
}

variable "azs" {
  description = "Duas Availability Zones a usar (a primeira recebe a subnet pública + privada A, a segunda só a privada B)."
  type        = list(string)
}
