# License analysis: obligations, not a matrix

The wrong model is a compatibility table ("MIT: compatible with BSD, Apache-2.0; GPL-3.0: incompatible"). It is wrong in both directions: MIT/Expat code can legally live inside a GPL combined work (MIT is GPL-compatible), and two licenses a table calls "compatible" can still create unmet obligations in a specific distribution model. The canonical trap: GPL-2.0-only and GPL-3.0 are NOT intercompatible even though a naive table groups them as "GPL family"; only "GPL-2.0-or-later" bridges them.

The right model asks three questions per dependency, in order.

## Step 0: Establish the project's posture first

Before judging any dependency, record:

1. **Project license** (its own LICENSE file, not an assumption).
2. **Distribution model**: shipped binary or installable app; library published for reuse; SaaS / network service; internal-only tooling. Obligations hinge on this more than on the license pair.
3. **Linking/combination model** where relevant: static vs dynamic linking, separate process, build-time-only tool. Weak-copyleft obligations often turn on this.

If any of the three is unknown, the license section reports its findings conditionally ("if distributed as ...") and lists the missing posture facts as UNKNOWN.

## Obligation categories

Classify each dependency's SPDX identifier into a category; the category, not a verdict, is what the finding states.

| Category | Examples | Obligation sketch | Typical trigger |
|---|---|---|---|
| Permissive | MIT, ISC, BSD-2/3-Clause, Apache-2.0, Zlib | Preserve notices; Apache-2.0 adds a patent grant and NOTICE-file handling | Distribution |
| Weak copyleft | LGPL-2.1/3.0, MPL-2.0, EPL-2.0 | Source obligations scoped to the covered files/library; combination mechanics matter (linking, file-level) | Distribution |
| Strong copyleft | GPL-2.0-only, GPL-2.0-or-later, GPL-3.0 | Combined work distributed under the GPL; full corresponding source on distribution | Distribution |
| Network copyleft | AGPL-3.0 | GPL obligations extended to users interacting over a network | Network use (SaaS counts) |
| Source-available / restricted | BUSL-1.1, SSPL, Elastic-2.0, Commons-Clause riders, "proprietary" | Read the actual grant; usage limits (competition clauses, production limits) may bind regardless of distribution | Varies; often use itself |
| Public-domain-like | CC0-1.0, Unlicense, 0BSD | Effectively no obligations | - |
| Unknown / custom | missing, "SEE LICENSE IN ...", nonstandard text | Cannot be classified mechanically | - |

## Finding format

Per dependency with a non-permissive category (or permissive with unusual mechanics, e.g. Apache-2.0 NOTICE files present):

```
<package> <version>: <SPDX id as reported> (<category>)
Obligation: <one sentence, e.g. "distributing a combined work triggers GPL-3.0 source obligations for the whole work">
Trigger: <distribution | network use | production use per grant | none in current posture>
Question for the owner: <the concrete decision, e.g. "is copyleft acceptable for the shipped CLI, or should this dependency be replaced?">
```

Wording rules, binding:

- Copyleft findings say "potential copyleft obligation: inspect combination/distribution model". They never say "incompatible with <project license>".
- A dependency whose obligations do not trigger under the recorded posture (e.g. GPL dependency in an internal-only tool, AGPL absent network exposure) is reported as informational with its trigger condition spelled out, not as a violation.
- Dual-licensed packages ("MIT OR Apache-2.0", "GPL-2.0 OR commercial") report both options; the project may choose either.
- Unknown/custom licenses go to a **requires legal review** list with the raw license string and the package's repository URL. No automatic verdict, ever.

## Tool caveats

- Manifest `license` fields are declarations, not guarantees. When a finding matters (copyleft, restricted, unknown), open the package's actual LICENSE file before reporting; note when declaration and file disagree.
- License inventory tools report the top-level declaration and can miss vendored code, dual licensing, or per-file exceptions ("GPL with classpath exception"). Treat tool output as TOOL-REPORTED for the declaration only; the obligation classification is INFERRED and says so.
- This analysis is engineering triage, not legal advice; the "requires legal review" list exists precisely because the final call on restricted and unknown licenses belongs to a human with legal context.
