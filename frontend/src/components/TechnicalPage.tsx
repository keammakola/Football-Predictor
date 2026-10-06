import React, { useEffect, useState, useMemo } from 'react';
import { ProofOfWork } from './ProofOfWork';

interface Provenance {
  exported_at_utc: string; verified_records: number; first_match: string; last_match: string;
  results_source: string; odds_source: string;
  xg_sources?: { league: string; matches: number; fetched_at_utc: string; urls: string[] }[];
  xg_coverage?: { league: string; results_matches: number; matched_xg: number }[];
  sources: { league: string; season: string; file: string; url: string; sha256: string }[];
}

interface Bet {
  id: string;
  date?: string;
  season: string;
  league: string;
  match: string;
  pick: string;
  prob: number;
  odds_taken: number;
  won: number;
  pnl: number;
  result?: string;
}

const SEASON_LABELS: Record<string, string> = {
  '2122': '21/22', '2223': '22/23', '2324': '23/24',
  '2425': '24/25', '2526': '25/26', '2627': '26/27',
};

const LEAGUE_LABELS: Record<string, string> = {
  EPL: 'Premier League', LaLiga: 'La Liga',
  SerieA: 'Serie A', Bundesliga: 'Bundesliga', Ligue1: 'Ligue 1',
};

function pct(n: number) { return (n * 100).toFixed(1) + '%'; }

// Simple CSS bar chart bar
function Bar({ value, max, positive }: { value: number; max: number; positive: boolean }) {
  const width = max === 0 ? 0 : Math.abs(value) / Math.abs(max) * 100;
  return (
    <div className="w-full bg-bg border border-line h-5 relative overflow-hidden">
      <div
        className={`h-full transition-all ${positive ? 'bg-accent' : 'bg-cost'}`}
        style={{ width: `${width}%` }}
      />
    </div>
  );
}

