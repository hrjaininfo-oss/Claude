// GST computation helpers. All amounts in rupees, rounded to 2 decimals.
const round2 = (n) => Math.round((n + Number.EPSILON) * 100) / 100;

/**
 * Compute GST on a taxable value.
 * @param {number} taxableValue
 * @param {number} rate   GST rate in percent (e.g. 18)
 * @param {boolean} interState  true => IGST; false => CGST + SGST/UTGST
 */
export function computeGst(taxableValue, rate, interState = false) {
  if (taxableValue < 0 || rate < 0) throw new RangeError('Values must be non-negative');
  const tax = round2((taxableValue * rate) / 100);
  if (interState) {
    return { taxableValue: round2(taxableValue), igst: tax, cgst: 0, sgst: 0, totalTax: tax, invoiceValue: round2(taxableValue + tax) };
  }
  const cgst = round2(tax / 2);
  const sgst = round2(tax - cgst);
  return { taxableValue: round2(taxableValue), igst: 0, cgst, sgst, totalTax: tax, invoiceValue: round2(taxableValue + tax) };
}

/** Back-calculate taxable value and GST from a tax-inclusive amount. */
export function reverseGst(inclusiveAmount, rate, interState = false) {
  const taxable = round2((inclusiveAmount * 100) / (100 + rate));
  const res = computeGst(taxable, rate, interState);
  // Absorb rounding so components add back to the inclusive amount exactly.
  const diff = round2(inclusiveAmount - res.invoiceValue);
  return { ...res, taxableValue: round2(res.taxableValue + diff), invoiceValue: round2(inclusiveAmount) };
}
