**Title**: Basket badge remains at 2 after removing an item from the basket

**Summary**: After removing one of two items, the basket screen shows one item, but the home-screen badge still shows 2. The test failed in 2 of 3 retries; the badge corrects itself after an app restart.

**Severity**: Medium — The badge displays an incorrect basket count after an item is removed.

**Steps to Reproduce**:
1. On staging with app version 5.2.0 (beta), log in as `test.buyer03@example.com`.
2. Add SKU-20011 and SKU-20345 to the basket.
3. Confirm the basket badge shows 2.
4. Open the basket and remove SKU-20011.
5. Confirm the basket screen lists 1 item.
6. Navigate back to the home screen.

**Expected Result**: The basket badge shows 1.

**Actual Result**: The basket badge shows 2. It corrects itself after an app restart.

**Likely Component**: Basket badge update after item removal.