# WC-2026-005 — Expected results table (local validation kit)

These are the *expected* outcomes for each case in the kit, derived from the
runtime-verified decision functions (see `../evidence/WC-2026-005/`) and the
statically traced browser wiring. They are predictions for the authorized
tester to confirm or refute — **not** observed results.

**2026-08-20 fix:** attacker and victim now use SEPARATE loopback site
identities (attacker http://127.0.0.1:8000, victim http://127.0.0.2:8765).
The previous single-port design made Control 2 same-site and confounded the
candidate case. Run two server instances: `server.py --role attacker --port 8000`
and `server.py --role victim --port 8765 --host 127.0.0.2`.

| Case | Fixture | firstPartyForCookies of the request | Registrable domain | Decision (verified fn) | Expected Cookie header on /victim request |
|---|---|---|---|---|---|
| **Candidate** | Opaque-origin iframe (`sandbox="allow-scripts allow-popups"`, no `allow-same-origin`) on attacker page (http://127.0.0.1:8000) → `blob:null/<uuid>` popup → fetch http://127.0.0.2:8765/victim | `blob:null/<uuid>` (popup's own URL; no opener inheritance) | empty (`nullOrigin`) | `None` (NOT blocked) | **present** (candidate behavior) |
| Control 1 | Same iframe WITH `allow-same-origin` → `blob:http://127.0.0.1:8000/<uuid>` popup → fetch http://127.0.0.2:8765/victim | `blob:http://127.0.0.1:8000/<uuid>` | `127.0.0.1` (non-empty) | `All` (blocked; cross-site to 127.0.0.2) | **absent** (negative control) |
| Control 2 | Top page (http://127.0.0.1:8000) → fetch http://127.0.0.2:8765/victim with credentials | `http://127.0.0.1:8000/` | `127.0.0.1` | `All` (blocked; cross-site to 127.0.0.2) | **absent** (negative control) |
| Control 3 | Victim origin page → fetch http://127.0.0.2:8765/victim (same origin) | `http://127.0.0.2:8765/` | `127.0.0.2` | `None` (same-site) | **present** (mechanism sanity check) |

## Notes

- The candidate case requires a **user gesture** (click inside the iframe)
  because popup blockers suppress `window.open()` otherwise. This is a
  one-click prerequisite, not zero-click.
- The decision-function values in the "Decision" column are
  **runtime-verified** (harness, exit 0). The "Expected Cookie header"
  column is a **prediction** for the browser-level test and is UNVERIFIED
  until an authorized tester runs the kit.
- If the candidate case shows `test_cookie_present=no` while Controls 1-3
  behave as expected, the browser wiring does not propagate
  firstPartyForCookies as traced, and the candidate would need re-analysis.
- If Control 1 unexpectedly shows `test_cookie_present=yes`, the
  non-opaque-blob negative control failed and the harness's
  `BlobURL::getOriginURL` shim (or the traced `RegistrableDomain` blob
  special case) would need re-audit.
