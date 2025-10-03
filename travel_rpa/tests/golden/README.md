# Golden Test Cases

This directory contains the golden test cases for the Travel RPA pilot automation.

## Structure

Each test case is stored in its own directory with the following files:

- `email.json`: Input email data (message_id, from, subject, body, received_at, ocr_results)
- `expected.json`: Expected output (route, extracted data, pricing breakdown)
- `passport_*.jpg` (optional): Passport images used in the test case

## Test Cases

### Completed Examples
- `case_06_outbound_silver_10days/`: Single traveller, Silver plan, Worldwide, 10 days
- `case_07_outbound_gold_14days/`: Two travellers, Gold plan, WW_EXCL_US_CA, 14 days

### TODO: Populate Remaining Cases
The following cases need to be created from the sample emails (cases 6-25):

- case_08: Platinum plan with senior traveller (age load test)
- case_09: Silver plan with sports coverage (sports load test)
- case_10: Gold plan with 15 travellers (group discount 5% test)
- case_11: Silver plan with 25 travellers (group discount 15% test)
- case_12: Gold plan with 35 travellers (group discount 25% test)
- case_13: Platinum plan with 45 travellers (group discount 35% test)
- case_14: Silver plan, 7 days (band 1-7 boundary)
- case_15: Gold plan, 15 days (band 8-15 boundary)
- case_16: Platinum plan, 31 days (band 16-31 boundary)
- case_17: Silver plan, 45 days (band 32-45 boundary)
- case_18: Gold plan, 92 days (band 46-92 max days)
- case_19: Missing scope (should route to "missing")
- case_20: Missing dates (should route to "missing")
- case_21: Missing passport data (should route to "missing")
- case_22: Non-travel intent email (should route to "ignore")
- case_23: Senior + sports combined
- case_24: Multiple seniors in group
- case_25: Edge case - day band boundary testing

## Running Tests

```bash
# Run all golden tests
pytest travel_rpa/tests/test_golden_set.py -v

# Run specific test case
pytest travel_rpa/tests/test_golden_set.py::test_golden_case[case_06_outbound_silver_10days] -v
```

## Adding New Cases

1. Create directory: `mkdir -p travel_rpa/tests/golden/case_XX_description/`
2. Create `email.json` with input data
3. Create `expected.json` with expected output
4. Run the test to verify it passes
