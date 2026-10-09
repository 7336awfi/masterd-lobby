#!/usr/bin/env python3
"""
MasterD — AER-1 verifier (core tier, independent clean-room implementation)

Spec: draft-zambo-aer1-12 (IETF Internet-Draft)
Implements the core-tier check on the eight Section 3 members:
  id, receipt_schema_version, created_at, tool, provenance_class,
  canonical_bytes, output_hash, verification_status

Conformance target (from IMPLEMENTING.md):
  - all valid vectors verify
  - all invalid vectors rejected for the reason their filename encodes
  - chain v07 / v06 / commitment / merkle vectors behave as specified

This is an INDEPENDENT implementation: written against the draft text and
the rejection-reason filenames, not copied from aer-1/conformance.py.
"""
import base64, binascii, hashlib, json, re, sys, unicodedata
from datetime import datetime, timezone

# ---- core-tier constants -------------------------------------------------
PROVENANCE_RE = re.compile(
    r"^(?:EXECUTED BY .+|OBSERVED VIA GATEWAY|LOGGED BY AGENT)$"
)
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)
RFC3339_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}[Tt]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[Zz]|[+-]\d{2}:\d{2})$"
)
STRICT_B64_RE = re.compile(r"^[A-Za-z0-9+/]*={0,2}$")


class Reject(Exception):
    pass


def _check_id(rid):
    """Section 3: lowercase UUID-shaped id. Core tier accepts any version."""
    if not isinstance(rid, str):
        raise Reject("bad-id: id is not a string")
    # uppercase letters are not allowed in the core tier
    if rid != rid.lower():
        raise Reject("uppercase-id: id must be lowercase")
    if rid != rid.strip():
        raise Reject("id-trailing-newline: id has leading/trailing whitespace")
    if not UUID_RE.match(rid):
        raise Reject("bad-id: not UUID-shaped")
    return True


def _check_schema_version(v):
    """Core tier: non-empty string (strict tier pins exactly '0.3')."""
    if not isinstance(v, str) or v == "":
        raise Reject("version: receipt_schema_version must be a non-empty string")
    return True


def _check_created_at(s):
    """Calendar-valid RFC 3339, with a real day-of-month check."""
    if not isinstance(s, str):
        raise Reject("bad-created-at: not a string")
    if not RFC3339_RE.match(s):
        raise Reject("bad-created-at: not RFC 3339")
    # calendar validity: parse and confirm the day exists (rejects Feb 29 non-leap etc.)
    try:
        core = s.rstrip("Zz")
        # strip timezone offset for the local-calendar parse
        m = re.match(r"^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})", core)
        if not m:
            raise Reject("bad-created-at: unparseable")
        y, mo, d, hh, mm, ss = (int(x) for x in m.groups())
        if not (1 <= mo <= 12):
            raise Reject("impossible-date: month out of range")
        if not (0 <= hh <= 23 and 0 <= mm <= 59 and 0 <= ss <= 60):
            raise Reject("impossible-date: time out of range")
        # datetime() will raise on Feb 29 in a non-leap year
        datetime(y, mo, d)
    except Reject:
        raise
    except ValueError as e:
        msg = str(e)
        if "day is out of range" in msg:
            raise Reject("feb29-non-leap: day out of range for month")
        raise Reject("impossible-date: " + msg)
    # timezone offset range check
    off = re.search(r"([+-])(\d{2}):(\d{2})$", s)
    if off:
        oh, om = int(off.group(2)), int(off.group(3))
        if oh > 23 or om > 59:
            raise Reject("bad-offset-range: tz offset out of range")
    return True


def _check_tool(t):
    if not isinstance(t, dict):
        raise Reject("tool-not-object: tool is not an object")
    for k in ("name", "version", "scope"):
        v = t.get(k)
        if not isinstance(v, str) or v == "":
            raise Reject(f"tool-empty-{k}: tool.{k} must be a non-empty string")
    return True


def _check_provenance(p):
    if not isinstance(p, str):
        raise Reject("bad-provenance: not a string")
    if p != p.rstrip("\n") or "\n" in p:
        raise Reject("provenance-trailing-newline: provenance has trailing newline")
    if not PROVENANCE_RE.match(p):
        raise Reject("bad-provenance: not one of the three core classes")
    return True


