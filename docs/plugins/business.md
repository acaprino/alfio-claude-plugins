# Business Plugin

> Navigate tech law without a lawyer on retainer. Contract review, GDPR/CCPA compliance, IP protection, and risk assessment tailored to software businesses.

## Agents

### `privacy-doc-generator`

Drafts privacy compliance documents -- Privacy Policies, Cookie Policies, DPAs, consent notices, DPIA reports. Covers EU/Italy (GDPR, ePrivacy, Codice Privacy) with modular support for CCPA, LGPD, and FADP.

| | |
|---|---|
| **Model** | `opus` |
| **Use for** | Drafting or auditing privacy and data protection documents for websites, apps, or SaaS products |

**Invocation:**
```
Use the privacy-doc-generator agent to draft a [privacy policy/cookie policy/DPA] for [product]
```

**Workflow:** Context gathering (jurisdiction, business profile, processing activities, cookie assessment) -> Risk analysis (DPIA triggers, transfer risks, sector overlays) -> Document generation -> Validation -> Output with evidence pack.

**Key features:**
- ROPA-driven generation -- builds a structured processing model before drafting
- Normative references on every clause (article, guideline, recital)
- Legal research phase with source verification against official texts
- Uncertainty markers (`[NON SPECIFICATO]`, `[REQUIRES LEGAL REVIEW]`, `[ASSUMPTION]`)

---

## Skills

### `legal-advisor`

Technology law advisor covering compliance and risk mitigation.

| | |
|---|---|
| **Invoke** | Skill reference |
| **Use for** | Contract review, compliance, IP protection, privacy policies, risk assessment |

**Core capabilities:**
- **Contract Management** - Review, negotiate, draft, and manage contracts
- **Privacy & Data Protection** - GDPR, CCPA, data processing agreements
- **Intellectual Property** - Patents, trademarks, copyrights, trade secrets
- **Compliance** - Regulatory mapping, policy development, audit preparation
- **Risk Management** - Legal risk assessment, mitigation strategies, insurance

**Legal domains covered:**
| Domain | Topics |
|--------|--------|
| Software | Licensing, SaaS agreements, open source |
| Privacy | GDPR, CCPA, data transfers, consent |
| IP | Patents, trademarks, copyrights, trade secrets |
| Employment | Agreements, NDAs, non-competes, IP assignments |
| Corporate | Formation, governance, equity, M&A |

---

**Related:** [stripe](stripe.md) (payment integration and compliance) | [digital-marketing](digital-marketing.md) (SEO and content strategy)
