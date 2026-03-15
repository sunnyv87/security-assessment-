# AI Analyst Assistant Module

## Overview

The AI Analyst Assistant is a Python microservice that augments VAPT security
analysts with AI-powered capabilities. It operates as a **human-in-the-loop
co-pilot**: every AI output is a recommendation that requires analyst review
before it becomes authoritative. The module **cannot** automatically publish
reports or change finding statuses without analyst confirmation.

---

## 1. AI Pipeline Architecture

### 1.1 System Architecture

```
                        ┌──────────────────────────────────┐
                        │       Analyst Workbench UI        │
                        │  (React / Next.js)                │
                        │                                    │
                        │  ┌────────┐ ┌─────────┐ ┌──────┐ │
                        │  │Validate│ │Remediate│ │Draft │ │
                        │  │Finding │ │Suggest  │ │Report│ │
                        │  └───┬────┘ └────┬────┘ └──┬───┘ │
                        └──────┼───────────┼─────────┼─────┘
                               │           │         │
                        ═══════╪═══════════╪═════════╪══════ API Gateway
                               │           │         │
                        ┌──────▼───────────▼─────────▼─────┐
                        │    AI Analyst Assistant Service    │
                        │    (Python 3.12 + FastAPI)        │
                        │                                    │
                        │  ┌──────────────────────────────┐ │
                        │  │       Request Router          │ │
                        │  │  (validates, rate-limits,     │ │
                        │  │   routes to pipeline stage)   │ │
                        │  └──────────┬───────────────────┘ │
                        │             │                      │
                        │  ┌──────────▼───────────────────┐ │
                        │  │     Pipeline Orchestrator     │ │
                        │  │                               │ │
                        │  │  ┌─────┐ ┌─────┐ ┌────────┐ │ │
                        │  │  │Summ.│ │FP   │ │Priorit.│ │ │
                        │  │  │     │ │Det. │ │        │ │ │
                        │  │  └──┬──┘ └──┬──┘ └───┬────┘ │ │
                        │  │     │       │        │      │ │
                        │  │  ┌──▼──┐ ┌──▼──────┐       │ │
                        │  │  │Remed│ │Report   │       │ │
                        │  │  │     │ │Draft    │       │ │
                        │  │  └─────┘ └─────────┘       │ │
                        │  └──────────────────────────────┘ │
                        │             │                      │
                        │  ┌──────────▼───────────────────┐ │
                        │  │      Context Builder          │ │
                        │  │  (RAG + historical data)      │ │
                        │  └──────────┬───────────────────┘ │
                        │             │                      │
                        │  ┌──────────▼───────────────────┐ │
                        │  │      LLM Gateway              │ │
                        │  │  (Claude API + retry +        │ │
                        │  │   token tracking + caching)   │ │
                        │  └──────────────────────────────┘ │
                        └────────┬──────────┬───────────────┘
                                 │          │
                    ┌────────────▼──┐  ┌────▼──────────────┐
                    │  Claude API   │  │  PostgreSQL +     │
                    │  (Anthropic)  │  │  pgvector         │
                    │               │  │  Redis Cache      │
                    └───────────────┘  └───────────────────┘
```

### 1.2 Pipeline Stages

The AI pipeline processes findings through five independent-but-composable
stages. Each stage can be invoked individually or chained together in the
full enrichment pipeline.

```
 Finding                                                          Analyst
 Ingested                                                         Reviews
    │                                                                │
    ▼                                                                │
 ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──▼───────┐
 │  Stage 1 │───▶│  Stage 2 │───▶│  Stage 3 │───▶│  Stage 4 │───▶│  Stage 5 │
 │          │    │          │    │          │    │          │    │          │
 │  Vuln    │    │  False   │    │  Risk    │    │ Remed.   │    │  Report  │
 │  Summary │    │  Positive│    │  Priority│    │ Suggest  │    │  Draft   │
 │          │    │  Detect  │    │  Ranking │    │          │    │          │
 └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
      │               │               │               │               │
      ▼               ▼               ▼               ▼               ▼
 ai_summary      fp_probability   risk_score     remediation     draft_report
 ai_confidence   fp_reasoning     risk_factors   code_examples   (NEVER auto-
 attack_context  similar_fps      business_imp   references       published)
```

