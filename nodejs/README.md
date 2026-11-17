# ca-calculators (Node.js)

A small, dependency-free Node.js (≥18) toolkit:

- **GST**: compute CGST/SGST or IGST on a taxable value, or back-calculate from a GST-inclusive amount.
- **Term loan**: EMI, month-wise repayment schedule and year-wise interest/principal summary (useful for DSCR workings in DPR/CMA).

```bash
cd nodejs
npm test                                   # run tests
node src/cli.js gst 10000 18               # CGST 900 + SGST 900
node src/cli.js gst 10000 18 inter         # IGST 1800
node src/cli.js rgst 11800 18              # taxable 10000
node src/cli.js loan 1000000 10 60         # EMI + yearly summary
```

Figures are rounded to 2 decimals per line item; verify against the actual invoice/sanction terms before use.
