# Phase 3: Design Correction Loop

## Current Implementation (Mock)

**File:** `src/pipeline/design_correction_loop.py`

The current implementation does mock string replacements:

```python
# Current mock logic:
async def run(self, design_text: str) -> CorrectionResult:
    # Just returns the original design with mock history
    return CorrectionResult(
        final_design=design_text,
        iterations=1,
        converged=True,
        history=[
            CorrectionIteration(
                iteration=1,
                changes_made=["Mock change 1"],
                issues_resolved=["Mock issue"]
            )
        ]
    )
```

**Problems with mock approach:**
- Doesn't actually fix any issues
- No intelligent rewriting of problematic sections
- Can't address hallucinations or missing content
- No iterative improvement

---

## What This Phase Should Do

### Purpose
Take a design with identified issues and iteratively correct it until:
1. All auto-correctable issues are fixed
2. Max iterations (3) reached
3. Confidence threshold (0.8) achieved

### Correction Types

| Issue Type | Correction Strategy |
|------------|-------------------|
| **Hallucinated package** | Replace with real alternative or remove |
| **Missing section** | Generate the missing content |
| **Scope mismatch** | Add/remove features to align |
| **Over-engineering** | Simplify architecture |
| **Under-engineering** | Add necessary complexity |
| **Inconsistency** | Rewrite to make coherent |

### Input Data
The LLM receives:
```json
{
  "design_text": "# Project Design\n...(current design)...",
  "issues_to_fix": [
    {
      "code": "hallucinated_package",
      "message": "Package 'fastapi-hipaa-middleware' does not exist",
      "location": "Tech Stack > Security",
      "suggestion": "Remove or replace with manual HIPAA controls"
    },
    {
      "code": "missing_section",
      "message": "No audit logging architecture defined",
      "location": "HIPAA Considerations",
      "suggestion": "Add audit logging strategy section"
    }
  ],
  "complexity_profile": {
    "score": 12.5,
    "depth_level": "detailed"
  },
  "iteration": 1,
  "max_iterations": 3
}
```

### Expected Output
```json
{
  "corrected_design": "# HealthTrack Pro - System Design\n\n## Architecture Overview\n...(full corrected design markdown)...",
  "changes_made": [
    {
      "issue_code": "hallucinated_package",
      "action": "replaced",
      "before": "fastapi-hipaa-middleware for compliance",
      "after": "Custom middleware with python-audit-log for compliance tracking",
      "explanation": "Replaced non-existent package with combination of custom middleware and real audit logging library"
    },
    {
      "issue_code": "missing_section",
      "action": "added",
      "location": "After HIPAA Considerations",
      "content_summary": "Added 'Audit Logging Architecture' section with structured logging, immutable audit trail, and retention policies",
      "explanation": "HIPAA requires comprehensive audit trails for all PHI access"
    }
  ],
  "remaining_issues": [],
  "confidence": 0.88,
  "notes": "All identified issues have been addressed. The corrected design now includes explicit audit logging architecture and uses real packages only."
}
```

### Iteration Flow

```
Iteration 1:
  Input: Original design + all issues
  Output: Corrected design v1 + remaining issues
  
Iteration 2 (if remaining_issues not empty):
  Input: Corrected design v1 + remaining issues
  Output: Corrected design v2 + remaining issues
  
Iteration 3 (if still issues):
  Input: Corrected design v2 + remaining issues  
  Output: Final design + any unresolved issues (flagged for human review)
```

### How Output Is Used

1. **`corrected_design`** → Replaces the current design in UI
2. **`changes_made`** → Displayed in correction timeline with before/after
3. **`remaining_issues`** → Fed back into next iteration or shown as warnings
4. **`confidence`** → Displayed in timeline, determines if loop continues
5. **`notes`** → Shown as iteration summary

---

## API Endpoint

**Endpoint:** `POST /api/adaptive/correct`