export const TechnicalPage: React.FC = () => {
  const [bets, setBets] = useState<Bet[]>([]);
  const [loading, setLoading] = useState(true);

  const [provenance, setProvenance] = useState<Provenance | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    const read = async (url: string) => {
      const response = await fetch(url, { signal: controller.signal });
      if (!response.ok) throw new Error('Data unavailable');
      return response.json();
    };
    Promise.all([read('/data/bets.json'), read('/data/provenance.json')]).then(([records, source]) => {
      if (!Array.isArray(records) || !records.length || source.verified_records !== records.length || !Array.isArray(source.sources)) throw new Error('Invalid source export');
      setBets(records);
      setProvenance(source);
      setLoading(false);
    }).catch(() => { if (!controller.signal.aborted) { setError(true); setLoading(false); } });
    return () => controller.abort();
  }, []);

  // --- Confidence Tier Analysis ---
  const confidenceTiers = useMemo(() => {
    const tiers = [
      { label: '60–65%', min: 0.60, max: 0.65 },
      { label: '65–70%', min: 0.65, max: 0.70 },
      { label: '70–75%', min: 0.70, max: 0.75 },
      { label: '75%+',   min: 0.75, max: 1.00 },
    ];
    return tiers.map(t => {
      const subset = bets.filter(b => b.prob >= t.min && b.prob < t.max);
      const wins = subset.filter(b => b.won === 1).length;
      const total = subset.length;
      const winRate = total > 0 ? wins / total : 0;
      const pnl = subset.reduce((a, b) => a + b.pnl, 0);
      return { ...t, total, wins, winRate, pnl };
    });
  }, [bets]);

  // --- League Breakdown ---
  const leagueStats = useMemo(() => {
    const map: Record<string, { wins: number; total: number; pnl: number }> = {};
    bets.forEach(b => {
      if (!map[b.league]) map[b.league] = { wins: 0, total: 0, pnl: 0 };
      map[b.league].total++;
      map[b.league].wins += b.won;
      map[b.league].pnl += b.pnl;
    });
    return Object.entries(map)
      .map(([league, d]) => ({ league, ...d, winRate: d.wins / d.total }))
      .sort((a, b) => b.winRate - a.winRate);
  }, [bets]);

  // --- Season Breakdown & Cumulative P&L ---
  const seasonStats = useMemo(() => {
    const map: Record<string, { wins: number; total: number; pnl: number }> = {};
    bets.forEach(b => {
      if (!map[b.season]) map[b.season] = { wins: 0, total: 0, pnl: 0 };
      map[b.season].total++;
      map[b.season].wins += b.won;
      map[b.season].pnl += b.pnl;
    });
    return Object.entries(map)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([season, d]) => ({ season, ...d, winRate: d.wins / d.total }));
  }, [bets]);

  // Cumulative P&L points (sorted by date/id)
  const cumulativePnl = useMemo(() => {
    const sorted = [...bets].sort((a, b) => {
      const da = a.date || a.season;
      const db = b.date || b.season;
      return da.localeCompare(db);
    });
    let running = 0;
    const points: number[] = [];
    for (const bet of sorted) {
      running += bet.pnl;
      points.push(running);
    }
    return points;
  }, [bets]);

  const maxAbsPnl = useMemo(() => Math.max(...seasonStats.map(s => Math.abs(s.pnl))), [seasonStats]);
  const maxWinRate = useMemo(() => Math.max(...confidenceTiers.map(t => t.winRate)), [confidenceTiers]);

  // Simple SVG cumulative P&L sparkline
  const sparkline = useMemo(() => {
    if (cumulativePnl.length === 0) return null;
    const W = 800, H = 120;
    const minV = Math.min(...cumulativePnl, 0);
    const maxV = Math.max(...cumulativePnl, 0);
    const range = maxV - minV || 1;
    const pts = cumulativePnl.map((v, i) => {
      const x = (i / Math.max(1, cumulativePnl.length - 1)) * W;
      const y = H - ((v - minV) / range) * H;
      return `${x},${y}`;
    }).join(' ');
    const zeroY = H - ((0 - minV) / range) * H;
    return { pts, zeroY, W, H, minV, maxV };
  }, [cumulativePnl]);

  if (loading) {
    return <div className="animate-pulse text-muted font-mono uppercase">Loading evidence...</div>;
  }

  if (error || !provenance) return <div role="alert" className="border-2 border-cost bg-surface p-6"><h2 className="text-xl font-bold mb-2">Evidence data unavailable</h2><p>The historical ledger or its source record could not be loaded. Refresh to try again. No example data is shown.</p></div>;

  const totalBets = bets.length;
  const totalWins = bets.filter(b => b.won === 1).length;
  const totalPnl = bets.reduce((a, b) => a + b.pnl, 0);

  return (
    <div className="w-full space-y-20">

      {/* ── HEADER ── */}
      <div className="border-b-2 border-ink pb-8">
        <div className="font-mono text-xs text-muted uppercase tracking-widest mb-3">Evidence Room // Technical Analysis</div>
        <h2 className="text-3xl font-bold font-sans uppercase tracking-tight mb-4">
          The predictions. The results. The evidence.
        </h2>
        <p className="text-lg font-sans text-ink/80 max-w-3xl leading-relaxed">
          Explore model-confidence groups, results by league, season P&L, and cumulative returns from the historical bet ledger. Results and odds are checked against source CSVs; probabilities are model outputs and returns are simulated.
        </p>
      </div>

      <section className="bg-surface border-2 border-ink p-6 md:p-8" aria-labelledby="data-source-title">
        <h3 id="data-source-title" className="text-xl font-bold mb-3">Where this evidence comes from</h3>
        <p className="text-sm leading-relaxed mb-3">{provenance.verified_records.toLocaleString()} ledger records checked against {provenance.sources.length} cached source CSVs from football-data.co.uk. Every displayed result, score, bet odd, and P&L is matched to its historical source record during export.</p>
        <p className="text-sm text-muted leading-relaxed">Match dates: {provenance.first_match} to {provenance.last_match}. Odds: {provenance.odds_source}. Export verified: {new Date(provenance.exported_at_utc).toLocaleString()}.</p>
        <p className="text-sm text-muted leading-relaxed mt-3">This page loads verified historical exports, not a live odds feed. Model inputs use observed Understat xG from completed matches. Form features use only earlier observations; missing history stays missing.</p>
        {provenance.xg_sources && provenance.xg_sources.length > 0 && <div className="mt-5 border-t border-dashed border-line pt-4"><h4 className="font-bold text-sm mb-3">Observed xG sources</h4><ul className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">{provenance.xg_sources.map(source => <li key={source.league} className="text-sm"><a href={source.urls[source.urls.length - 1].replace('/getLeagueData/', '/league/')} target="_blank" rel="noreferrer" className="text-accent underline underline-offset-4">{LEAGUE_LABELS[source.league] || source.league}: Understat</a><p className="text-xs text-muted mt-1">{source.matches.toLocaleString()} observed match records</p></li>)}</ul>{provenance.xg_coverage && <p className="text-xs text-muted mt-4">Across the input history, {provenance.xg_coverage.reduce((sum, source) => sum + source.matched_xg, 0).toLocaleString()} of {provenance.xg_coverage.reduce((sum, source) => sum + source.results_matches, 0).toLocaleString()} results match an xG record. Unmatched observations are excluded from form history.</p>}</div>}
        <details className="mt-5"><summary className="cursor-pointer font-bold text-sm focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent">Inspect the original data sources</summary><ul className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3 mt-4">{provenance.sources.map(source => <li key={source.file}><a href={source.url} target="_blank" rel="noreferrer" className="text-sm text-accent underline underline-offset-4">{source.file}</a></li>)}</ul><a href="/data/provenance.json" download className="inline-block text-sm text-accent underline mt-5">Download source metadata and file hashes</a></details>
      </section>

      {/* ── SECTION 1: MODEL PROOF ── */}
      <div>
        <div className="font-mono text-xs text-accent uppercase tracking-widest mb-2">Section 01</div>
        <h3 className="text-2xl font-bold font-sans uppercase tracking-tight mb-2">Model Proof</h3>
        <p className="font-sans text-ink/70 mb-10 max-w-2xl">
          Compare the observed win rates across model-confidence groups. These are selected bets, not a calibration test of all predictions; each group’s sample size matters.
        </p>

        {/* Confidence Tiers */}
        <div className="mb-12">
          <div className="font-mono text-xs text-muted uppercase tracking-wider mb-4 border-b border-dashed border-line pb-2">
            Win Rate by Model Confidence Tier
          </div>
          <div className="space-y-4">
            {confidenceTiers.map(tier => (
              <div key={tier.label} className="grid grid-cols-12 gap-4 items-center">
                <div className="col-span-2 font-mono text-sm font-bold">{tier.label}</div>
                <div className="col-span-6">
                  <Bar value={tier.winRate} max={maxWinRate} positive={true} />
                </div>
                <div className="col-span-2 font-mono text-sm font-bold text-accent">{pct(tier.winRate)}</div>
                <div className="col-span-2 font-mono text-xs text-muted">{tier.total} bets</div>
              </div>
            ))}
          </div>
          <div className="mt-4 font-mono text-xs text-muted bg-bg border border-dashed border-line px-4 py-3 max-w-xl">
            Observed win rates: {pct(confidenceTiers[0].winRate)} at 60–65% confidence and {pct(confidenceTiers[confidenceTiers.length - 1].winRate)} at 75%+. These group win rates alone do not establish calibration.
          </div>
        </div>

        {/* League Breakdown */}
        <div>
          <div className="font-mono text-xs text-muted uppercase tracking-wider mb-4 border-b border-dashed border-line pb-2">
            Performance by League — {totalBets} total bets across {leagueStats.length} leagues
          </div>
          <div role="region" aria-label="League performance table" tabIndex={0} className="overflow-x-auto bg-surface border-2 border-ink shadow-[6px_6px_0px_0px_rgba(17,24,39,1)]">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-ink text-surface font-mono text-xs uppercase tracking-wider">
                  <th scope="col" className="py-3 px-4 font-normal">League</th>
                  <th scope="col" className="py-3 px-4 font-normal text-right">Bets</th>
                  <th scope="col" className="py-3 px-4 font-normal text-right">Wins</th>
                  <th scope="col" className="py-3 px-4 font-normal text-right">Win Rate</th>
                  <th scope="col" className="py-3 px-4 font-normal text-right">Net P&L</th>
                  <th scope="col" className="py-3 px-4 font-normal w-40">Win Rate Bar</th>
                </tr>
              </thead>
              <tbody className="font-mono text-sm divide-y divide-dashed divide-line">
                {leagueStats.map(l => (
                  <tr key={l.league} className="hover:bg-bg transition-colors">
                    <td className="py-3 px-4 font-sans font-bold">{LEAGUE_LABELS[l.league] ?? l.league}</td>
                    <td className="py-3 px-4 text-right text-muted">{l.total}</td>
                    <td className="py-3 px-4 text-right">{l.wins}</td>
                    <td className="py-3 px-4 text-right font-bold">{pct(l.winRate)}</td>
                    <td className={`py-3 px-4 text-right font-bold ${l.pnl >= 0 ? 'text-accent' : 'text-cost'}`}>
                      {l.pnl >= 0 ? '+' : ''}{l.pnl.toFixed(2)}
                    </td>
                    <td className="py-3 px-4">
                      <Bar value={l.winRate} max={1} positive={l.winRate > 0.5} />
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* ── SECTION 2: WHERE THE EDGE DIES ── */}
      <div>
        <div className="font-mono text-xs text-cost uppercase tracking-widest mb-2">Section 02</div>
        <h3 className="text-2xl font-bold font-sans uppercase tracking-tight mb-2">Where the Edge Dies</h3>
        <p className="font-sans text-ink/70 mb-10 max-w-2xl">
          Below is the season-by-season result and cumulative P&L for a simulated one-unit stake on each selected bet — {totalBets} bets, {totalWins} wins, net result: <span className={`font-bold ${totalPnl >= 0 ? 'text-accent' : 'text-cost'}`}>{totalPnl >= 0 ? '+' : ''}{totalPnl.toFixed(2)} units</span>.
        </p>

        {/* Season Table */}
        <div className="mb-12">
          <div className="font-mono text-xs text-muted uppercase tracking-wider mb-4 border-b border-dashed border-line pb-2">
            Season-by-Season P&L
          </div>
          <div role="region" aria-label="Season returns table" tabIndex={0} className="overflow-x-auto bg-surface border-2 border-ink shadow-[6px_6px_0px_0px_rgba(17,24,39,1)]">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-ink text-surface font-mono text-xs uppercase tracking-wider">
                  <th scope="col" className="py-3 px-4 font-normal">Season</th>
                  <th scope="col" className="py-3 px-4 font-normal text-right">Bets</th>
                  <th scope="col" className="py-3 px-4 font-normal text-right">Win Rate</th>
                  <th scope="col" className="py-3 px-4 font-normal text-right">Net P&L (Units)</th>
                  <th scope="col" className="py-3 px-4 font-normal w-48">P&L Bar</th>
                </tr>
              </thead>
              <tbody className="font-mono text-sm divide-y divide-dashed divide-line">
                {seasonStats.map(s => (
                  <tr key={s.season} className="hover:bg-bg transition-colors">
                    <td className="py-3 px-4 font-bold">{SEASON_LABELS[s.season] ?? s.season}</td>
                    <td className="py-3 px-4 text-right text-muted">{s.total}</td>
                    <td className="py-3 px-4 text-right">{pct(s.winRate)}</td>
                    <td className={`py-3 px-4 text-right font-bold ${s.pnl >= 0 ? 'text-accent' : 'text-cost'}`}>
                      {s.pnl >= 0 ? '+' : ''}{s.pnl.toFixed(2)}
                    </td>
                    <td className="py-3 px-4">
                      <Bar value={s.pnl} max={maxAbsPnl} positive={s.pnl >= 0} />
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="bg-bg border-t-2 border-ink font-mono text-sm font-bold">
                  <td className="py-3 px-4">TOTAL</td>
                  <td className="py-3 px-4 text-right">{totalBets}</td>
                  <td className="py-3 px-4 text-right">{pct(totalWins / totalBets)}</td>
                  <td className={`py-3 px-4 text-right ${totalPnl >= 0 ? 'text-accent' : 'text-cost'}`}>
                    {totalPnl >= 0 ? '+' : ''}{totalPnl.toFixed(2)}
                  </td>
                  <td />
                </tr>
              </tfoot>
            </table>
          </div>
        </div>

        {/* Cumulative P&L Sparkline */}
        {sparkline && (
          <div>
            <div className="font-mono text-xs text-muted uppercase tracking-wider mb-4 border-b border-dashed border-line pb-2">
              Cumulative P&L — All {totalBets} Bets (Chronological)
            </div>
            <div className="bg-surface border-2 border-ink shadow-[6px_6px_0px_0px_rgba(17,24,39,1)] p-6">
              <div className="flex justify-between font-mono text-xs text-muted mb-2">
                <span>Bet #1</span>
                <span>Bet #{totalBets}</span>
              </div>
              <svg
                viewBox={`0 0 ${sparkline.W} ${sparkline.H}`}
                className="w-full"
                preserveAspectRatio="none"
                style={{ height: '120px' }}
              >
                {/* Zero line */}
                <line
                  x1={0} y1={sparkline.zeroY}
                  x2={sparkline.W} y2={sparkline.zeroY}
                  stroke="currentColor" strokeDasharray="4 4" strokeWidth="1"
                  className="text-line"
                />
                {/* P&L line */}
                <polyline
                  points={sparkline.pts}
                  fill="none"
                  stroke={totalPnl >= 0 ? '#16a34a' : '#dc2626'}
                  strokeWidth="2"
                />
              </svg>
              <div className="flex justify-between font-mono text-xs mt-2">
                <span className="text-muted">Peak: <span className="font-bold">{sparkline.maxV.toFixed(2)}</span></span>
                <span className={`font-bold ${totalPnl >= 0 ? 'text-accent' : 'text-cost'}`}>
                  Final: {totalPnl >= 0 ? '+' : ''}{totalPnl.toFixed(2)} units
                </span>
                <span className="text-muted">Trough: <span className="font-bold">{sparkline.minV.toFixed(2)}</span></span>
              </div>
              <p className="font-mono text-xs text-muted mt-4 border-t border-dashed border-line pt-3">
                The line shows running P&L across all placed bets in chronological order. It reflects the selected predictions and recorded odds; this curve alone cannot isolate the effect of bookmaker margin.
              </p>
            </div>
          </div>
        )}
      </div>

      <ProofOfWork />

    </div>
  );
};
