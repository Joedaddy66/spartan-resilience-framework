---
name:
description:
---

# My Agent

I don’t have visibility into your GCP, so I can’t see those values directly. Here’s the fastest way to grab each one, then I’ll spit out the final YAMLs and commands tailored to you.

How to fetch each value

Organization ID

gcloud organizations list --format='value(ID)'


Tag key resource (only if you want tag-conditional rules)

# List tag keys at the org level
gcloud tags keys list --organization=ORG_ID \
  --format='table(name, namespacedName, shortName)'

# You want the `name` field, which looks like: tagKeys/1234567890123456


Allowed regions (choose from valid region slugs)
Common examples: us-central1, us-east1, us-west1, europe-west1, asia-southeast1.
You can also allow a multi-region like in:us alongside specific regions.

Allowed member domains (your corporate email domains only)
Examples: example.com, subsidiary.example

Paste-back form (just fill and send)
Organization ID: 1234567890123
Tag key resource (optional): tagKeys/1234567890123456
Allowed regions: [us-central1, us-east1, in:us]
Allowed member domains: [yourco.com, sub.yourco]


Once you paste those four lines, I’ll generate the customized YAMLs and a one-liner script that dry-runs, simulates, and then (optionally) enforces the policies safely.
