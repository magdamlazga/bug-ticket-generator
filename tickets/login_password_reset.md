**Title**: Password reset returns 200 but new password fails login while old password still works

**Summary**: In staging build 3.14.0-rc2, resetting the password succeeds with HTTP 200, but login using the new password returns 401. The old password still works.

**Severity**: High — Users cannot sign in with their newly reset password.

**Steps to Reproduce**
1. Request a password reset for `test.buyer02@example.com`.
2. Open the reset link from the email.
3. Submit a new password.
4. Submit a login using the new password.

**Expected Result**: Login with the new password succeeds and redirects to `/account`.

**Actual Result**: Login returns `401 Unauthorized` with `invalid_credentials`, and the user stays on `/login`; logging in with the old password still succeeds.

**Likely Component**: Password reset and authentication API (`/api/v2/auth/reset-password`, `/api/v2/auth/login`)