### 1.3 Guardrails & Safety Controls

| Control                     | Implementation                                      |
|-----------------------------|------------------------------------------------------|
| Human-in-the-loop           | All AI outputs tagged `status: pending_review`       |
| No auto-publish             | Report drafts stored with `published: false`; only   |
|                             | analyst with `report:publish` permission can publish  |
| Confidence scores           | Every output includes 0.0-1.0 confidence score       |
| Audit trail                 | All AI invocations logged with input hash, output,   |
|                             | model version, latency, token count                  |
| Rate limiting               | Per-tenant + per-analyst API rate limits              |
| Content filtering           | Output sanitized; no executable code in remediation  |
| Hallucination guard         | RAG grounds responses in actual scanner evidence     |
| Prompt injection defense    | Finding data inserted via structured variables, not  |
|                             | raw concatenation; system prompt is immutable         |
| Graceful degradation        | If Claude API is unavailable, findings queue for      |
|                             | manual analyst review without AI enrichment           |
| Token budget                | Per-request token ceiling; truncation strategy for    |
|                             | oversized evidence                                    |

---

## 2. Prompts Used

### 2.1 Vulnerability Summarization Prompt

```
SYSTEM:
You are a senior VAPT security analyst. Your role is to produce concise,
accurate vulnerability summaries for other analysts to review. You must
base your analysis ONLY on the provided scanner evidence and finding data.
Do not speculate about vulnerabilities not present in the evidence.

Always structure your response as JSON matching the required schema.

USER:
Analyze this vulnerability finding and produce a structured summary.

## Finding Data
- Title: {{finding.title}}
- CWE: {{finding.cwe_id}} ({{finding.cwe_name}})
- Scanner: {{finding.scanner}}
- Asset: {{finding.asset}}
- Endpoint: {{finding.http_method}} {{finding.endpoint}}
- CVSS Score: {{finding.cvss_score}} (Vector: {{finding.cvss_vector}})

## Scanner Evidence
### Request
{{finding.evidence.request | truncate(4000)}}

### Response
{{finding.evidence.response | truncate(4000)}}

### Raw Output
{{finding.evidence.raw_output | truncate(2000)}}

## Asset Context
- Environment: {{asset.environment}}  (production/staging/dev)
- Internet-facing: {{asset.internet_facing}}
- Data classification: {{asset.data_classification}}
- Technology stack: {{asset.tech_stack}}

## Historical Context
{{rag_context.similar_findings | format_similar(top=5)}}

## Required Output (JSON)
{
  "executive_summary": "1-2 sentence non-technical summary for executives",
  "technical_summary": "Detailed technical explanation (max 300 words)",
  "attack_scenario": "Step-by-step exploit scenario if confirmed",
  "affected_component": "Specific component/function/endpoint affected",
  "data_at_risk": "What data could be exposed or compromised",
  "prerequisites": "What an attacker needs (auth, network position, etc.)",
  "confidence": 0.0-1.0,
  "confidence_reasoning": "Why this confidence level"
}
```

### 2.2 False Positive Detection Prompt

