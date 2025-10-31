terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# GitHub OIDC Provider
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com"
  ]

  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1",
    "1c58a3a8518e8759bf075b76b750d4f2df264fcd"
  ]

  tags = merge(
    var.tags,
    {
      Name = "github-actions-oidc"
    }
  )
}

# IAM Role for GitHub Actions
resource "aws_iam_role" "github_actions" {
  name               = var.role_name
  description        = "Role for GitHub Actions via OIDC"
  assume_role_policy = data.aws_iam_policy_document.github_actions_assume.json

  max_session_duration = var.max_session_duration

  tags = merge(
    var.tags,
    {
      Name = var.role_name
    }
  )
}

# Trust policy for GitHub OIDC
data "aws_iam_policy_document" "github_actions_assume" {
  statement {
    effect = "Allow"

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    actions = ["sts:AssumeRoleWithWebIdentity"]

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = var.github_repo_subjects
    }
  }
}

# Attach custom policies
resource "aws_iam_role_policy_attachment" "custom" {
  count      = length(var.policy_arns)
  role       = aws_iam_role.github_actions.name
  policy_arn = var.policy_arns[count.index]
}

# Attach inline policies
resource "aws_iam_role_policy" "inline" {
  count  = length(var.inline_policies)
  name   = var.inline_policies[count.index].name
  role   = aws_iam_role.github_actions.id
  policy = var.inline_policies[count.index].policy
}