def _check_canonical_bytes(cb):
    """Strict base64, strict UTF-8 after decoding. Returns the decoded bytes."""
    if not isinstance(cb, str):
        raise Reject("bytes-not-base64: canonical_bytes not a string")
    if not STRICT_B64_RE.match(cb) or len(cb) % 4 != 0:
        raise Reject("base64: not strict/padded base64")
    try:
        raw = base64.b64decode(cb, validate=True)
    except (binascii.Error, ValueError):
        raise Reject("bytes-not-base64: invalid base64")
    try:
        raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise Reject("non-utf8-bytes: decoded bytes are not valid UTF-8")
    return raw


def _check_output_hash(oh, raw):
    if not isinstance(oh, str):
        raise Reject("missing-output-hash: output_hash not a string")
    if not oh.startswith("sha256:"):
        raise Reject("hash-bad-format: must start with 'sha256:'")
    hexpart = oh[len("sha256:"):]
    if not re.fullmatch(r"[0-9a-f]{64}", hexpart):
        raise Reject("hash-bad-format: not 64 lowercase hex chars")
    want = hashlib.sha256(raw).hexdigest()
    if want != hexpart:
        raise Reject("hash-mismatch: output_hash does not match canonical_bytes")
    return True


def _check_verification_status(vs):
    if vs != "verified":
        raise Reject("bad-verification-status: must be exactly 'verified'")
    return True


def _check_commitment(rec, raw):
    """Section: when canonical_bytes commits issuer_claims / version, the OUTER
    fields MUST equal the committed ones (draft-zambo-aer1-12). This is what
    catches tampered-provenance and version-downgrade."""
    try:
        inner = json.loads(raw.decode("utf-8"))
    except Exception:
        return True  # not a JSON payload convention; nothing to cross-check
    if not isinstance(inner, dict):
        return True
    claims = inner.get("issuer_claims")
    if isinstance(claims, dict) and "provenance_class" in claims:
        if claims["provenance_class"] != rec.get("provenance_class"):
            raise Reject(
                "tampered-provenance: outer provenance_class %r != committed %r"
                % (rec.get("provenance_class"), claims["provenance_class"])
            )
    if "receipt_schema_version" in inner:
        if inner["receipt_schema_version"] != rec.get("receipt_schema_version"):
            raise Reject(
                "version-downgrade: outer schema version %r != committed %r"
                % (rec.get("receipt_schema_version"), inner["receipt_schema_version"])
            )
    return True


def verify_receipt(rec):
    """Core-tier verification. Raises Reject(reason) on failure; returns True."""
    if not isinstance(rec, dict):
        raise Reject("not-an-object: receipt is not an object")
    _check_id(rec.get("id"))
    _check_schema_version(rec.get("receipt_schema_version"))
    _check_created_at(rec.get("created_at"))
    _check_tool(rec.get("tool"))
    _check_provenance(rec.get("provenance_class"))
    raw = _check_canonical_bytes(rec.get("canonical_bytes"))
    _check_output_hash(rec.get("output_hash"), raw)
    _check_verification_status(rec.get("verification_status"))
    _check_commitment(rec, raw)
    return True


# ---- vector runner -------------------------------------------------------
def _load(path):
    with open(path, "rb") as fh:
        return json.loads(fh.read().decode("utf-8"))


def run_corpus(valid_dir, invalid_dir):
    import os
    ok = fail = 0
    print("== valid vectors ==")
    for name in sorted(os.listdir(valid_dir)):
        if not name.endswith(".json"):
            continue
        try:
            verify_receipt(_load(os.path.join(valid_dir, name)))
            print(f"  [PASS] {name}")
            ok += 1
        except Reject as e:
            print(f"  [FAIL] {name}: {e}")
            fail += 1
    print("== invalid vectors ==")
    for name in sorted(os.listdir(invalid_dir)):
        if not name.endswith(".json"):
            continue
        try:
            verify_receipt(_load(os.path.join(invalid_dir, name)))
            print(f"  [FAIL] {name}: accepted but should be rejected")
            fail += 1
        except Reject as e:
            print(f"  [PASS] {name}: rejected ({e})")
            ok += 1
    print(f"\nRESULT: {ok} pass, {fail} fail")
    return fail == 0


