# AER-1 Conformant Verifier — MasterD

An **independent** AER-1 verifier (Python · stdlib only), written against the
draft text (`draft-zambo-aer1`) — not copied from the reference kit.

**Status:** all conformance vectors pass.

| Corpus | Result |
|---|---|
| receipt core (8 valid + 25 invalid) | 33 / 33 |
| chain v07 (Section 7 hardened) | 28 / 28 |
| chain v06 (legacy regression gate) | 7 / 7 |
| commitment (Section 7.3) | 8 / 8 |
| merkle (canonical + legacy leaves + must_not_equal) | 8 / 8 |
| **total** | **84 / 84** |

Verified against the published vectors; agrees with the reference runner
(`aer-1/conformance.py`, which prints `CONFORMANCE OK`) vector for vector.

## Files
- `verifier.py` — the verifier (core tier + chain v07/v06 + commitment + merkle)

## What it checks (core tier, Section 3)
`id`, `receipt_schema_version`, `created_at`, `tool`, `provenance_class`,
`canonical_bytes`, `output_hash`, `verification_status` — plus the outer/inner
agreement rule (outer fields must equal what `canonical_bytes` commits), which
rejects tampered provenance and version downgrade.

## Run
```
git clone https://gitlab.com/rambozambodotdev/zambo
python3 verifier.py zambo/aer-1
```

Spec: https://datatracker.ietf.org/doc/draft-zambo-aer1/
Registry: https://rambozambodotdev.gitlab.io/registry.html

_MasterD · Arkie AI · 2026-10-09_
