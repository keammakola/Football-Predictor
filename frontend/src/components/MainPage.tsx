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

const LEAGUE_LABELS: Record<string, string> = {
  EPL: 'Premier League', LaLiga: 'La Liga', Bundesliga: 'Bundesliga', SerieA: 'Serie A', Ligue1: 'Ligue 1',
};
const seasonLabel = (season: string) => /^\d{4}$/.test(season) ? `20${season.slice(0, 2)}/${season.slice(2)}` : season;

export const MainPage: React.FC = () => {
  const [bets, setBets] = useState<Bet[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [expandedBet, setExpandedBet] = useState<string | null>(null);
  const [visibleCount, setVisibleCount] = useState(50);
  const [league, setLeague] = useState('all');
  const [season, setSeason] = useState('all');
  const [query, setQuery] = useState('');
  const [error, setError] = useState(false);

  const resetRows = () => { setVisibleCount(50); setExpandedBet(null); };
  const clearFilters = () => { setLeague('all'); setSeason('all'); setQuery(''); resetRows(); };

  useEffect(() => {
    const controller = new AbortController();
    const read = async (url: string) => {
      const response = await fetch(url, { signal: controller.signal });
      if (!response.ok) throw new Error('Historical data unavailable');
      return response.json();
    };
    Promise.all([
      read('/data/bets.json'),
      read('/data/stats.json')
    ]).then(([betsData, statsData]) => {
      setBets(betsData);
      setStats(statsData);
      setLoading(false);
    }).catch(err => {
      if (controller.signal.aborted) return;
      console.error(err);
      setError(true);
      setLoading(false);
    });
    return () => controller.abort();
  }, []);

  const totalBets = bets.length;
  const totalWins = bets.filter(b => b.won === 1).length;
  const totalPnl = bets.reduce((acc, b) => acc + b.pnl, 0);
  const roi = totalBets > 0 ? (totalPnl / totalBets) * 100 : 0;
  const seasonsCount = new Set(bets.map(b => b.season)).size;
  const leagues = [...new Set(bets.map(bet => bet.league))].sort();
  const seasons = [...new Set(bets.map(bet => bet.season))].sort().reverse();
  const terms = query.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const filteredBets = bets.filter(bet => (league === 'all' || bet.league === league)
    && (season === 'all' || bet.season === season)
    && terms.every(term => bet.match.toLowerCase().includes(term)));
  const filtersActive = league !== 'all' || season !== 'all' || query.trim() !== '';

  const formatPct = (val: number) => (val * 100).toFixed(1) + '%';
  const formatOdds = (val: number) => val.toFixed(2);



  if (loading) {
    return <div className="animate-pulse text-muted font-mono uppercase">Loading ledger...</div>;
  }
  if (error) {
    return <div role="alert" className="border-2 border-ink bg-surface p-6"><p className="mb-4">The historical data could not be loaded. Reload the page to try again.</p><button type="button" onClick={() => window.location.reload()} className="bg-ink px-5 py-2 text-surface font-bold">Reload page</button></div>;
  }

  return (
    <div className="w-full">
      {/* Article Brief */}
      <div className="mb-12 border-b-2 border-ink pb-8">
        <h2 className="text-3xl font-bold font-serif mb-4 leading-tight">
          My Prediction Bot Won More Often Than It Lost. The Backtest Still Lost Money.
        </h2>
        <p className="text-xl font-sans text-ink/80 leading-relaxed max-w-4xl mb-6">
          I built a prediction engine for the top five European football leagues. In this historical backtest, its strong predictions had a {stats?.strong_hit_rate?.toFixed(1) ?? '—'}% hit rate. The {totalBets} selected bets won {totalBets > 0 ? ((totalWins / totalBets) * 100).toFixed(1) : '—'}% of the time across {seasonsCount} seasons, including a partial final season, but simulated one-unit stakes returned {roi.toFixed(1)}%. These results show how this model lost money despite winning more often than it lost. They do not establish that every strategy will lose or predict future returns.
        </p>
        <a 
          href="https://keammakola.hashnode.dev/house-always-wins"
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
          <span className="font-bold text-accent">THE STRATEGY:</span> Each simulated bet required <strong className="text-ink">at least 60% model confidence</strong>, a lead of at least 25 percentage points over the next most likely outcome, and recorded bookmaker odds above the model's fair odds. This was a model-estimated edge; it did not guarantee a profitable bet.
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
          <div className="font-mono text-4xl font-bold">{totalWins} <span className="text-base text-muted font-normal ml-2">({totalBets > 0 ? ((totalWins/totalBets)*100).toFixed(1) : '0.0'}% Hit Rate)</span></div>
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
        <form role="search" aria-label="Filter historical bets" onSubmit={event => event.preventDefault()} className="mb-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-[1fr_1fr_2fr_auto] items-end">
          <div><label htmlFor="ledger-league" className="text-sm font-bold">League</label><select id="ledger-league" value={league} onChange={event => { setLeague(event.target.value); resetRows(); }} className="mt-2 block w-full border-2 border-ink bg-surface px-3 py-2 font-normal"><option value="all">All leagues</option>{leagues.map(value => <option key={value} value={value}>{LEAGUE_LABELS[value] || value}</option>)}</select></div>
          <div><label htmlFor="ledger-season" className="text-sm font-bold">Season</label><select id="ledger-season" value={season} onChange={event => { setSeason(event.target.value); resetRows(); }} className="mt-2 block w-full border-2 border-ink bg-surface px-3 py-2 font-normal"><option value="all">All seasons</option>{seasons.map(value => <option key={value} value={value}>{seasonLabel(value)}</option>)}</select></div>
          <div><label htmlFor="ledger-search" className="text-sm font-bold">Search matches</label><input id="ledger-search" type="search" value={query} onChange={event => { setQuery(event.target.value); resetRows(); }} placeholder="Team or match name" className="mt-2 block min-h-11 w-full border-2 border-ink bg-surface px-3 py-2 font-normal" /></div>
          <button type="button" disabled={!filtersActive} onClick={clearFilters} className="border-2 border-ink bg-surface px-4 py-2 font-bold disabled:opacity-50 disabled:cursor-default">Clear filters</button>
        </form>
        <p aria-live="polite" className="text-sm text-muted mb-3">{filteredBets.length} matching bets of {bets.length}. Overview totals above cover the full experiment.</p>
        <p className="sm:hidden text-xs text-muted mb-3" id="ledger-scroll-hint">Swipe the table to see odds, results and returns.</p>
        <div role="region" aria-label="Historical bets table" tabIndex={0} aria-describedby="ledger-scroll-hint" className="overflow-x-auto max-w-full bg-surface border-2 border-ink shadow-[8px_8px_0px_0px_rgba(17,24,39,1)]">
          <table className="w-full min-w-[900px] text-left border-collapse">
            <caption className="sr-only">Historical simulated bets with model probabilities, recorded odds, results and returns in units</caption>
            <thead>
              <tr className="border-b-2 border-ink font-mono text-xs uppercase text-muted tracking-wider bg-bg">
                <th scope="col" className="py-3 px-4 font-normal">Date</th>
                <th scope="col" className="py-3 px-4 font-normal">League</th>
                <th scope="col" className="py-3 px-4 font-normal">Match</th>
                <th scope="col" className="py-3 px-4 font-normal text-center">Pick</th>
                <th scope="col" className="py-3 px-4 font-normal text-right">Model P()</th>
                <th scope="col" className="py-3 px-4 font-normal text-right">Odds Taken</th>
                <th scope="col" className="py-3 px-4 font-normal text-center">Match Res</th>
                <th scope="col" className="py-3 px-4 font-normal text-center">Bet Outcome</th>
                <th scope="col" className="py-3 px-4 font-normal text-right">PnL</th>
              </tr>
            </thead>
            <tbody className="font-mono text-sm">
              {filteredBets.length === 0 && <tr><td colSpan={9} className="p-6 text-center">No matches found. Try another team name or clear the filters.</td></tr>}
              {filteredBets.slice(0, visibleCount).map((bet) => (
                <React.Fragment key={bet.id}>
                  <tr 
                    onClick={() => setExpandedBet(expandedBet === bet.id ? null : bet.id)}
                    className="border-b border-dashed border-line hover:bg-bg transition-colors cursor-pointer"
                  >
                    <td className="py-3 px-4 text-muted">{bet.date ? bet.date : bet.season}</td>
                    <td className="py-3 px-4">{LEAGUE_LABELS[bet.league] || bet.league}</td>
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
                              <span className="font-mono text-2xl font-bold bg-ink text-surface px-4 py-1">{bet.scoreline || 'Not recorded'}</span>
                              <span className="font-sans font-bold text-lg">{bet.match.split(' vs ')[1]}</span>
                            </div>
                          </div>
                          <div>
                            <h4 className="font-sans font-bold uppercase tracking-tight text-xs text-muted mb-4">Model Distribution</h4>
                            <div className="bg-surface border-2 border-ink p-4 shadow-[4px_4px_0px_0px_rgba(17,24,39,1)] grid grid-cols-3 text-center divide-x-2 divide-ink">
                              <div>
                                <div className="text-xs text-muted uppercase mb-1">Home</div>
                                <div className={`text-lg font-bold ${bet.pick === 'Home' ? 'text-accent' : ''}`}>{bet.p_home != null ? formatPct(bet.p_home) : '-'}</div>
                              </div>
                              <div>
                                <div className="text-xs text-muted uppercase mb-1">Draw</div>
                                <div className={`text-lg font-bold ${bet.pick === 'Draw' ? 'text-accent' : ''}`}>{bet.p_draw != null ? formatPct(bet.p_draw) : '-'}</div>
                              </div>
                              <div>
                                <div className="text-xs text-muted uppercase mb-1">Away</div>
                                <div className={`text-lg font-bold ${bet.pick === 'Away' ? 'text-accent' : ''}`}>{bet.p_away != null ? formatPct(bet.p_away) : '-'}</div>
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
            <p aria-live="polite" className="font-mono text-xs text-muted">Showing {Math.min(visibleCount, filteredBets.length)} of {filteredBets.length} matching bets.</p>
            {visibleCount < filteredBets.length && (
              <>
                <button type="button" onClick={() => setVisibleCount(count => Math.min(count + 50, filteredBets.length))} className="border-2 border-ink bg-ink text-surface px-4 py-2 font-mono text-xs font-bold uppercase hover:bg-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ink">Show {Math.min(50, filteredBets.length - visibleCount)} more</button>
                <button type="button" onClick={() => setVisibleCount(filteredBets.length)} className="border-2 border-ink px-4 py-2 font-mono text-xs font-bold uppercase hover:bg-surface focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-ink">Show all {filteredBets.length}</button>
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
