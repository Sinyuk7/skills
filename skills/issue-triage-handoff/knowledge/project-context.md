# Project Context Template

> **⚠️ THIS IS A TEMPLATE — DO NOT EDIT IN `knowledge/` DIRECTORY**
> 
> **To use this feature**:
> 1. Copy this file: `cp knowledge/project-context.md ./triage/project-context.md`
> 2. Edit `./triage/project-context.md` with your project's actual info
> 3. Run triage workflow — context automatically loaded in Step 6.5
> 
> **This is OPTIONAL**: Skill works without it, but gives generic recommendations.
> 
> **When to configure**: Your team has specific ownership boundaries that affect triage recommendations (e.g., SDK team maintains both client and backend, shouldn't receive "check external server" advice).

---

**Purpose**: Provide project-specific context to prevent incorrect responsibility attribution during triage synthesis. This file is loaded in workflow Step 6.5 (before synthesis) to inform `recommended_next_steps` and `suitable_for` fields.

---

## Project Identity

```yaml
project_name: "Your Project Name"
repository: "https://github.com/org/repo"
primary_language: "Python|JavaScript|Go|etc."
architecture_type: "monolith|microservices|library|cli_tool"
```

---

## Team Role

**Definition**: What is your team's relationship to this system?

```yaml
team_role: "provider"  # provider | consumer | integration | platform
```

### Role Definitions

| Role | Meaning | Example |
|------|---------|---------|
| `provider` | We build and maintain the system users consume | SDK team, API service team |
| `consumer` | We use an external system/SDK | App team using third-party SDK |
| `integration` | We connect multiple external systems | Middleware, gateway, orchestrator |
| `platform` | We provide infrastructure for other teams | Cloud platform, CI/CD team |

---

## Ownership Boundaries

**Critical**: Define what your team owns vs external dependencies.

```yaml
ownership:
  our_code:
    - "client SDK (Python/Java)"
    - "backend API server"
    - "database schema"
  
  external_dependencies:
    - "AWS S3 (storage)"
    - "Redis (caching)"
    - "Third-party payment API"
  
  shared_ownership:
    - "API gateway (platform team owns infra, we own routes)"
```

### Attribution Rules

Based on ownership:

**If `team_role: provider`**:
- ❌ DON'T recommend: "Check if the server team's API is down"
- ✅ DO recommend: "Investigate our API server timeout configuration"

**If `team_role: consumer`**:
- ✅ DO recommend: "Check third-party SDK logs"
- ✅ DO recommend: "Verify API credentials and rate limits"

**If `team_role: integration`**:
- ✅ DO recommend: "Check upstream service health"
- ✅ DO recommend: "Verify downstream service connectivity"

---

## Issue Scope (Optional)

**Context**: What is the typical scope of issues this project faces?

```yaml
issue_scope:
  typical_failures:
    - "Timeout on API calls"
    - "Rate limit exceeded"
    - "Authentication failures"
  
  typical_root_causes:
    - "Network instability"
    - "Configuration mismatch"
    - "Backend service degradation"
```

---

## Forbidden Assumptions

**List assumptions that should NEVER appear in handoff synthesis.**

```yaml
forbidden_assumptions:
  - "Assume we don't own the backend API"
  - "Recommend checking external service logs first"
  - "Suggest contacting the server team (we ARE the server team)"
  - "Assume the SDK is a black box (we maintain the SDK)"
```

### Example Use Case (from case_02)

**Problem**: SDK team's handoff says "检查服务端 openapi.music.163.com 响应日志"

**Context File**:
```yaml
team_role: "provider"
ownership:
  our_code:
    - "Client SDK"
    - "openapi.music.163.com API server"
forbidden_assumptions:
  - "Assume openapi.music.163.com is external"
```

**Result**: Handoff now says "检查我们的 openapi.music.163.com 服务器日志" instead of suggesting to "check external server".

---

## Synthesis Integration Points

### Step 6.5: Load Project Context (Workflow)

```yaml
if project-context.md exists:
  load context
  
  # Filter recommendations
  if team_role == "provider":
    - Remove "investigate external server" suggestions
    - Focus on internal code paths, configuration, deployment
  
  if team_role == "consumer":
    - Focus on integration points
    - Emphasize external API behavior, credentials, network
  
  # Adjust suitable_for agents
  if ownership.our_code includes "backend":
    suitable_for: ["rca_agent", "patch_agent"]
  else:
    suitable_for: ["human_review"]  # Can't patch external code
```

---

## Validation Rules

**Before using this context**:

1. ✅ `team_role` is one of: provider | consumer | integration | platform
2. ✅ `ownership.our_code` is non-empty (we own something)
3. ✅ `forbidden_assumptions` lists concrete phrases to avoid
4. ⚠️  File timestamp <90 days old (warn if stale)

**Staleness Warning**:
```
⚠️  project-context.md is 120 days old. 
Please verify ownership boundaries are still accurate.
```

---

## Template Instantiation Example

### Cloud Music IoT SDK (Real Case)

```yaml
project_name: "Cloud Music IoT SDK"
repository: "https://github.com/netease/iot-sdk"
primary_language: "Java"
architecture_type: "library"

team_role: "provider"

ownership:
  our_code:
    - "IoT SDK client (Java)"
    - "openapi.music.163.com API server"
    - "WebSocket gateway"
  
  external_dependencies:
    - "Client's application code"
    - "Public internet connectivity"

forbidden_assumptions:
  - "Assume openapi.music.163.com is external"
  - "Recommend client-side investigation first"
  - "Suggest contacting backend team (we ARE the backend team)"

issue_scope:
  typical_failures:
    - "Timeout on device registration"
    - "WebSocket connection drops"
  
  typical_root_causes:
    - "Backend API timeout configuration"
    - "Network firewall rules"
    - "Client SDK retry logic bugs"
```

---

## Next Steps

1. **Create this file** in your triage directory: `./triage/project-context.md`
2. **Populate fields** based on your project
3. **Test with case** that previously had wrong attribution
4. **Update quarterly** or when ownership changes

---

**Last Updated**: [Insert date when you fill this out]
