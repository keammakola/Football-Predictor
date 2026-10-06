import { useEffect, useMemo, useState } from 'react';
import type { MarketSelection } from './TechnicalTools';

interface Prediction {
  id: string; date?: string; logged_at_utc: string | null; kickoff_utc?: string | null; league: string; home: string; away: string;
  p_home: number; p_draw: number; p_away: number; odds_home: number; odds_draw: number; odds_away: number; result: string | null;
}
const pageSize = 12;
const probability = (value: number) => Number.isFinite(value) ? `${(value * 100).toFixed(1)}%` : '—';
const odds = (value: number) => Number.isFinite(value) && value > 1 ? value.toFixed(2) : '—';
const date = (row: Prediction) => row.date || row.kickoff_utc || row.logged_at_utc || ''; 

export function PredictionsTable({ onSelectMarket }: { onSelectMarket?: (market: MarketSelection) => void }) {
  const [data, setData] = useState<Prediction[]>([]);
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading');
  const [query, setQuery] = useState('');
  const [league, setLeague] = useState('all');
  const [result, setResult] = useState('all');
  const [page, setPage] = useState(0);
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    const controller = new AbortController();
    fetch('/data/predictions-all.json', { signal: controller.signal }).then(response => {
      if (!response.ok) throw new Error('Unable to load predictions');
      return response.json();
    }).then((json: Prediction[]) => {
      if (!Array.isArray(json)) throw new Error('Invalid prediction data');
      setData([...json].sort((a, b) => new Date(date(b)).getTime() - new Date(date(a)).getTime()));
      setStatus('ready');
    }).catch(() => { if (!controller.signal.aborted) setStatus('error'); });
    return () => controller.abort();
  }, [attempt]);
  const leagues = useMemo(() => [...new Set(data.map(row => row.league))].sort(), [data]);
  const filtered = useMemo(() => data.filter(row => (league === 'all' || row.league === league) && (result === 'all' || (result === 'pending' ? !row.result : !!row.result)) && `${row.home} ${row.away}`.toLowerCase().includes(query.trim().toLowerCase())), [data, league, result, query]);
  const pages = Math.ceil(filtered.length / pageSize);
  const currentPage = Math.min(page, Math.max(0, pages - 1));
  const visible = filtered.slice(currentPage * pageSize, (currentPage + 1) * pageSize);
  const resetFilters = () => { setQuery(''); setLeague('all'); setResult('all'); setPage(0); };
  return (
    <section id="prediction-ledger" className="prediction-ledger" aria-labelledby="ledger-title">
      <div className="ledger-heading"><div><h3 id="ledger-title">Prediction ledger</h3><p>Compare model probabilities with the recorded market odds.</p></div><span className="record-count">{status === 'ready' ? `${data.length.toLocaleString()} matches` : status === 'loading' ? 'Loading records…' : 'Records unavailable'}</span></div>
      <div className="ledger-controls"><div className="match-search"><label htmlFor="match-search">Find a match</label><input id="match-search" type="search" placeholder="Search home or away team…" value={query} onChange={e => { setQuery(e.target.value); setPage(0); }} /></div><div><label htmlFor="league-filter">League</label><select id="league-filter" value={league} onChange={e => { setLeague(e.target.value); setPage(0); }}><option value="all">All leagues</option>{leagues.map(name => <option key={name}>{name}</option>)}</select></div><div><label htmlFor="result-filter">Match status</label><select id="result-filter" value={result} onChange={e => { setResult(e.target.value); setPage(0); }}><option value="all">All matches</option><option value="settled">Completed</option><option value="pending">No recorded result</option></select></div></div>
      {status === 'loading' ? <div className="ledger-message" role="status">Loading the prediction ledger…</div> : status === 'error' ? <div className="ledger-message" role="alert"><h4>The ledger couldn’t be loaded.</h4><p>Check your connection and try again.</p><button className="tools-button" onClick={() => { setStatus('loading'); setAttempt(n => n + 1); }}>Try again</button></div> : filtered.length === 0 ? <div className="ledger-message"><h4>{data.length ? 'No matches found.' : 'No predictions available yet.'}</h4><p>{data.length ? 'Try a different team or clear the filters.' : 'The ledger will appear when prediction data is available.'}</p>{data.length > 0 && <button className="tools-button" onClick={resetFilters}>Clear filters</button>}</div> : <>
        <div className="tools-table-scroll"><table className="ledger-table"><thead><tr><th scope="col">Match / date</th><th scope="col">League</th><th scope="col">Model 1 / X / 2</th><th scope="col">Market 1 / X / 2</th><th scope="col">Result</th><th scope="col"><span className="sr-only">Calculator action</span></th></tr></thead><tbody>{visible.map((row, index) => {
          const canLoad = [row.odds_home, row.odds_draw, row.odds_away].every(n => Number.isFinite(n) && n > 1);
          const resultLabel = row.result === 'H' ? 'Home win' : row.result === 'A' ? 'Away win' : row.result === 'D' ? 'Draw' : row.result || 'Pending';
          return <tr key={`${row.id}-${index}`}><th scope="row"><span className="match-name">{row.home}<span className="versus"> vs </span>{row.away}</span><time dateTime={date(row)}>{date(row).split('T')[0]}</time></th><td><span className="league-tag">{row.league}</span></td><td><div className="three-values">{[row.p_home, row.p_draw, row.p_away].map((n, i) => <span key={i}>{probability(n)}</span>)}</div></td><td><div className="three-values market-values">{[row.odds_home, row.odds_draw, row.odds_away].map((n, i) => <span key={i}>{odds(n)}</span>)}</div></td><td><span className={`result-tag ${row.result ? 'settled' : ''}`}>{resultLabel}</span></td><td><button className="load-odds" disabled={!canLoad} aria-label={`Load odds for ${row.home} versus ${row.away}`} onClick={() => onSelectMarket?.({ home: row.odds_home, draw: row.odds_draw, away: row.odds_away, match: `${row.home} vs ${row.away}` })}>Load odds</button></td></tr>;
        })}</tbody></table></div>
        <div className="ledger-pagination"><span aria-live="polite">Showing {(currentPage * pageSize + 1).toLocaleString()}–{Math.min((currentPage + 1) * pageSize, filtered.length).toLocaleString()} of {filtered.length.toLocaleString()}</span><div><button disabled={currentPage === 0} onClick={() => setPage(currentPage - 1)} aria-label="Previous page">←</button><span>Page {currentPage + 1} of {pages}</span><button disabled={currentPage + 1 >= pages} onClick={() => setPage(currentPage + 1)} aria-label="Next page">→</button></div></div>
      </>}
      <p className="ledger-footnote">1 = home win, X = draw, 2 = away win. Odds are recorded snapshots; they may differ from the current market.</p>
    </section>
  );
}