if __name__ == "__main__":
    base = sys.argv[1] if len(sys.argv) > 1 else "zambo/aer-1"
    good = run_corpus(f"{base}/test-vectors/valid", f"{base}/test-vectors/invalid")
    sys.exit(0 if good else 1)


# ---- Section 7: hash-chained job timelines (v07 construction) -------------
CHAIN_FIELDS = ["prev_digest", "seq", "job_id", "close", "id", "tool",
                "provenance_class", "output_hash"]


def entry_digest(entry):
    """Section 7 (-07) entry digest: SHA-256 over UTF-8 of the canonical JSON
    object {prev_digest, seq, job_id, close, id, tool, provenance_class,
    output_hash}, keys sorted by Unicode code point, no whitespace.
    output_hash is RECOMPUTED as lowercase hex sha256 of the base64-decoded
    canonical_bytes. A missing close member digests as false."""
    raw = base64.b64decode(entry["canonical_bytes"], validate=True)
    output_hash = hashlib.sha256(raw).hexdigest()
    seq = entry["seq"]
    if isinstance(seq, float) and seq.is_integer():
        seq = int(seq)
    payload = {
        "prev_digest": entry["prev_digest"],
        "seq": seq,
        "job_id": entry["job_id"],
        "close": entry.get("close", False),
        "id": entry["id"],
        "tool": entry["tool"],
        "provenance_class": entry["provenance_class"],
        "output_hash": output_hash,
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


B64_RE = STRICT_B64_RE


def verify_chain(timeline):
    """Verify one v07 chain timeline. Raises Reject on failure."""
    if not isinstance(timeline, list) or not timeline:
        raise Reject("empty-chain: timeline is not a non-empty list")
    prev = None
    job = None
    for i, e in enumerate(timeline):
        if not isinstance(e, dict):
            raise Reject(f"entry {i} is not an object")
        cb = e.get("canonical_bytes")
        if not isinstance(cb, str) or not STRICT_B64_RE.match(cb) or len(cb) % 4 != 0:
            raise Reject(f"entry {i} canonical_bytes is not valid base64")
        try:
            base64.b64decode(cb, validate=True)
        except (binascii.Error, ValueError):
            raise Reject(f"entry {i} canonical_bytes is not valid base64")
        for m in ("id", "tool", "provenance_class", "job_id", "prev_digest"):
            if not isinstance(e.get(m), str) or not e[m]:
                raise Reject(f"entry {i} missing {m}")
        seq = e.get("seq")
        if isinstance(seq, bool) or not (
                isinstance(seq, int) or (isinstance(seq, float) and seq.is_integer())):
            raise Reject(f"entry {i} seq is not an integer")
        seq = int(seq)
        if seq != i + 1:
            raise Reject(f"entry {i} seq {seq} breaks contiguity (expected {i+1})")
        if job is None:
            job = e["job_id"]
        elif e["job_id"] != job:
            raise Reject(f"entry {i} job_id mixes jobs")
        if i == 0:
            if e["prev_digest"] != "0" * 64:
                raise Reject("entry 0 prev_digest is not 64 zero characters")
        elif e["prev_digest"] != prev:
            raise Reject(f"entry {i} prev_digest does not match entry {i-1}")
        if "close" in e and not isinstance(e["close"], bool):
            raise Reject(f"entry {i} close is not a boolean")
        if i < len(timeline) - 1 and e.get("close") is True:
            raise Reject(f"entry {i} carries close:true before the last entry")
        prev = entry_digest(e)
    return True


# ---- Section 7 (v06 legacy regression construction) -----------------------
def verify_chain_v06(timeline):
    """Legacy -06 chain: entry digest = sha256 of the base64-DECODED
    canonical_bytes (strict, fail closed); genesis prev_digest = 64 zeros;
    each later prev_digest = lowercase hex digest of the previous entry's
    decoded bytes; LAST entry MUST carry close == True. Raises Reject."""
    if not isinstance(timeline, list) or not timeline:
        raise Reject("empty-chain: timeline is not a non-empty list")
    prev = None
    for i, e in enumerate(timeline):
        if not isinstance(e, dict):
            raise Reject(f"entry {i} is not an object")
        cb = e.get("canonical_bytes")
        if not isinstance(cb, str) or not STRICT_B64_RE.match(cb) or len(cb) % 4 != 0:
            raise Reject(f"entry {i} canonical_bytes is not valid base64")
        try:
            raw = base64.b64decode(cb, validate=True)
        except (binascii.Error, ValueError):
            raise Reject(f"entry {i} canonical_bytes is not valid base64")
        digest = hashlib.sha256(raw).hexdigest()
        pd = e.get("prev_digest")
        if i == 0:
            if not isinstance(pd, str) or pd != "0" * 64:
                raise Reject("entry 0 prev_digest is not 64 zero characters")
        elif not isinstance(pd, str) or pd != prev:
            raise Reject(f"entry {i} prev_digest does not match the digest of entry {i-1}")
        prev = digest
    last = timeline[-1]
    if not isinstance(last, dict) or last.get("close") is not True:
        raise Reject("last entry does not carry close: true")
    return True


# ---- Section 7.3: external chain commitment artifact ----------------------
def verify_commitment(timeline, commitment):
    """A commitment published OUTSIDE the chain binds {job_id,
    final_entry_digest, entry_count, published_at}. Raises Reject."""
    if not isinstance(timeline, list) or not timeline:
        raise Reject("timeline is not a non-empty list")
    if not isinstance(commitment, dict):
        raise Reject("commitment is not an object")
    jid = commitment.get("job_id")
    if not isinstance(jid, str) or not jid:
        raise Reject("commitment.job_id is not a non-empty string")
    for e in timeline:
        if e.get("job_id") != jid:
            raise Reject("commitment.job_id does not match every entry's job_id")
    fed = commitment.get("final_entry_digest")
    if not isinstance(fed, str) or not re.fullmatch(r"[0-9a-f]{64}", fed):
        raise Reject("commitment.final_entry_digest is not 64 lowercase hex")
    want = entry_digest(timeline[-1])
    if fed != want:
        raise Reject("commitment.final_entry_digest does not match the last entry digest")
    cnt = commitment.get("entry_count")
    if isinstance(cnt, bool) or not isinstance(cnt, int):
        raise Reject("commitment.entry_count is not an integer")
    if cnt != len(timeline):
        raise Reject("commitment.entry_count does not equal the timeline length")
    pub = commitment.get("published_at")
    try:
        _check_created_at(pub if isinstance(pub, str) else "")
    except Reject:
        raise Reject("commitment.published_at is not a calendar-valid RFC 3339")
    return True


# ---- Merkle root over workflow receipt ids ---------------------------------
def merkle_root(receipt_ids):
    """Root over leaf hashes of the (seq-ordered) receipt ids: leaf =
    sha256(id); parent = sha256(left||right); odd node duplicated; empty
    tree root = sha256(b'')."""
    lvl = [hashlib.sha256(rid.encode("utf-8")).digest() for rid in receipt_ids]
    if not lvl:
        return hashlib.sha256(b"").hexdigest()
    while len(lvl) > 1:
        nxt = []
        for i in range(0, len(lvl), 2):
            a = lvl[i]
            b = lvl[i + 1] if i + 1 < len(lvl) else a
            nxt.append(hashlib.sha256(a + b).digest())
        lvl = nxt
    return lvl[0].hex()


def merkle_root_leaves(leaves):
    """Legacy-construction Merkle root: leaves are {seq, preimage}; leaf =
    sha256(preimage), sorted by seq; odd node duplicated; empty = sha256(b'')."""
    lvl = [hashlib.sha256(l["preimage"].encode("utf-8")).digest()
           for l in sorted(leaves, key=lambda x: x["seq"])]
    if not lvl:
        return hashlib.sha256(b"").hexdigest()
    while len(lvl) > 1:
        if len(lvl) % 2:
            lvl.append(lvl[-1])
        lvl = [hashlib.sha256(lvl[i] + lvl[i + 1]).digest()
               for i in range(0, len(lvl), 2)]
    return lvl[0].hex()
