# WC-2026-005 — Local validation kit (manual, authorized test environment only)

This kit lets an authorized tester check the candidate chain in a real
WebKit/Safari environment. It is **local-only**: everything binds to
`127.0.0.1`, uses a uniquely named throwaway cookie, and touches no real
domains, accounts, or third-party services.

> **IMPORTANT — what this kit does and does not prove**
> This kit is a *test fixture*, not a proof. It cannot be run in this
> research environment (no Safari/WebKit browser, no full WebKit build with
> ITP test infrastructure). It exists so that an authorized tester with a
> current Apple product or WebKit test environment can collect the missing
> end-to-end evidence. The harness in `../evidence/WC-2026-005/` already
> proves the decision-function logic; this kit targets the browser wiring.

## Prerequisites

- Python 3 (any recent version) on the test machine
- An authorized test environment with a current Safari (macOS/iOS) or a
  WebKit build with ITP enabled (e.g. `run-webkit-tests` infrastructure)
- The test machine must be able to run a local HTTP server on 127.0.0.1

## Steps

1. **Start the local server** (terminal 1):

   ```sh
   cd validation-kit
   python3 server.py --port 8765
   ```

   The server prints the test cookie name and the log file path
   (`validation-kit/results.log`). It binds only to 127.0.0.1.

2. **Load the attacker fixture** in the browser:

   ```
   http://127.0.0.1:8765/
   ```

   The page embeds an opaque-origin sandboxed iframe
   (`sandbox="allow-scripts allow-popups"`, no `allow-same-origin`).

3. **Run the candidate case**: click the button inside the iframe
   ("Click to open blob: popup"). This is the required **user gesture** —
   popup blockers suppress `window.open()` without one. The iframe creates a
   `blob:null/<uuid>` payload and opens it as a popup. The popup fetches
   `http://127.0.0.1:8765/victim` with `credentials:'include'`.

4. **Run the negative controls** (one at a time, per the on-page
   instructions):
   - **Control 1 — non-opaque blob:** edit `attacker.html` to add
     `allow-same-origin` to the iframe sandbox (so the blob URL is
     `blob:http://127.0.0.1:8765/<uuid>`). Expected: the popup's cross-site
     fetch is blocked from carrying cookies.
   - **Control 2 — ordinary third-party:** from the top page, fetch
     `http://127.0.0.1:8765/victim` with `credentials:'include'`. Expected:
     blocked from carrying cookies.
   - **Control 3 — first-party:** from the top page, fetch
     `http://127.0.0.1:8765/` (same origin). Expected: cookie IS sent.

5. **Collect results**:

   ```sh
   ./collect-results.sh results.log
   ```

   The script summarizes only the log you supply; it contacts nothing.

## Reading the results

The server logs one line per `/victim` request:

```
VICTIM_REQ path=/victim cookie_header_present=yes|no test_cookie_present=yes|no origin=...
```

- `test_cookie_present=yes` on the **candidate case** (opaque blob popup)
  means the Cookie header was attached to a cross-site request from a
  `blob:null/<uuid>` document — the candidate behavior.
- `test_cookie_present=no` on **Control 1** (non-opaque blob) and
  **Control 2** (ordinary third-party) confirms the negative controls.
- `test_cookie_present=yes` on **Control 3** (first-party) confirms the
  cookie mechanism itself works.

## Safety constraints (enforced by design)

- Server binds only to `127.0.0.1`; no remote access.
- Cookie name is random per server start; no real cookies are used.
- No state-changing requests outside localhost; `/victim` only sets a
  throwaway cookie and logs headers.
- Cross-origin response bodies are NOT read by the fixture; the popup only
  reports success/failure via `postMessage` to its opener. The optional
  `/cors-test` endpoint reflects the Origin explicitly and is only used if
  the tester opts in.
- `collect-results.sh` parses only the user-supplied log file.
