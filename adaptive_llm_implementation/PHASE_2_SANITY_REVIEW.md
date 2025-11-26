# Phase 2: LLM Sanity Review

## Current Implementation (Mock)

**File:** `src/pipeline/llm_sanity_reviewer.py`

The current implementation returns hardcoded mock data:

```python
# Current mock logic:
def review(self, design_text: str, validation_report: ValidationReport) -> ReviewResult:
    # Returns static mock values
    return ReviewResult(
        confidence=0.85,
        risks=["Mock risk 1", "Mock risk 2"],
        suggestions=["Mock suggestion"],
        notes="Mock review notes"
    )
```

**Problems with mock approach:**
- No actual semantic analysis of the design
- Can't detect real inconsistencies or hallucinations
- Doesn't understand if the design matches the requirements
- No intelligent risk identification

---

## What This Phase Should Do

### Purpose
Perform a semantic review of the generated design document to catch issues that rule-based validation misses:

1. **Coherence check** - Does the design make sense as a whole?
2. **Hallucination detection** - Are there made-up frameworks, impossible integrations, or fake APIs?
3. **Scope alignment** - Does the design match the stated requirements?
4. **Over/under engineering** - Is the architecture appropriate for the scale?
5. **Risk identification** - What could go wrong with this approach?

### Input Data
The LLM receives:
```json
{
  "design_text": "# Project Design\n\n## Architecture Overview\n...(full design markdown)...",
  "validation_report": {
    "is_valid": true,
    "checks": {
      "has_architecture": true,
      "has_tech_stack": true,
      "has_data_model": true,
      "scope_alignment": true
    },
    "issues": []
  },
  "complexity_profile": {
    "score": 12.5,
    "depth_level": "detailed",
    "estimated_phase_count": 7
  },
  "original_requirements": "Build a patient health monitoring SaaS platform..."
}
```

### Expected Output
```json
{
  "confidence": 0.78,
  "overall_assessment": "sound_with_concerns",
  "coherence": {
    "score": 0.85,
    "notes": "Architecture is internally consistent. The microservices approach aligns with the multi-tenant requirement."
  },
  "hallucination_check": {
    "passed": false,
    "issues": [
      {
        "type": "non_existent_package",
        "text": "fastapi-hipaa-middleware",
        "note": "This package does not exist. HIPAA compliance must be implemented manually or via audit logging libraries."
      }
    ]
  },
  "scope_alignment": {
    "score": 0.9,
    "missing_requirements": [],
    "over_engineered": [
      "Kubernetes deployment may be overkill for 10k users - consider starting with single-node Docker Compose"
    ],
    "under_engineered": [
      "No mention of audit logging strategy for HIPAA compliance"
    ]
  },
  "risks": [
    {
      "severity": "high",
      "category": "compliance",
      "description": "HIPAA requires BAA agreements with all data processors. Stripe, Twilio, and cloud provider all need BAAs.",
      "mitigation": "Create checklist of required BAAs before development starts"
    },
    {
      "severity": "medium", 
      "category": "integration",
      "description": "Apple HealthKit requires native iOS app - web-only approach won't work for Apple Health data",
      "mitigation": "Clarify if mobile app is in scope or if HealthKit sync is deferred"
    }
  ],
  "suggestions": [
    "Add explicit audit logging architecture section",
    "Clarify data retention and deletion policies for HIPAA",
    "Consider FHIR standard for healthcare data interoperability"
  ],
  "summary": "The design is architecturally sound but has compliance gaps that need addressing before development. The hallucinated HIPAA middleware should be replaced with explicit security controls. Recommend adding Phase 0 for compliance planning."
}
```

### How Output Is Used

1. **`confidence`** → Displayed as gauge in UI, blocks auto-advance if < 0.7
2. **`hallucination_check.issues`** → Shown as errors requiring correction
3. **`risks`** → Displayed as warnings with severity badges
4. **`suggestions`** → Shown as actionable improvement items
5. **`summary`** → Displayed as the main review text in UI

---

## API Endpoint

**Endpoint:** `POST /api/adaptive/validate`

This endpoint runs both rule-based validation AND LLM sanity review:
```
Frontend → POST design_text + complexity_profile 
         → DesignValidator.validate() (rule-based)
         → LLMSanityReviewer.review() (LLM call)
         → Combined response via SSE
```

---

## Prompt for You

I need you to act as the LLM for this phase. Below is a sample design document. Please provide the sanity review response in the exact JSON format shown above.

### Sample Design Input

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
- Audit logs for all data access
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

### Validation Report (from rule-based checks)

```json
{
  "is_valid": true,
  "checks": {
    "has_architecture": true,
    "has_tech_stack": true,
    "has_data_model": true,
    "has_integrations": true,
    "scope_alignment": true
  },
  "issues": []
}
```

### Your Task

Provide the sanity review response in the JSON format specified above. Focus on:
1. Semantic coherence of the design
2. Any hallucinated packages or impossible integrations
3. Scope alignment with requirements
4. Over/under engineering concerns
5. Real risks the design doesn't address
6. Actionable suggestions for improvement

---

## Response Location

Please provide your response in: `adaptive_llm_implementation/RESPONSE_2_SANITY_REVIEW.md`
