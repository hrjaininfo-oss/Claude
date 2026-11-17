#!/usr/bin/env node
import { computeGst, reverseGst, emi, schedule, yearlySummary } from './index.js';

const [cmd, ...args] = process.argv.slice(2);
const n = (i) => Number(args[i]);

const usage = `Usage:
  node src/cli.js gst <taxable> <rate%> [inter]        GST on taxable value (add "inter" for IGST)
  node src/cli.js rgst <inclusive> <rate%> [inter]     Back-calculate from GST-inclusive amount
  node src/cli.js loan <principal> <rate%> <months>    EMI + year-wise repayment summary`;

switch (cmd) {
  case 'gst':
    console.table(computeGst(n(0), n(1), args[2] === 'inter'));
    break;
  case 'rgst':
    console.table(reverseGst(n(0), n(1), args[2] === 'inter'));
    break;
  case 'loan': {
    console.log(`EMI: ₹${emi(n(0), n(1), n(2)).toLocaleString('en-IN')}`);
    console.table(yearlySummary(schedule(n(0), n(1), n(2))));
    break;
  }
  default:
    console.log(usage);
    process.exit(cmd ? 1 : 0);
}
