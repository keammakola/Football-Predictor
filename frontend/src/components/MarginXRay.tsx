import { useState } from 'react';
import type { MarketSelection } from './TechnicalTools';

const outcomes = ['home', 'draw', 'away'] as const;
const labels = { home: 'Home win', draw: 'Draw', away: 'Away win' };
const initialOdds = { home: '2.50', draw: '3.30', away: '2.80' };
const pct = (n: number) => `${(n * 100).toFixed(1)}%`;

export function MarginXRay({ market }: { market?: MarketSelection }) {
  const [odds, setOdds] = useState(market ? { home: String(market.home), draw: String(market.draw), away: String(market.away) } : initialOdds);
  const [match, setMatch] = useState(market?.match || '');
  const values = outcomes.map(key => Number(odds[key]));
  const valid = values.every(n => Number.isFinite(n) && n > 1);
  const total = valid ? values.reduce((sum, n) => sum + 1 / n, 0) : 0;
  const margin = total - 1;
  const rows = outcomes.map((key, index) => ({ key, implied: valid ? 1 / values[index] : 0, probability: valid ? 1 / values[index] / total : 0 }));

  return (
    <section id="margin-calculator" className="market-workbench" aria-labelledby="calculator-title">
      <div className="market-input-panel">
        <div className="tool-title"><span className="tool-symbol" aria-hidden="true">⅟</span><div><h3 id="calculator-title">Margin X-Ray</h3><p>A clearer view of the 1X2 market</p></div></div>
        <p className="input-description">Enter decimal odds for all three outcomes to estimate the market’s probabilities with the margin removed.</p>
        {match && <div className="loaded-match">Loaded: {match}</div>}
        <div className="market-fields">{outcomes.map(key => {
          const invalid = !Number.isFinite(Number(odds[key])) || Number(odds[key]) <= 1;
          return <div key={key}><label htmlFor={`odds-${key}`}>{labels[key]}</label><div className="odds-field"><span aria-hidden="true">{key === 'home' ? '1' : key === 'draw' ? 'X' : '2'}</span><input id={`odds-${key}`} type="number" inputMode="decimal" min="1.01" step="0.01" value={odds[key]} aria-invalid={invalid} aria-describedby={invalid ? 'odds-error' : undefined} onChange={e => setOdds(prev => ({ ...prev, [key]: e.target.value }))} /></div></div>;
        })}</div>
        {!valid && <p className="tools-error" id="odds-error" role="alert">Enter a finite decimal odd greater than 1 for every outcome.</p>}
        <button className="reset-button" onClick={() => { setOdds(initialOdds); setMatch(''); }}>Reset to example</button>
        <div className="method-note"><strong>How it works</strong><p>Each implied probability (1 ÷ odds) is divided by their total. This proportional method estimates fair probabilities; it doesn’t establish the true chance of a result.</p></div>
      </div>
      <div className="market-results-panel">
        <div className="results-heading"><h4>Market breakdown</h4><span className={`market-status ${valid && margin < 0 ? 'underround' : ''}`}>{!valid ? 'Awaiting valid odds' : margin < -0.000001 ? 'Underround market' : margin > 0.000001 ? 'Margin detected' : 'Balanced market'}</span></div>
        <div className="probability-strip" aria-label="Estimated margin-free probabilities">{valid ? rows.map(row => <div className={`probability-segment ${row.key}`} key={row.key} style={{ width: pct(row.probability) }} title={`${labels[row.key]}: ${pct(row.probability)}`}><span>{row.key === 'home' ? '1' : row.key === 'draw' ? 'X' : '2'}</span></div>) : <div className="probability-placeholder">Add all three odds to see the distribution</div>}</div>
        <div className="probability-legend">{rows.map(row => <span key={row.key}><i className={row.key} />{labels[row.key]} <strong>{valid ? pct(row.probability) : '—'}</strong></span>)}</div>
        <div className="tools-table-scroll"><table className="breakdown-table"><thead><tr><th>Outcome</th><th>Implied</th><th>Margin-free</th><th>Fair odds</th></tr></thead><tbody>{rows.map(row => <tr key={row.key}><th scope="row">{labels[row.key]}</th><td>{valid ? pct(row.implied) : '—'}</td><td>{valid ? pct(row.probability) : '—'}</td><td className="fair-odds">{valid ? (1 / row.probability).toFixed(2) : '—'}</td></tr>)}</tbody></table></div>
        <div className="market-metrics" aria-live="polite"><div><span>Total implied probability</span><strong>{valid ? pct(total) : '—'}</strong></div><div><span>Bookmaker overround</span><strong>{valid ? pct(margin) : '—'}</strong></div></div>
        <p className="results-note">{valid && margin < 0 ? 'The implied probabilities sum to less than 100%. Check that these odds belong to the same match and market.' : 'Overround measures how far the implied probabilities exceed 100%. Fair odds are the reciprocal of the estimated margin-free probabilities.'}</p>
      </div>
    </section>
  );
}
