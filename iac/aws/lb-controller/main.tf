# ============================================
# Root Module: IRSA para AWS Load Balancer Controller
# Se ejecuta DESPUES de crear el cluster (data source del issuer OIDC) y se
# destruye ANTES que el cluster (misma razon: el data source lo requiere vivo).
# Estado propio: aws/lb-controller.tfstate (independiente del ensayo base).
# ============================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    tls = {
      source  = "hashicorp/tls"
      version = "~> 4.0"
    }
  }

  backend "s3" {
    bucket       = "sri-gitops-tfstate-640110193767"
    key          = "aws/lb-controller.tfstate"
    region       = "us-east-1"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region = var.region
}

# ============================================
# Data sources: el cluster ya existe (creado por iac/aws)
# ============================================
data "aws_eks_cluster" "this" {
  name = var.cluster_name
}

data "aws_caller_identity" "current" {}

locals {
  oidc_issuer_clean = replace(data.aws_eks_cluster.this.identity[0].oidc[0].issuer, "https://", "")
  oidc_provider_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${local.oidc_issuer_clean}"
}

# ============================================
# Trust policy: solo el ServiceAccount kube-system/aws-load-balancer-controller
# puede asumir este rol (federacion OIDC + condiciones sub/aud).
# ============================================
data "aws_iam_policy_document" "irsa_trust" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [local.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer_clean}:sub"
      values   = ["system:serviceaccount:kube-system:aws-load-balancer-controller"]
    }

    condition {
      test     = "StringEquals"
      variable = "${local.oidc_issuer_clean}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lb_controller" {
  name               = "${var.cluster_name}-alb-controller"
  assume_role_policy = data.aws_iam_policy_document.irsa_trust.json

  tags = merge(var.tags, {
    Name = "${var.cluster_name}-alb-controller"
  })
}

# ============================================
# Politica oficial del AWS Load Balancer Controller (v2.7.2).
# Se descarga con curl en la sesion (guion Fase 5); NO se versiona el JSON
# porque es artefacto upstream: la fuente de verdad es el repo del proyecto.
# ============================================
resource "aws_iam_policy" "lb_controller" {
  name   = "AWSLoadBalancerControllerIAMPolicy"
  policy = file("${path.module}/iam_policy.json")

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "lb_controller" {
  role       = aws_iam_role.lb_controller.name
  policy_arn = aws_iam_policy.lb_controller.arn
}