```
SYSTEM:
You are a false positive detection specialist for vulnerability scanners.
Your job is to assess whether a scanner finding is a true positive (real
vulnerability) or a false positive (incorrectly flagged). You must be
conservative: when uncertain, lean toward "likely true positive" to avoid
missing real vulnerabilities.

Base your assessment ONLY on the evidence provided. Clearly state when
evidence is insufficient to make a determination.

USER:
Assess whether this finding is a true positive or false positive.

## Finding
- Title: {{finding.title}}
- CWE: {{finding.cwe_id}}
- Scanner: {{finding.scanner}} (known FP rate for this rule: {{scanner_rule.fp_rate}}%)
- Confidence from scanner: {{finding.scanner_confidence}}

## Evidence
### Request
{{finding.evidence.request | truncate(4000)}}

### Response
{{finding.evidence.response | truncate(4000)}}

## Scanner Rule Context
- Rule ID: {{scanner_rule.id}}
- Rule description: {{scanner_rule.description}}
- Historical FP rate for this rule on similar assets: {{scanner_rule.historical_fp_rate}}%

## Similar Past Findings (analyst-verified)
{{rag_context.similar_verified | format_verified(top=10)}}

Of the {{rag_context.similar_count}} similar historical findings:
- {{rag_context.tp_count}} were confirmed True Positive
- {{rag_context.fp_count}} were confirmed False Positive
- {{rag_context.dup_count}} were marked Duplicate

## Technology Context
- Server: {{asset.server_tech}}
- Framework: {{asset.framework}}
- WAF/Security layers: {{asset.security_layers}}

## Required Output (JSON)
{
  "verdict": "true_positive | likely_true_positive | uncertain | likely_false_positive | false_positive",
  "probability_fp": 0.0-1.0,
  "reasoning": [
    "Reason 1 for this assessment",
    "Reason 2 for this assessment"
  ],
  "evidence_quality": "strong | moderate | weak | insufficient",
  "key_indicators": [
    {"indicator": "description", "supports": "tp | fp"}
  ],
  "recommended_action": "validate_manually | accept_as_tp | dismiss_as_fp | needs_retest",
  "manual_verification_steps": [
    "Step analyst should take to verify"
  ],
  "confidence": 0.0-1.0
}
```

### 2.3 Risk Prioritization Prompt

```
SYSTEM:
You are a risk assessment specialist. Given a set of vulnerability findings,
you must prioritize them based on real-world exploitability, business impact,
and environmental context. Your prioritization directly influences which
vulnerabilities analysts investigate first, so accuracy is critical.

Use the CVSS base score as a starting point but adjust based on the
environmental and threat context provided.

USER:
Prioritize these findings for analyst investigation.

## Engagement Context
- Customer: {{engagement.customer_name}}
- Industry: {{engagement.industry}}
- Compliance requirements: {{engagement.compliance_frameworks | join(', ')}}
- Assessment type: {{engagement.type}}

## Findings to Prioritize ({{findings | length}} total)
{% for f in findings %}
### Finding #{{f.id}} — {{f.title}}
- Severity: {{f.severity}} | CVSS: {{f.cvss_score}}
- CWE: {{f.cwe_id}}
- Asset: {{f.asset}} ({{f.asset_criticality}})
- Internet-facing: {{f.internet_facing}}
- Authentication required: {{f.auth_required}}
- Scanner: {{f.scanner}}
- AI FP probability: {{f.ai_false_positive_prob}}
{% endfor %}

## Threat Intelligence Context
- Active exploits in the wild: {{threat_intel.active_exploits | join(', ')}}
- CISA KEV matches: {{threat_intel.kev_matches | join(', ')}}
- EPSS scores: {{threat_intel.epss_scores | format_epss}}

## Required Output (JSON)
{
  "prioritized_findings": [
    {
      "finding_id": "id",
      "priority_rank": 1,
      "risk_score": 0.0-10.0,
      "risk_factors": {
        "exploitability": "critical | high | medium | low",
        "business_impact": "critical | high | medium | low",
        "exposure": "external | internal | restricted",
        "data_sensitivity": "critical | high | medium | low",
        "active_threat": true/false
      },
      "justification": "Why this priority ranking",
      "attack_chains": ["finding_id_1 → finding_id_2 → finding_id_3"],
      "compliance_impact": ["PCI DSS Req 6.2", "SOC 2 CC6.1"]
    }
  ],
  "executive_risk_summary": "2-3 sentence overall risk posture",
  "recommended_investigation_order": ["id1", "id2", "id3"],
  "confidence": 0.0-1.0
}
```

