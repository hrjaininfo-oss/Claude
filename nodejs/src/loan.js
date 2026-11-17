// Term-loan EMI and repayment schedule (reducing balance, monthly rests).
const round2 = (n) => Math.round((n + Number.EPSILON) * 100) / 100;

/** EMI = P·r·(1+r)^n / ((1+r)^n − 1), r = monthly rate */
export function emi(principal, annualRatePct, months) {
  if (principal <= 0 || months <= 0) throw new RangeError('Principal and tenure must be positive');
  const r = annualRatePct / 12 / 100;
  if (r === 0) return round2(principal / months);
  const f = (1 + r) ** months;
  return round2((principal * r * f) / (f - 1));
}

/** Month-wise schedule; the final instalment is adjusted to close the loan exactly. */
export function schedule(principal, annualRatePct, months) {
  const r = annualRatePct / 12 / 100;
  const inst = emi(principal, annualRatePct, months);
  let balance = principal;
  const rows = [];
  for (let m = 1; m <= months; m++) {
    const interest = round2(balance * r);
    let principalPart = round2(inst - interest);
    if (m === months) principalPart = round2(balance);
    const payment = round2(principalPart + interest);
    balance = round2(balance - principalPart);
    rows.push({ month: m, opening: round2(balance + principalPart), payment, interest, principal: principalPart, closing: balance });
  }
  return rows;
}

/** Year-wise summary (12-month blocks) — handy for DSCR workings in a DPR. */
export function yearlySummary(rows) {
  const years = [];
  for (let i = 0; i < rows.length; i += 12) {
    const block = rows.slice(i, i + 12);
    years.push({
      year: i / 12 + 1,
      opening: block[0].opening,
      interest: round2(block.reduce((s, x) => s + x.interest, 0)),
      principal: round2(block.reduce((s, x) => s + x.principal, 0)),
      closing: block[block.length - 1].closing,
    });
  }
  return years;
}
