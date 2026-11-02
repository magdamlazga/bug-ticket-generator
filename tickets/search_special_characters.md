**Title**: Search returns HTTP 500 for queries containing apostrophes and ampersands

**Summary**: In staging build 3.14.0-rc2, searching for `kids' t-shirt & shorts` returns an error page instead of results. The search service logs a query-parser syntax error near the apostrophe.

**Severity**: High — Special characters in a search query cause a server error and prevent results from being displayed.

**Steps to Reproduce**:
1. Open the homepage.
2. Enter `kids' t-shirt & shorts` in the search field.
3. Submit the search.

**Expected Result**: Search returns at least one result or otherwise handles the query without showing an error page.

**Actual Result**: The search request returns HTTP 500, the page shows “Something went wrong,” and the test gets an error page instead of results. The failure occurred on all 3 retries.

**Likely Component**: Search service query parser