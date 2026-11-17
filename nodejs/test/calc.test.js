import test from 'node:test';
import assert from 'node:assert/strict';
import { computeGst, reverseGst, emi, schedule } from '../src/index.js';

test('intra-state GST splits into CGST + SGST', () => {
  const r = computeGst(10000, 18);
  assert.equal(r.cgst, 900);
  assert.equal(r.sgst, 900);
  assert.equal(r.invoiceValue, 11800);
});

test('inter-state GST is IGST', () => {
  const r = computeGst(10000, 12, true);
  assert.equal(r.igst, 1200);
  assert.equal(r.cgst, 0);
});

test('reverse GST adds back to inclusive amount', () => {
  const r = reverseGst(11800, 18);
  assert.equal(r.taxableValue, 10000);
  assert.equal(r.invoiceValue, 11800);
  const odd = reverseGst(999, 5);
  assert.equal(Math.round((odd.taxableValue + odd.totalTax) * 100) / 100, 999);
});

test('EMI for ₹10,00,000 at 10% for 60 months', () => {
  assert.equal(emi(1000000, 10, 60), 21247.04);
});

test('schedule closes loan to zero', () => {
  const rows = schedule(1000000, 10, 60);
  assert.equal(rows.length, 60);
  assert.equal(rows.at(-1).closing, 0);
  const totalPrincipal = rows.reduce((s, x) => s + x.principal, 0);
  assert.equal(Math.round(totalPrincipal), 1000000);
});
