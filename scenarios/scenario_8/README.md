# Scenario 8: AWS Privilege Escalation & Data Exfiltration

---

## Overview

This scenario simulates a multi-stage AWS attack that demonstrates privilege escalation through IAM role chaining, persistence via backdoor user creation, and data exfiltration from S3 and Secrets Manager — all routed through Tor for anonymization.

---

## Quick Start

### Configuration

Edit `infra/Pulumi.yaml` before deploying:

```yaml
config:
  aws:region: us-east-1
  infra:extraRegion: us-west-1
  infra:includeAgent: False  # Set True for endpoint variant
  infra:agentInstallerPath: ../../../path/to/agent.tar.gz  # Required if includeAgent: True
  # infra:exfilBucketCount: 20  # Number of S3 buckets to create (default: 20)
  # infra:subnetId: subnet-xxxxx  # Optional: use existing subnet
  # infra:vpcId: vpc-xxxxx        # Optional: use existing VPC
  infra:tags:
    value: |
      {
        "Owner": "YourName",
        "UC-OWNER": "YourName",
        "Team": "YourTeam"
      }
```

### Deployment Options

**Option 1: With Learning Period (Recommended)**

```bash
# Deploy infrastructure only
python cobra.py launch --simulation --manual --scenario cobra-scenario-8

# Wait for behavioral baselines to establish (5+ days recommended)

# Execute attack simulation
python cobra.py post-launch --simulation --scenario cobra-scenario-8
```

**Option 2: Immediate Execution**

```bash
# Deploy and attack in one step (may produce fewer behavioral alerts)
python cobra.py launch --simulation --scenario cobra-scenario-8
```

### Cleanup

> ⚠️ **Always clean up after the demo** to remove backdoor accounts and infrastructure.

```bash
python cobra.py destroy --scenario cobra-scenario-8
```

---

## Attack Flow

The attack progresses through the following stages:

### Stage 1 — Initial Access

- **Variant 1 (Default):** Attacker starts with compromised developer AWS CLI credentials.
- **Variant 2 (Endpoint):** Attacker compromises an EC2 instance with a Cortex XDR agent, then exfiltrates AWS credentials from the machine via Tor.

### Stage 2 — Reconnaissance (Low Privilege)

Using the compromised dev credentials, the attacker enumerates:

- S3 buckets (`s3api list-buckets`)
- Secrets Manager secrets (primary + secondary region)
- IAM roles (`iam list-roles`)

Most of these calls fail due to the dev user's limited permissions.

### Stage 3 — Privilege Escalation via Role Chaining

1. The dev user assumes the **Lambda execution role** (allowed by the Lambda role's trust policy).
2. The Lambda role has an overly permissive policy: `sts:AssumeRole` on `Resource: "*"`.
3. The attacker sprays `AssumeRole` across all discovered IAM roles.
4. The attacker successfully assumes the **IAM Monitor role**, which has `AdministratorAccess`.

### Stage 4 — Persistence

With admin privileges, the attacker:

- Creates a backdoor IAM user (`cobra-prod-system-backup-user`)
- Attaches `AdministratorAccess` policy to the backdoor user
- Creates a login profile (console password) for the backdoor user

### Stage 5 — Data Exfiltration

With elevated privileges, the attacker:

- Re-runs reconnaissance (now succeeds with full visibility)
- Dumps all secrets from AWS Secrets Manager (both regions)
- Syncs all S3 bucket contents to the attacker machine

All attack traffic is routed through **Tor** (via `proxychains`) to obscure the attacker's origin.

---

## Scenario Variants

### Variant 1: Credential-Based (Default)

- `includeAgent: False`
- Simpler setup — no agent installer needed
- Pure cloud security demo
- Attack starts with compromised dev credentials

### Variant 2: Endpoint + Cloud

- `includeAgent: True`
- Requires Cortex XDR agent installer (x86_64 Linux `.tar.gz`)
- Demonstrates endpoint compromise leading to cloud attack
- Includes a compromised EC2 instance with the XDR agent installed

---

## Key Misconfigurations

| Misconfiguration | Detail |
|---|---|
| **Overly permissive AssumeRole** | Lambda role can assume ANY role (`Resource: "*"`) |
| **Excessive privileges** | IAM Monitor role has `AdministratorAccess` attached |
| **Weak trust policy** | Dev user can directly assume the Lambda execution role |

---

## Infrastructure Components

### IAM

| Resource | Purpose |
|---|---|
| Dev User | Limited-privilege developer with Lambda admin access and an access key |
| Lambda Role | Execution role with overly permissive `sts:AssumeRole` on `*` |
| IAM Monitor Role | Trusts the Lambda role; has `AdministratorAccess` |

### Compute

| Resource | Purpose |
|---|---|
| Attacker EC2 | Ubuntu instance with Tor and AWS CLI pre-installed |
| Compromised EC2 | *(Variant 2 only)* Ubuntu instance with Cortex XDR agent |
| Lambda Function | Scheduled function (every 2 hours) to establish behavioral baseline |

### Storage & Secrets

| Resource | Purpose |
|---|---|
| S3 Buckets | 20 buckets (configurable) populated with sensitive files |
| Secrets Manager | Secrets in 2 regions (primary + `extraRegion`) |

### Networking

- A VPC, subnet, internet gateway, and route table are created automatically unless existing `vpcId`/`subnetId` are provided in the config.
- The attacker EC2 security group restricts SSH to the deployer's `/24` CIDR block.

---

## Troubleshooting

- **Check Pulumi logs:** `pulumi logs -s cobra-scenario-8`
- **Review CloudTrail events** in the AWS Console for API call history
- **Missing behavioral alerts?** Ensure a 5+ day learning period before running the attack
- **Verify CloudTrail** has S3 data events enabled for exfiltration detection

---

## Security Warning

> **⚠️ This scenario creates intentionally vulnerable infrastructure.**
>
> - Run in an isolated AWS sandbox account only
> - Never deploy in production environments
> - Clean up immediately after the demo