### 2.4 Remediation Suggestion Prompt

```
SYSTEM:
You are a remediation specialist. Generate actionable, specific remediation
guidance for vulnerability findings. Your suggestions must be:
1. Technically accurate for the target technology stack
2. Include concrete code examples when applicable
3. Ordered from most effective to least effective
4. Include both immediate fixes and long-term hardening

NEVER generate guidance that could be used offensively. Focus exclusively
on defensive remediation.

USER:
Generate remediation guidance for this vulnerability.

## Finding
- Title: {{finding.title}}
- CWE: {{finding.cwe_id}} ({{finding.cwe_name}})
- Severity: {{finding.severity}} (CVSS: {{finding.cvss_score}})
- Asset: {{finding.asset}}
- Endpoint: {{finding.http_method}} {{finding.endpoint}}

## Technical Context
- Language: {{asset.language}}
- Framework: {{asset.framework}} (version: {{asset.framework_version}})
- Runtime: {{asset.runtime}}
- Database: {{asset.database}}
- Deployment: {{asset.deployment_type}}

## Vulnerability Evidence
### Vulnerable Request
{{finding.evidence.request | truncate(3000)}}

### Server Response
{{finding.evidence.response | truncate(3000)}}

## Source Code Context (if SAST)
{{finding.source_code_context | truncate(2000) | default("Not available — DAST finding")}}

## Existing Security Controls
{{asset.security_controls | join('\n')}}

## Required Output (JSON)
{
  "summary": "1-2 sentence remediation summary",
  "priority": "immediate | short_term | medium_term",
  "detailed_steps": [
    {
      "step": 1,
      "action": "What to do",
      "description": "Detailed explanation",
      "effort": "minutes | hours | days"
    }
  ],
  "code_examples": [
    {
      "language": "java",
      "label": "Fix SQL injection in login handler",
      "before": "// vulnerable code",
      "after": "// secure code",
      "explanation": "Why this fix works"
    }
  ],
  "defense_in_depth": [
    "Additional hardening recommendation 1",
    "Additional hardening recommendation 2"
  ],
  "testing_verification": [
    "How to verify the fix works"
  ],
  "references": [
    {"title": "OWASP Guide", "url": "https://...", "source": "OWASP"}
  ],
  "estimated_effort": "hours | days | weeks",
  "confidence": 0.0-1.0
}
```

### 2.5 Report Drafting Prompt

