# Defect report: packet-builder records a digest that does not describe what it embeds

Date: 2026-08-11
Plugin: `peer-review` (1.2.0 installed, source at `plugins/peer-review/`)
Severity: run-invalidating on any CRLF repository. Blocks every `/peer-review:review` run on Windows checkouts.
Status: root cause confirmed against source. Fix proposed, not applied.

## Symptom

`/peer-review:review docs/superpowers/specs/2026-08-11-repo-hygiene-split-design.md` aborted at
Phase 1 step 4, the independent digest recheck. The three values R15 requires to agree:

| Value | bytes | sha256 |
|---|---|---|
| 1. Source recomputed from disk | 21601 | `6269bce1…` |
| 2. Digest recorded in `00-packet.md` | 21601 | `6269bce1…` |
| 3. Text actually embedded in `00-packet.md` | 21271 | `f70e6af8…` |

The delta is exactly the file's line count:

```
CRLF terminators on disk: 330
21601 - 330 = 21271
```

The packet embedded the artifact with LF endings while recording the digest of the on-disk
CRLF bytes. The two can never agree on a CRLF file.

The `packet-builder` reported its own self-check green, stating the embedded slice was
"byte-identical to the source file (same sha256)". It was not.

## Root cause

Not model error. The agent's own checklist cannot detect this failure, because it verifies
the one pair that cannot fail and never the pair that can.

`plugins/peer-review/agents/packet-builder.md:86-87` tells the agent to compute both values
from the file on disk, in binary:

```
bytes: $(stat -c %s <artifact>)   [or wc -c]
sha256: python -c "...open(sys.argv[1],'rb').read()..." <artifact>
```

`'rb'` and `wc -c` both count CRLF. So value 2 is a faithful description of the source.

The embedding, however, is produced by the model: it reads the artifact and writes the text
into `00-packet.md`. That path carries LF. Nothing in the agent's instructions requires the
written bytes to equal the hashed bytes.

The self-check at `packet-builder.md:109-110` then closes the loop in the wrong place:

> `bytes` and `sha256` recorded immediately above the embedded artifact, and match **the
> artifact file on disk**.

That check compares value 2 against value 1. Those always agree, because both are computed
from the same file by the same method. The check never compares value 2 against value 3,
which is the only comparison that can catch a corrupted embedding. An agent following its
instructions exactly will report green while shipping a packet whose digest is a lie.

## Why the run still stopped

The command was written knowing this. `commands/review.md` Phase 1 step 4 explicitly refuses
to trust the agent and computes all three values itself, with the reason stated inline:

> Checking only the recorded digest line (step 2) proves nothing about whether the embedding
> below it was truncated or altered after that line was written.

The command caught the agent. Defense in depth worked exactly as designed, and that is the
only reason a corrupted packet did not reach the transport. This report is about removing the
defect, not about the check that contained it.

## Fix

Three candidates. The first two are wrong in instructive ways.

**Rejected: hash what is embedded instead of what is on disk.** Makes 2 and 3 agree by
computing the digest over the normalized text. But then 1 and 2 disagree, and the command
aborts anyway, correctly: R15 requires source, packet embedding, and outgoing request to be
byte-identical, and a normalized embedding is not byte-identical to a CRLF source. This
converts a detected defect into a differently-detected defect.

**Rejected: normalize the source to LF and declare it.** Record the normalized digest as the
packet's digest and the raw digest as provenance. Defensible, but it weakens R15 from
"byte-identical" to "byte-identical after a declared transformation". That is a protocol
amendment, and it should not be smuggled in as a bug fix.

**Proposed: splice the source bytes in, never retype them.** `00-packet.md` is assembled by a
script that writes the header and digest block, then concatenates the artifact's raw bytes
read in binary, then the remaining sections. The model composes every section except the
embedded artifact, which it never reproduces.

This is correct for CRLF because nothing normalizes, and it also eliminates a larger risk the
current design accepts silently: a model retyping a 12 KB document can alter it. Byte-splicing
removes that entire class of corruption rather than detecting it after the fact.

Alongside it, correct the self-check at `packet-builder.md:109-110` so it compares the
embedded slice against the recorded digest, not the source file against the recorded digest.
A checklist item that cannot fail is worse than no item, because it reports confidence.

## Second finding: R15 verifies fidelity, not identity

Surfaced by the same abort, and independent of it.

The same run had a second problem the protocol has no requirement for: the artifact on disk
was not the document under discussion. The working tree had been reverted to a previously
committed draft, discarding an uncommitted rewrite. R15 would not have noticed. It verifies
that the packet faithfully carries the file; it has nothing to say about whether the file is
the one the operator meant to put on trial.

Had the discarded rewrite also been LF, all three digests would have agreed, the run would
have proceeded, and the challenger would have spent three rounds on a document its operator
never wrote. The digest check caught it here only as a side effect of the CRLF bug.

**Proposed:** the packet records the artifact's git provenance alongside its digest: the
commit the file matches, or `uncommitted changes` when the working tree differs from HEAD,
or `untracked`. The consent gate then displays that line with the destination and byte size.
An operator seeing `artifact matches HEAD e1cbd27 (clean)` when they expected to be reviewing
unsaved edits has the information to stop, and it costs one `git status --porcelain` plus one
`git rev-parse HEAD`.

This does not make the protocol responsible for choosing the artifact. It makes the choice
visible at the one moment the operator is already being asked to look before egress.

## Reproduction

Any repository whose checkout produces CRLF. On this machine:

```bash
git config core.autocrlf          # true on this checkout
printf 'a\r\nb\r\n' > /tmp/x.md
/peer-review:review /tmp/x.md     # aborts at Phase 1 step 4
```

The workaround used to unblock the run under discussion was to normalize the artifact to LF
before building the packet. That is a workaround, not a fix, on two counts: it depends on the
operator noticing, and it does not even hold for the file it was applied to. This checkout has
`core.autocrlf=true` and no `.gitattributes`, so the normalized file reverts to CRLF the next
time git writes it, which git itself warns about on every commit of that file.

A repository-level `.gitattributes` pinning `*.md text eol=lf` would close the whole class
independently of the plugin fix. It is deliberately not proposed here: with `autocrlf=true`
and no existing attributes file, adding one renormalizes on the next checkout and touches far
more than this defect warrants. It is a separate decision with its own blast radius, and it
does not remove the need for the splice fix, which is what makes the packet correct for any
line ending rather than for one chosen line ending.
