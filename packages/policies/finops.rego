package finops

# Budget Guardrail - Enforce cost caps
deny contains msg if {
    input.unit_cost_usd > 0.5
    msg := sprintf("Unit cost %.4f exceeds budget cap of 0.5 USD", [input.unit_cost_usd])
}

# Budget Guardrail - Total spend limits
deny contains msg if {
    input.total_spend_usd > input.budget_cap_usd
    msg := sprintf("Total spend %.2f USD exceeds budget cap %.2f USD", [input.total_spend_usd, input.budget_cap_usd])
}

# Require Cost Tags - All deployments must have cost allocation tags
deny contains msg if {
    not input.cost_tags
    msg := "Deployment missing required cost_tags"
}

deny contains msg if {
    input.cost_tags
    count(input.cost_tags) == 0
    msg := "cost_tags cannot be empty"
}

deny contains msg if {
    input.cost_tags
    not input.cost_tags.team
    msg := "cost_tags missing required 'team' field"
}

deny contains msg if {
    input.cost_tags
    not input.cost_tags.environment
    msg := "cost_tags missing required 'environment' field"
}

# Block Promotion - Prevent promotion if quality gates fail
deny contains msg if {
    input.promotion_request == true
    input.test_pass_rate < 0.95
    msg := sprintf("Cannot promote: test pass rate %.2f%% is below required 95%%", [input.test_pass_rate * 100])
}

deny contains msg if {
    input.promotion_request == true
    input.security_scan_passed == false
    msg := "Cannot promote: security scan failed"
}

# Carbon Shift - Enforce sustainability requirements
deny contains msg if {
    input.carbon_intensity_g_per_kwh > 400
    msg := sprintf("Carbon intensity %.2f g/kWh exceeds limit of 400 g/kWh", [input.carbon_intensity_g_per_kwh])
}

deny contains msg if {
    input.deployment_region
    not carbon_efficient_region(input.deployment_region)
    msg := sprintf("Region '%s' is not carbon-efficient - consider shifting to a greener region", [input.deployment_region])
}

# Carbon efficient regions (example list - expand based on actual data)
carbon_efficient_region(region) if {
    region == "us-west-2"  # Powered by renewable energy
}

carbon_efficient_region(region) if {
    region == "eu-north-1"  # Nordic hydro power
}

carbon_efficient_region(region) if {
    region == "ca-central-1"  # Canadian hydro power
}

# Allow rule - deployment is approved if no deny rules match
allow if {
    count(deny) == 0
}

# Warnings - non-blocking but should be addressed
warn contains msg if {
    input.unit_cost_usd > 0.3
    input.unit_cost_usd <= 0.5
    msg := sprintf("Warning: Unit cost %.4f is approaching budget cap", [input.unit_cost_usd])
}

warn contains msg if {
    input.carbon_intensity_g_per_kwh > 300
    input.carbon_intensity_g_per_kwh <= 400
    msg := sprintf("Warning: Carbon intensity %.2f g/kWh is high - consider optimization", [input.carbon_intensity_g_per_kwh])
}