```
SYSTEM:
You are a VAPT report author. Draft professional vulnerability assessment
reports from validated findings. Your reports must be:
1. Factual — based only on confirmed/validated findings
2. Structured — following the standard VAPT report format
3. Audience-appropriate — executive summary is non-technical, technical
   sections include full detail
4. Actionable — clear remediation roadmap with priorities

CRITICAL: You are drafting a report for analyst review. This draft will
NOT be sent to the customer until an authorized analyst reviews, edits,
and explicitly approves it for publication. Mark all sections as DRAFT.

USER:
Draft a {{report_type}} report for this engagement.

## Engagement
- Customer: {{engagement.customer_name}}
- Engagement: {{engagement.name}}
- Type: {{engagement.type}}
- Scope: {{engagement.scope_description}}
- Period: {{engagement.start_date}} to {{engagement.end_date}}
- Lead Analyst: {{engagement.lead_analyst}}

## Validated Findings ({{findings | length}} total)
### By Severity
- Critical: {{findings | selectattr('severity', 'eq', 'critical') | list | length}}
- High: {{findings | selectattr('severity', 'eq', 'high') | list | length}}
- Medium: {{findings | selectattr('severity', 'eq', 'medium') | list | length}}
- Low: {{findings | selectattr('severity', 'eq', 'low') | list | length}}
- Info: {{findings | selectattr('severity', 'eq', 'info') | list | length}}

{% for f in findings %}
### Finding: {{f.title}}
- ID: {{f.id}}
- Severity: {{f.severity}} | CVSS: {{f.cvss_score}}
- CWE: {{f.cwe_id}} ({{f.cwe_name}})
- Status: {{f.validation_verdict}}
- Asset: {{f.asset}}
- Endpoint: {{f.endpoint}}
- Description: {{f.description}}
- Evidence summary: {{f.evidence_summary | truncate(500)}}
- Remediation: {{f.remediation_guidance | truncate(500)}}
{% endfor %}

## Compliance Context
- Frameworks: {{engagement.compliance_frameworks | join(', ')}}
- Compliance mapping: {{compliance_mapping | format_compliance}}

## Report Type: {{report_type}}
{% if report_type == 'executive' %}
Generate a 2-3 page executive summary with risk posture, key findings,
and strategic recommendations. No technical details.
{% elif report_type == 'technical' %}
Generate a full technical report with detailed finding descriptions,
evidence, reproduction steps, and remediation guidance.
{% elif report_type == 'compliance' %}
Generate a compliance-focused report mapping findings to control
frameworks with gap analysis.
{% endif %}

## Required Output (JSON)
{
  "report_title": "Report title",
  "report_type": "executive | technical | compliance",
  "status": "draft",
  "sections": [
    {
      "heading": "Section title",
      "content": "Markdown content for this section",
      "order": 1
    }
  ],
  "metadata": {
    "generated_at": "ISO timestamp",
    "model_version": "claude-opus-4-6",
    "finding_count": 0,
    "confidence": 0.0-1.0,
    "disclaimer": "AI-GENERATED DRAFT — Requires analyst review before publication"
  }
}
```

---

## 3. Data Flow

### 3.1 Full Enrichment Pipeline (Async — Kafka-driven)

```
Scanner completes
       │
       ▼
┌──────────────┐     ┌───────────────┐     ┌──────────────────────┐
│ Scan Results │────▶│ Findings      │────▶│ Kafka Topic:         │
│ (raw)        │     │ Normalization │     │ finding.normalized   │
└──────────────┘     │ Engine        │     └──────────┬───────────┘
                     └───────────────┘                │
                                                      ▼
                     ┌────────────────────────────────────────────┐
                     │        AI Analyst Assistant Service         │
                     │                                            │
                     │  ┌─────────────────────────────────────┐  │
                     │  │  1. Context Builder                  │  │
                     │  │     • Load finding + evidence        │  │
                     │  │     • Query pgvector for similar     │  │
                     │  │       historical findings            │  │
                     │  │     • Load asset metadata            │  │
                     │  │     • Load scanner rule FP rates     │  │
                     │  │     • Check Redis cache              │  │
                     │  └──────────────┬──────────────────────┘  │
                     │                 │                          │
                     │  ┌──────────────▼──────────────────────┐  │
                     │  │  2. LLM Gateway                      │  │
                     │  │     • Select prompt template          │  │
                     │  │     • Render with Jinja2              │  │
                     │  │     • Call Claude API                 │  │
                     │  │       - model: claude-opus-4-6        │  │
                     │  │       - max_tokens: per-stage limit   │  │
                     │  │       - temperature: 0.1 (low var.)  │  │
                     │  │     • Parse JSON response             │  │
                     │  │     • Validate against schema         │  │
                     │  │     • Cache result in Redis           │  │
                     │  └──────────────┬──────────────────────┘  │
                     │                 │                          │
                     │  ┌──────────────▼──────────────────────┐  │
                     │  │  3. Result Writer                    │  │
                     │  │     • Write to PostgreSQL            │  │
                     │  │     • Publish enrichment event       │  │
                     │  │     • Log to audit trail             │  │
                     │  └─────────────────────────────────────┘  │
                     └──────────────────────┬─────────────────────┘
                                            │
                     ┌──────────────────────▼─────────────────────┐
                     │  Kafka Topic: finding.ai_enriched           │
                     └──────────────────────┬─────────────────────┘
                                            │
                     ┌──────────────────────▼─────────────────────┐
                     │  WebSocket Push → Analyst Workbench UI      │
                     │  (finding card updated with AI badges)      │
                     └────────────────────────────────────────────┘
```

