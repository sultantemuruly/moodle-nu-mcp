# NU Moodle Authentication

How authentication works on `https://moodle.nu.edu.kz`, and what it means for this MCP project.

## TL;DR

NU Moodle does **not** use local username/password auth. It delegates login to
**Microsoft Entra ID (Azure AD / Office 365)** via Moodle's OAuth 2 auth plugin
(`auth_oauth2`). The password never reaches Moodle, so the usual
`POST /login/token.php` (username + password → `wstoken`) flow **cannot work**.
Authenticated access must reuse a **real logged-in browser session**, which is
exactly what `auth.py` does (Playwright → manual Microsoft login → saved
`storage_state`).

## Evidence (inspected live on the login page)

From `tool_mobile_get_public_config`:

| Field | Value | Meaning |
|-------|-------|---------|
| `typeoflogin` | `1` | Login via browser / external IdP (not in-app password). `2` would mean local password login. |
| `authloginviaemail` | `0` | No local email/password login. |
| `registerauth` | `""` | No self-registration. |
| `enablewebservices` | `1` | Web services API is enabled. |
| `enablemobilewebservice` | `1` | Mobile web service is enabled. |
| `launchurl` | `https://moodle.nu.edu.kz/admin/tool/mobile/launch.php` | SSO token-launch endpoint (see below). |

Login-page links point to Microsoft, confirming the IdP:

- Password reset → `https://passwordreset.microsoftonline.com/`
- Account security → `https://mysignins.microsoft.com/security-info`
- Page instructs users to use the same credentials as the NU portal / registrar.

A username/password form is still rendered at `/login/index.php`, but it is not
the real authentication path — the identity check happens at Microsoft.

## The actual login flow

1. User opens `/login/index.php` and starts login.
2. Moodle (`auth_oauth2`) redirects to `login.microsoftonline.com`.
3. User authenticates at Microsoft (password, MFA, etc.). **Moodle never sees the password.**
4. Microsoft redirects back to Moodle's OAuth callback (`/auth/oauth2/...`).
5. Moodle matches/creates the local user and calls `complete_user_login()`,
   establishing a session.
6. The browser now holds a valid **`MoodleSession` cookie**. Subsequent requests
   are authorized by that cookie.

Because step 3 is external, Moodle's internal `user_login()` is never invoked and
`/login/token.php` has no password to verify.

## What this means for the MCP server

### Why the password → token approach fails
`/login/token.php` only issues a `wstoken` for **internal** auth types (manual,
email) where Moodle stores the password. With OAuth2-only auth, there is no
password in Moodle to validate, so that request cannot return a token.

### Approaches that work

**A. Session-cookie reuse (current approach in `auth.py`) — recommended**
- Drive a real browser (Playwright), let the user complete the Microsoft login
  once, then persist `storage_state` (the `MoodleSession` cookie + related state).
- Reuse that saved state for later runs until the session expires; then
  re-authenticate the same way.
- All Moodle requests go through this authenticated browser context (page
  navigation, or `context.request` for AJAX/service calls) rather than the
  token API.
- Note: state-changing requests need Moodle's CSRF token (`sesskey`), which is
  available in page HTML / JS once logged in.

**B. Manual web-service token**
- After logging in via Microsoft, create a token under
  *Preferences → Security keys* (`/user/managetoken.php`), if the admin permits it.
- Use that static token directly as `wstoken` against
  `/webservice/rest/server.php`. This skips `login/token.php` entirely.

**C. Mobile SSO launch (matches `launchurl`)**
- Because `typeoflogin` is `1`, the supported programmatic token path is the
  mobile-app handshake: open
  `admin/tool/mobile/launch.php?service=moodle_mobile_app&passport=<random>`,
  complete the Microsoft login in a browser, and Moodle redirects to a
  `moodlemobile://token=<base64>` URL containing the token. Decode it and use it
  as `wstoken`.

Approach A is the least fragile here and is already what the project implements.

## Key facts to remember

- Auth type: `auth_oauth2` (Microsoft Entra ID).
- No local passwords → `login/token.php` username/password exchange is a dead end.
- Authorization for reused access = the `MoodleSession` cookie.
- CSRF for writes = `sesskey`.
- Web services are enabled, so a **manually created token** works if you need the
  REST API instead of the session.