```
Frontend → POST design_text + validation_report
         → For each iteration:
              → LLM call to correct
              → Validate corrected design
              → SSE stream progress
         → Final corrected design via SSE
```

---

## Prompt for You

I need you to act as the LLM for this phase. Below is a design with identified issues. Please provide the corrected design and change log in the exact JSON format shown above.

### Design to Correct

```markdown
# HealthTrack Pro - System Design

## Architecture Overview

HealthTrack Pro uses a microservices architecture deployed on AWS EKS with the following services:

- **API Gateway**: Kong for request routing and rate limiting
- **Auth Service**: Handles JWT authentication with HIPAA-compliant session management
- **User Service**: Patient and provider account management
- **Health Data Service**: Ingests and stores wearable device data
- **Messaging Service**: Real-time secure chat using WebSockets
- **Notification Service**: Handles email/SMS via Twilio and SendGrid
- **Billing Service**: Stripe integration for subscriptions
- **Scheduling Service**: Appointment booking with Google Calendar sync

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy
- **Frontend**: Next.js 14, TypeScript, TailwindCSS
- **Database**: PostgreSQL 15 with pgcrypto for encryption at rest
- **Cache**: Redis for sessions and real-time data
- **Queue**: Celery with Redis broker for async tasks
- **Infrastructure**: AWS EKS, RDS, ElastiCache, S3
- **Monitoring**: DataDog for APM and logging
- **Security**: fastapi-hipaa-middleware for compliance, AWS WAF

## Data Model

### Core Entities
- User (patients, providers, admins)
- Organization (multi-tenant)
- HealthMetric (heart rate, steps, sleep, etc.)
- Appointment
- Message
- Prescription
- Subscription

### HIPAA Considerations
- All PHI encrypted at rest using AES-256
- Automatic session timeout after 15 minutes
- Data retention policy: 7 years

## External Integrations

1. **Fitbit API** - OAuth2 flow, webhook for real-time sync
2. **Apple HealthKit** - Direct API integration for health data
3. **Stripe** - Subscriptions, invoicing, payment methods
4. **Twilio** - SMS notifications and 2FA
5. **Google Calendar** - Appointment sync for providers
6. **Pharmacy API** - TBD based on partner selection

## Deployment Strategy

- Blue/green deployments on EKS
- Terraform for infrastructure as code
- GitHub Actions for CI/CD
- Staging environment mirrors production
```

### Issues to Fix

```json
[
  {
    "code": "hallucinated_package",
    "message": "Package 'fastapi-hipaa-middleware' does not exist in PyPI",
    "location": "Tech Stack > Security",
    "auto_correctable": true,
    "suggestion": "Remove reference or replace with real security packages"
  },
  {
    "code": "missing_audit_logging",
    "message": "HIPAA compliance requires explicit audit logging but none is defined",
    "location": "HIPAA Considerations",
    "auto_correctable": true,
    "suggestion": "Add audit logging architecture section"
  },
  {
    "code": "impossible_integration",
    "message": "Apple HealthKit requires native iOS SDK - cannot be accessed via 'Direct API integration' from a web backend",
    "location": "External Integrations > Apple HealthKit",
    "auto_correctable": true,
    "suggestion": "Clarify that mobile app is needed or remove HealthKit integration"
  },
  {
    "code": "missing_baa_mention",
    "message": "HIPAA requires Business Associate Agreements with all data processors but none mentioned",
    "location": "HIPAA Considerations",
    "auto_correctable": true,
    "suggestion": "Add section on required BAAs with third parties"
  }
]
```

### Your Task

Provide the correction response in the JSON format specified above. Include:
1. The fully corrected design markdown (complete document, not just changes)
2. Detailed change log for each issue fixed
3. Any remaining issues that couldn't be auto-corrected
4. Confidence score for the corrected design
5. Notes summarizing what was done

---

## Response Location

Please provide your response in: `adaptive_llm_implementation/RESPONSE_3_CORRECTION.md`