### 3.2 On-Demand Analysis (Sync — API-driven)

```
Analyst clicks              API Gateway                AI Assistant Service
"Regenerate AI"             (authenticated)
      │                          │                            │
      │   POST /ai/analyze       │                            │
      │─────────────────────────▶│  POST /v1/analyze          │
      │                          │───────────────────────────▶│
      │                          │                            │
      │                          │                     ┌──────▼──────┐
      │                          │                     │ Validate    │
      │                          │                     │ request +   │
      │                          │                     │ permissions │
      │                          │                     └──────┬──────┘
      │                          │                            │
      │                          │                     ┌──────▼──────┐
      │                          │                     │ Build       │
      │                          │                     │ context     │
      │                          │                     │ (RAG query) │
      │                          │                     └──────┬──────┘
      │                          │                            │
      │                          │                     ┌──────▼──────┐
      │                          │                     │ Call Claude │
      │                          │                     │ API         │
      │                          │                     │ (streaming) │
      │                          │                     └──────┬──────┘
      │                          │                            │
      │                          │    SSE stream              │
      │◀─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│◀─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─│
      │   (partial results       │                            │
      │    streamed to UI)       │                     ┌──────▼──────┐
      │                          │                     │ Persist     │
      │                          │   200 OK (final)    │ results     │
      │◀─────────────────────────│◀───────────────────│ (DB + audit)│
      │                          │                     └─────────────┘
      │
 Analyst reviews
 AI output in UI
      │
      ▼
 Analyst approves/
 edits/overrides
```

### 3.3 Report Drafting Flow (with Publish Guard)

```
Analyst clicks                                           AI Service
"Draft Report"                                               │
      │                                                      │
      │  POST /v1/reports/draft                              │
      │─────────────────────────────────────────────────────▶│
      │                                                      │
      │                                          ┌───────────▼──────────┐
      │                                          │ Load ALL validated    │
      │                                          │ findings for          │
      │                                          │ engagement            │
      │                                          │ (status=validated     │
      │                                          │  only — never uses   │
      │                                          │  unvalidated          │
      │                                          │  findings)            │
      │                                          └───────────┬──────────┘
      │                                                      │
      │                                          ┌───────────▼──────────┐
      │                                          │ Build report prompt  │
      │                                          │ with compliance      │
      │                                          │ mapping              │
      │                                          └───────────┬──────────┘
      │                                                      │
      │                                          ┌───────────▼──────────┐
      │                                          │ Claude API call      │
      │                                          │ (large context,      │
      │                                          │  extended thinking)  │
      │                                          └───────────┬──────────┘
      │                                                      │
      │                                          ┌───────────▼──────────┐
      │   Draft returned                         │ Store as DRAFT       │
      │◀─────────────────────────────────────────│ published = false    │
      │                                          │ requires_approval =  │
      │                                          │   true               │
      │                                          └──────────────────────┘
      │
 Analyst reviews
 draft in editor
      │
      ├──── Edits content ──────▶ PATCH /v1/reports/{id}
      │                          (saves analyst edits)
      │
      ├──── Approves draft ─────▶ POST /v1/reports/{id}/approve
      │                          (sets approved_by, approved_at)
      │                          ▲
      │                          │ REQUIRES: role = lead_analyst | admin
      │                          │ REQUIRES: approved_by ≠ drafted_by
      │                          │   (four-eyes principle)
      │
      └──── Publishes ──────────▶ POST /v1/reports/{id}/publish
                                  ▲
                                  │ BLOCKED unless:
                                  │   1. approved_by is set
                                  │   2. approved_at is set
                                  │   3. User has report:publish perm
                                  │   4. All critical/high findings
                                  │      have remediation guidance
                                  │
                                  │ The AI module CANNOT call this
                                  │ endpoint. Only human analysts
                                  │ can publish reports.
```

