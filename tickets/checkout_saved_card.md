**Title**: Saved-card checkout remains PENDING after payment authorisation times out

**Summary**: In staging on build 3.14.0-rc2, `test_checkout_with_saved_card` failed on all 3 retries because the payment authorisation request timed out and the order remained PENDING. The same test passed on build 3.13.2.

**Severity**: High — Checkout does not reach the expected CONFIRMED order status.

**Steps to Reproduce**:
1. Log in as `test.buyer01@example.com`.
2. Add SKU-10482 to the basket with quantity 2.
3. Select the saved card ending in 4242.
4. Submit payment authorisation via `POST /api/v2/payments/authorise`.

**Expected Result**: Order status is CONFIRMED.

**Actual Result**: The authorisation request returned 504 Gateway Timeout after 30002 ms; the payment service reported an upstream timeout to `gateway.example.com`, and the order status was PENDING.

**Likely Component**: Payment service or its upstream payment gateway authorisation request.