import React, { useEffect, useState } from 'react';

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
  scoreline?: string;
  p_home?: number;
  p_draw?: number;
  p_away?: number;
}

interface Stats {
  strong_hit_rate: number;
}

export const MainPage: React.FC = () => {
  const [bets, setBets] = useState<Bet[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedBet, setExpandedBet] = useState<string | null>(null);
  const [visibleCount, setVisibleCount] = useState(50);

  useEffect(() => {
    Promise.all([
      fetch('/data/bets.json').then(r => r.json()),
      fetch('/data/stats.json').then(r => r.json())
    ]).then(([betsData, statsData]) => {
      setBets(betsData);
      setStats(statsData);
      setLoading(false);
    }).catch(err => {
      console.error(err);
      setLoading(false);
    });
  }, []);

  const totalBets = bets.length;
  const totalWins = bets.filter(b => b.won === 1).length;
  const totalPnl = bets.reduce((acc, b) => acc + b.pnl, 0);
  const roi = totalBets > 0 ? (totalPnl / totalBets) * 100 : 0;
  const seasonsCount = new Set(bets.map(b => b.season)).size;

  const formatPct = (val: number) => (val * 100).toFixed(1) + '%';
  const formatOdds = (val: number) => val.toFixed(2);



  if (loading) {
    return <div className="animate-pulse text-muted font-mono uppercase">Loading ledger...</div>;
  }

  return (
    <div className="w-full">
      {/* Article Brief */}
      <div className="mb-12 border-b-2 border-ink pb-8">
        <h2 className="text-3xl font-bold font-serif mb-4 leading-tight">
          The Math is Rigged: Why You Can Never Beat the House in Sports Betting
        </h2>
        <p className="text-xl font-sans text-ink/80 leading-relaxed max-w-4xl mb-6">
          I spent weeks building a prediction engine for the top five European football leagues. The crazy part is that the code actually worked. It accurately predicted the outcome of matches roughly {stats?.strong_hit_rate?.toFixed(1) ?? '—'}% of the time (dropping to {totalBets > 0 ? ((totalWins / totalBets) * 100).toFixed(1) : '—'}% when only taking bets where the odds were also in our favour). But when I simulated running actual bets through it over {seasonsCount || 3} seasons, the system still lost money. Here is the data that proves why.
        </p>
        <a 
          href="https://hashnode.com" 
          target="_blank" 
          rel="noreferrer"
          className="inline-block bg-ink text-surface font-mono text-sm font-bold uppercase px-6 py-3 hover:bg-accent transition-colors shadow-[4px_4px_0px_0px_rgba(220,38,38,1)]"
        >
          Read the Full Article on Hashnode
        </a>
      </div>

      <div className="mb-8 border-2 border-ink bg-bg p-6">
        <p className="font-mono text-xs font-bold uppercase tracking-wider mb-2">Historical experiment</p>
        <p className="text-ink/80 leading-relaxed">Explore recorded match results, bookmaker odds and model predictions from the backtest. Returns simulate one-unit stakes on completed matches.</p>
      </div>

      {/* Explanation */}
      <div className="mb-8">
        <p className="text-lg font-sans font-medium text-ink bg-bg border-l-4 border-accent p-6">
          <span className="font-bold text-accent">THE STRATEGY:</span> The historical bets shown below are strictly those where the model had a <strong className="text-ink">at least 60% confidence</strong> on a strong win, and it only placed the wager if the bookmaker's listed odds were strictly greater than the model's calculated fair odds (Odds &gt; Fair Odds).
        </p>
      </div>

      {/* KPI Bar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-16">
        <div className="bg-surface border-2 border-ink p-6 shadow-[4px_4px_0px_0px_rgba(17,24,39,1)]">
          <div className="font-mono text-sm text-muted uppercase tracking-wider mb-2">Simulated Bets</div>
          <div className="font-mono text-4xl font-bold">{totalBets}</div>
        </div>
        <div className="bg-surface border-2 border-ink p-6 shadow-[4px_4px_0px_0px_rgba(17,24,39,1)]">
          <div className="font-mono text-sm text-muted uppercase tracking-wider mb-2">Total Wins</div>
          <div className="font-mono text-4xl font-bold">{totalWins} <span className="text-base text-muted font-normal ml-2">({((totalWins/totalBets)*100).toFixed(1)}% Hit Rate)</span></div>
        </div>
        <div className="bg-surface border-2 border-cost p-6 shadow-[4px_4px_0px_0px_rgba(220,38,38,1)]">
          <div className="font-mono text-sm text-cost uppercase tracking-wider mb-2 font-bold">Net ROI (Profit/Loss)</div>
          <div className="font-mono text-4xl font-bold text-cost">{roi.toFixed(1)}%</div>
          <div className="text-xs font-mono text-cost mt-1">({totalPnl.toFixed(2)} Units)</div>
        </div>
      </div>

      {/* Historical Bets */}
      <div>
        <h3 className="text-2xl font-bold font-sans uppercase tracking-tight mb-6">Historical Bets Ledger</h3>
        <p className="text-sm text-muted mb-4">Expand a match to see its scoreline and model probabilities. Show more rows to explore the full ledger.</p>
        <div className="overflow-x-auto bg-surface border-2 border-ink shadow-[8px_8px_0px_0px_rgba(17,24,39,1)]">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b-2 border-ink font-mono text-xs uppercase text-muted tracking-wider bg-bg">
                <th className="py-3 px-4 font-normal">Date</th>
                <th className="py-3 px-4 font-normal">League</th>
                <th className="py-3 px-4 font-normal">Match</th>
                <th className="py-3 px-4 font-normal text-center">Pick</th>
                <th className="py-3 px-4 font-normal text-right">Model P()</th>
                <th className="py-3 px-4 font-normal text-right">Odds Taken</th>
                <th className="py-3 px-4 font-normal text-center">Match Res</th>
                <th className="py-3 px-4 font-normal text-center">Bet Outcome</th>
                <th className="py-3 px-4 font-normal text-right">PnL</th>
              </tr>
            </thead>
            <tbody className="font-mono text-sm">
              {bets.slice(0, visibleCount).map((bet) => (
                <React.Fragment key={bet.id}>
                  <tr 
                    onClick={() => setExpandedBet(expandedBet === bet.id ? null : bet.id)}
                    className="border-b border-dashed border-line hover:bg-bg transition-colors cursor-pointer"
                  >
                    <td className="py-3 px-4 text-muted">{bet.date ? bet.date : bet.season}</td>
                    <td className="py-3 px-4">{bet.league}</td>
                    <td className="py-3 px-4 font-sans font-bold text-base">
                      <button
                        type="button"
                        aria-expanded={expandedBet === bet.id}
                        aria-controls={expandedBet === bet.id ? `match-details-${bet.id}` : undefined}
                        onClick={(event) => {
                          event.stopPropagation();
                          setExpandedBet(expandedBet === bet.id ? null : bet.id);
                        }}
                        className="text-left hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ink"
                      >
                        {bet.match}
                        <span className="block mt-1 font-mono text-xs font-normal text-muted">{expandedBet === bet.id ? '− Hide details' : '+ View details'}</span>
                      </button>
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span className="border border-ink px-2 py-0.5 text-xs font-bold">{bet.pick}</span>
                    </td>
                    <td className="py-3 px-4 text-right">{formatPct(bet.prob)}</td>
                    <td className="py-3 px-4 text-right">{formatOdds(bet.odds_taken)}</td>
                    <td className="py-3 px-4 text-center font-bold">{bet.result}</td>
                    <td className="py-3 px-4 text-center">
                      {bet.won === 1 ? (
                         <span className="text-accent font-bold">WON</span>
                      ) : (
                         <span className="text-cost font-bold">LOST</span>
                      )}
                    </td>
                    <td className={`py-3 px-4 text-right font-bold ${bet.pnl > 0 ? 'text-accent' : 'text-cost'}`}>
                      {bet.pnl > 0 ? '+' : ''}{bet.pnl.toFixed(2)}
                    </td>
                  </tr>
                  
                  {expandedBet === bet.id && (
                    <tr id={`match-details-${bet.id}`} className="bg-bg border-b-2 border-ink">
                      <td colSpan={9} className="p-0">
                        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-8 border-l-4 border-accent">
                          <div>
                            <h4 className="font-sans font-bold uppercase tracking-tight text-xs text-muted mb-4">Match Facts</h4>
                            <div className="flex justify-between items-center bg-surface border-2 border-ink p-4 shadow-[4px_4px_0px_0px_rgba(17,24,39,1)]">
                              <span className="font-sans font-bold text-lg">{bet.match.split(' vs ')[0]}</span>
                              <span className="font-mono text-2xl font-bold bg-ink text-surface px-4 py-1">{bet.scoreline || '?-?'}</span>
                              <span className="font-sans font-bold text-lg">{bet.match.split(' vs ')[1]}</span>
                            </div>
                          </div>
                          <div>
                            <h4 className="font-sans font-bold uppercase tracking-tight text-xs text-muted mb-4">Model Distribution</h4>
                            <div className="bg-surface border-2 border-ink p-4 shadow-[4px_4px_0px_0px_rgba(17,24,39,1)] grid grid-cols-3 text-center divide-x-2 divide-ink">
                              <div>
                                <div className="text-xs text-muted uppercase mb-1">Home</div>
                                <div className={`text-lg font-bold ${bet.pick === 'Home' ? 'text-accent' : ''}`}>{bet.p_home ? formatPct(bet.p_home) : '-'}</div>
                              </div>
                              <div>
                                <div className="text-xs text-muted uppercase mb-1">Draw</div>
                                <div className={`text-lg font-bold ${bet.pick === 'Draw' ? 'text-accent' : ''}`}>{bet.p_draw ? formatPct(bet.p_draw) : '-'}</div>
                              </div>
                              <div>
                                <div className="text-xs text-muted uppercase mb-1">Away</div>
                                <div className={`text-lg font-bold ${bet.pick === 'Away' ? 'text-accent' : ''}`}>{bet.p_away ? formatPct(bet.p_away) : '-'}</div>
                              </div>
                            </div>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
          <div className="bg-bg px-4 py-5 border-t-2 border-ink flex flex-wrap items-center justify-center gap-4">
            <p aria-live="polite" className="font-mono text-xs text-muted">Showing {Math.min(visibleCount, bets.length)} of {bets.length} historical bets.</p>
            {visibleCount < bets.length && (
              <>
                <button type="button" onClick={() => setVisibleCount(count => Math.min(count + 50, bets.length))} className="border-2 border-ink bg-ink text-surface px-4 py-2 font-mono text-xs font-bold uppercase hover:bg-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ink">Show {Math.min(50, bets.length - visibleCount)} more</button>
                <button type="button" onClick={() => setVisibleCount(bets.length)} className="border-2 border-ink px-4 py-2 font-mono text-xs font-bold uppercase hover:bg-surface focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ink">Show all {bets.length}</button>
              </>
            )}
            {visibleCount > 50 && (
              <button type="button" onClick={() => { setVisibleCount(50); setExpandedBet(null); }} className="border-2 border-ink px-4 py-2 font-mono text-xs font-bold uppercase hover:bg-surface focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ink">Show fewer</button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