### 3.4 Data Flow per Pipeline Stage

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Flow Matrix                              │
├──────────────┬──────────────────┬───────────────────────────────┤
│ Stage        │ Input            │ Output                        │
├──────────────┼──────────────────┼───────────────────────────────┤
│ Vuln Summary │ finding          │ executive_summary             │
│              │ evidence         │ technical_summary             │
│              │ asset_context    │ attack_scenario               │
│              │ similar_findings │ data_at_risk                  │
│              │ (RAG)            │ confidence + reasoning        │
├──────────────┼──────────────────┼───────────────────────────────┤
│ FP Detection │ finding          │ verdict (TP/FP spectrum)      │
│              │ evidence         │ fp_probability (0-1)          │
│              │ scanner_rule_fp  │ reasoning[]                   │
│              │ verified_similar │ evidence_quality              │
│              │ (RAG)            │ manual_verification_steps[]   │
├──────────────┼──────────────────┼───────────────────────────────┤
│ Risk Prior.  │ findings[]       │ prioritized_findings[]        │
│              │ asset_metadata   │ risk_scores                   │
│              │ threat_intel     │ attack_chains                 │
│              │ compliance_ctx   │ compliance_impact             │
│              │                  │ investigation_order           │
├──────────────┼──────────────────┼───────────────────────────────┤
│ Remediation  │ finding          │ summary + detailed_steps      │
│              │ evidence         │ code_examples (before/after)  │
│              │ tech_stack       │ defense_in_depth[]            │
│              │ source_code      │ testing_verification[]        │
│              │ (if SAST)        │ references[]                  │
├──────────────┼──────────────────┼───────────────────────────────┤
│ Report Draft │ engagement       │ report_sections[]             │
│              │ validated_       │ executive_summary             │
│              │   findings[]     │ status: "draft"               │
│              │ compliance_map   │ published: false              │
│              │ remediation[]    │ disclaimer: "AI-GENERATED"    │
└──────────────┴──────────────────┴───────────────────────────────┘
```

### 3.5 Caching Strategy

```
Request arrives
      │
      ▼
┌─────────────┐    cache hit     ┌──────────────────┐
│ Generate    │─────────────────▶│ Return cached    │
│ cache key   │                  │ result           │
│ (SHA-256 of │                  │ (with cache_hit  │
│  input hash)│                  │  flag for UI)    │
└──────┬──────┘                  └──────────────────┘
       │ cache miss
       ▼
┌─────────────┐
│ Call Claude │
│ API         │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Cache in    │
│ Redis       │
│ TTL: stage- │
│ dependent   │
│ Summary: 4h │
│ FP Det: 24h │
│ Remed: 12h  │
│ Report: 1h  │
└─────────────┘
```

### 3.6 Embedding & RAG Flow

```
Historical finding validated by analyst
      │
      ▼
┌──────────────────┐
│ Generate         │
│ embedding        │
│ (text-embedding) │
└───────┬──────────┘
        │
        ▼
┌──────────────────┐
│ Store in         │
│ pgvector         │
│ (findings_       │
│  embeddings)     │
└──────────────────┘

                    ... later, new finding arrives ...

New finding
      │
      ▼
┌──────────────────┐
│ Generate         │
│ embedding for    │
│ new finding      │
└───────┬──────────┘
        │
        ▼
┌──────────────────┐     ┌──────────────────────────────────┐
│ pgvector         │────▶│ Top-K similar findings           │
│ cosine           │     │ (with analyst verdicts,           │
│ similarity       │     │  remediation applied,             │
│ search           │     │  outcome data)                    │
└──────────────────┘     └──────────────────────────────────┘
        │
        ▼
  Injected into prompt as "Historical Context"
  (grounds AI response in real organizational data)
```
