# Phase 1: Complexity Analysis

## Current Implementation (Mock)

**File:** `src/interview/complexity_analyzer.py`

The current implementation uses static keyword matching to bucket projects:

```python
# Current mock logic:
project_type_score = {
    'cli_tool': 1, 'library': 2, 'api': 3, 'web_app': 4, 'saas': 5
}
# Looks for keywords like "cli", "api", "saas" in requirements text
# Returns deterministic scores based on keyword presence
```

**Problems with mock approach:**
- Can't understand nuanced requirements
- Misses implicit complexity (e.g., "simple auth" vs "enterprise SSO")
- No reasoning about WHY a project is complex
- Can't generate intelligent follow-up questions

---

## What This Phase Should Do

### Purpose
Analyze the full project context (from interview data) and produce a holistic complexity assessment that determines:
1. How many phases the devplan should have (3-15)
2. How detailed each phase should be (minimal/standard/detailed)
3. Confidence level in the assessment
4. Follow-up questions if information is missing

### Input Data
The LLM receives interview data containing:
```json
{
  "project_name": "MyApp",
  "project_type": "web_app",  // May be inferred or explicit
  "requirements": "Build a REST API with user authentication, payment processing via Stripe, and real-time notifications",
  "languages": ["Python", "TypeScript"],
  "frameworks": "FastAPI, React, PostgreSQL",
  "team_size": "3",
  "apis": ["Stripe", "SendGrid", "Twilio"],
  "timeline": "3 months",
  "constraints": "Must be HIPAA compliant"
}
```

### Expected Output
The LLM should return a structured complexity profile:
```json
{
  "complexity_score": 12.5,
  "estimated_phase_count": 7,
  "depth_level": "detailed",
  "confidence": 0.85,
  "rationale": "This project involves multiple external integrations (Stripe, SendGrid, Twilio), real-time features requiring WebSocket infrastructure, and HIPAA compliance which adds significant security and audit requirements. The 3-person team and 3-month timeline are aggressive for this scope.",
  "complexity_factors": {
    "integrations": "high - 3 external APIs with different auth patterns",
    "security": "very_high - HIPAA compliance requires audit logging, encryption, BAA",
    "realtime": "medium - notifications require WebSocket or SSE",
    "data": "medium - user data with PII handling",
    "scale": "unknown - no metrics provided"
  },
  "follow_up_questions": [
    "What is the expected user volume at launch and 12 months out?",
    "Will you need to store PHI (Protected Health Information) or just handle it transiently?"
  ],
  "hidden_risks": [
    "HIPAA compliance typically requires 2-3x development time for audit trails",
    "Stripe + HIPAA has specific requirements around card data isolation"
  ]
}
```

### How Output Is Used

1. **`estimated_phase_count`** → Determines how many phases the devplan generator creates
2. **`depth_level`** → Selects template variant (minimal/standard/detailed)
3. **`confidence`** → If < 0.7, UI shows follow-up questions before proceeding
4. **`rationale`** → Displayed in UI for user understanding
5. **`hidden_risks`** → Shown as warnings in the design phase

---

## API Endpoint

**Endpoint:** `POST /api/adaptive/complexity`

**Current flow:**
```
Frontend → POST interview_data → ComplexityAnalyzer.analyze() → SSE stream → Frontend
```

**After implementation:**
```
Frontend → POST interview_data → LLM call with prompt → Parse JSON → SSE stream → Frontend
```

---

## Prompt for You

I need you to act as the LLM for this phase. Below is a sample project. Please provide the response in the exact JSON format shown above.

### Sample Project Input

```json
{
  "project_name": "HealthTrack Pro",
  "project_type": "saas",
  "requirements": "Build a patient health monitoring SaaS platform. Features include: user dashboard with health metrics visualization, integration with wearable devices (Fitbit, Apple Health), appointment scheduling with calendar sync, secure messaging between patients and healthcare providers, prescription tracking with pharmacy API integration, HIPAA compliant data storage, multi-tenant architecture for different healthcare organizations, billing and subscription management via Stripe, email and SMS notifications for appointments and medication reminders.",
  "languages": ["Python", "TypeScript"],
  "frameworks": "FastAPI, Next.js, PostgreSQL, Redis, Celery",
  "team_size": "5",
  "apis": ["Fitbit API", "Apple HealthKit", "Stripe", "Twilio", "Google Calendar", "pharmacy API TBD"],
  "timeline": "6 months",
  "constraints": "HIPAA compliance required, SOC 2 certification planned for year 2, must support 10k users at launch"
}
```

### Your Task

Provide the complexity analysis response in the JSON format specified above. Include:
1. A complexity score (0-20 scale)
2. Recommended phase count (3-15)
3. Depth level (minimal/standard/detailed)
4. Confidence score (0-1)
5. Detailed rationale explaining your reasoning
6. Breakdown of complexity factors
7. Any follow-up questions needed
8. Hidden risks the user might not have considered

---

## Response Location

Please provide your response in: `adaptive_llm_implementation/RESPONSE_1_COMPLEXITY.md`
