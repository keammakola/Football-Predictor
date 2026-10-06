import { MarginXRay } from './MarginXRay';
import { PredictionsTable } from './PredictionsTable';
import { useState } from 'react';
import './technical-tools.css';

export type MarketSelection = { home: number; draw: number; away: number; match: string };

export function TechnicalTools() {
  const [market, setMarket] = useState<MarketSelection>();
  const [selectionVersion, setSelectionVersion] = useState(0);
  return (
    <div className="tools-workspace">
      <section className="tools-intro">
        <div><h2>See what’s inside the odds.</h2><p>Unpack the bookmaker’s margin. Compare the model. Explore the numbers behind every match.</p></div>
        <a href="#prediction-ledger" className="tools-link">Explore the prediction ledger <span aria-hidden="true">↓</span></a>
      </section>
      <MarginXRay key={selectionVersion} market={market} />
      <PredictionsTable onSelectMarket={(selection) => { setMarket(selection); setSelectionVersion(n => n + 1); document.getElementById('margin-calculator')?.scrollIntoView({ behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth', block: 'start' }); }} />
    </div>
  );
}
