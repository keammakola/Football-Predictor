export function calculateImplied(odds: number): number {
  if (odds > 1.01 && odds < 1000) {
    return 1 / odds;
  }
  return 0;
}

export function calculateOverround(impliedProbs: number[]): number {
  const sum = impliedProbs.reduce((acc, prob) => acc + prob, 0);
  return sum - 1;
}

export function calculateMarginFreeProportional(implied: number, overround: number): number {
  if (implied === 0) return 0;
  return implied / (1 + overround);
}

export function calculateFairOdds(marginFreeProb: number): number {
  if (marginFreeProb === 0) return 0;
  return 1 / marginFreeProb;
}
