terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

# Organization Policy: Disable Service Account Key Creation
resource "google_org_policy_policy" "disable_sa_key_creation" {
  count  = var.organization_id != "" ? 1 : 0
  name   = "${var.organization_id}/policies/iam.disableServiceAccountKeyCreation"
  parent = var.organization_id

  spec {
    rules {
      enforce = "TRUE"
    }
  }
}

# Organization Policy: Disable Service Account Key Upload
resource "google_org_policy_policy" "disable_sa_key_upload" {
  count  = var.organization_id != "" ? 1 : 0
  name   = "${var.organization_id}/policies/iam.managed.disableServiceAccountKeyUpload"
  parent = var.organization_id

  spec {
    rules {
      enforce = "TRUE"
    }
  }
}

# Organization Policy: Disable Service Account API Key Creation
resource "google_org_policy_policy" "disable_sa_api_key_creation" {
  count  = var.organization_id != "" ? 1 : 0
  name   = "${var.organization_id}/policies/iam.managed.disableServiceAccountApiKeyCreation"
  parent = var.organization_id

  spec {
    rules {
      enforce = "TRUE"
    }
  }
}

# Organization Policy: Storage Public Access Prevention
resource "google_org_policy_policy" "storage_public_access_prevention" {
  count  = var.organization_id != "" ? 1 : 0
  name   = "${var.organization_id}/policies/storage.publicAccessPrevention"
  parent = var.organization_id

  spec {
    rules {
      values {
        allowed_values = ["enforced"]
      }
    }
  }
}

# Optional: Disable default service account creation
resource "google_org_policy_policy" "disable_default_sa_creation" {
  count  = var.organization_id != "" && var.disable_default_sa_creation ? 1 : 0
  name   = "${var.organization_id}/policies/iam.automaticIamGrantsForDefaultServiceAccounts"
  parent = var.organization_id

  spec {
    rules {
      enforce = "TRUE"
    }
  }
}

# Optional: Restrict service account privilege escalation
resource "google_org_policy_policy" "restrict_sa_privilege_escalation" {
  count  = var.organization_id != "" && var.harden_service_accounts ? 1 : 0
  name   = "${var.organization_id}/policies/iam.serviceAccountKeyExpiryHours"
  parent = var.organization_id

  spec {
    rules {
      values {
        allowed_values = ["2160"]  # 90 days
      }
    }
  }
}
