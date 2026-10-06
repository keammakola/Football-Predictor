const work = [
  {
    title: 'Built a repeatable data pipeline',
    description: 'I assembled historical results and bookmaker odds across five leagues, standardised team names, and turned the match history into model-ready tables.',
    reason: 'Consistent names and dates make it possible to join sources and compare models on the same matches. Historical odds provide a market benchmark alongside the results.',
    evidence: 'data.py · team_names.py · matches.csv',
  },
  {
    title: 'Started with team strength, then added match context',
    description: 'I built Elo ratings, rest-day features, and rolling expected-goals form using observed Understat match data. The collector records source URLs and match IDs, validates its caches, and never substitutes synthetic xG.',
    reason: 'Elo gives me a simple baseline, rest days describe the fixture schedule, and expected goals add observations about chance creation and defence. Team-specific form uses only earlier matches to avoid using the result I am trying to predict.',
    evidence: 'elo.py · features.py · xg_scraper.py',
  },
  {
    title: 'Combined two approaches to prediction',
    description: 'I implemented a Dixon–Coles goals model and an XGBoost classifier. The backtest averages their home, draw, and away probabilities with equal weights.',
    reason: 'Dixon–Coles provides an explicit attack-and-defence model with a correction for low scores. XGBoost lets me test relationships between multiple match features. The equal-weight blend is a simple starting point whose value still needs to be measured.',
    evidence: 'dixon_coles.py · train_xgb.py · backtest.py',
  },
  {
    title: 'Evaluated predictions against recorded outcomes',
    description: 'I built season-by-season backtests, confidence tiers, probability scoring, market comparisons, and a unit-stake profit-and-loss ledger.',
    reason: 'A high hit rate alone doesn’t tell me whether probabilities are accurate or whether the available odds cover the losses. I need to inspect prediction quality and returns separately.',
    evidence: 'evaluate.py · backtest.py · audit_backtest.py · bets.csv',
  },
];

const tools = [
  ['Python', 'Data preparation, model training, backtests, and export scripts.', 'One language connects the numerical work and the repeatable pipeline.'],
  ['pandas + NumPy', 'Match tables, feature calculations, and probability arrays.', 'They make chronological transformations and numerical calculations practical.'],
  ['SciPy', 'Poisson probabilities and optimisation for Dixon–Coles.', 'The goals model needs a probability distribution and a constrained parameter fit.'],
  ['scikit-learn + XGBoost', 'The logistic baseline, class encoding, evaluation metrics, and boosted trees.', 'A simple baseline gives the more flexible model something concrete to improve on.'],
  ['React + TypeScript', 'The interactive evidence page and typed data components.', 'Reusable components keep the charts consistent; types help catch mismatches in the data they consume.'],
  ['Vite + Tailwind CSS', 'Frontend builds and the visual system.', 'They support quick iteration and a consistent layout across screen sizes.'],
];

export function ProofOfWork() {
  return (
    <section aria-labelledby="proof-of-work-title" className="space-y-12">
      <div>
        <div className="font-mono text-xs text-accent uppercase tracking-widest mb-2">Section 03</div>
        <h3 id="proof-of-work-title" className="text-2xl font-bold uppercase tracking-tight mb-3">Proof of work</h3>
        <p className="text-lg leading-relaxed max-w-3xl text-ink/80">What I built, the tools I used, and the decisions behind the project.</p>
      </div>

      <div className="grid md:grid-cols-[1fr_2fr] gap-6 md:gap-12 border-t-2 border-ink pt-8">
        <h4 className="text-xl font-bold">Why I built it</h4>
        <div className="space-y-4 text-ink/80 leading-relaxed max-w-3xl">
          <p>I started by asking whether I could identify football matches with a high probability of a particular result. That became a broader investigation: how do those predictions compare with the market, and what happens when I apply them to recorded odds?</p>
          <p>I chose to output home-win, draw, and away-win probabilities rather than a single pick. That makes uncertainty visible and gives me something I can evaluate against actual outcomes.</p>
          <p>This page brings the implementation and its results together, so the work can be inspected beyond a headline win rate.</p>
        </div>
      </div>

      <div>
        <h4 className="text-xl font-bold mb-6">What I did and why</h4>
        <div className="grid md:grid-cols-2 gap-6">{work.map(item => (
          <article key={item.title} className="bg-surface border-2 border-ink p-6 md:p-8 flex flex-col">
            <h5 className="text-lg font-bold mb-3">{item.title}</h5>
            <p className="text-sm text-ink/80 leading-relaxed mb-5">{item.description}</p>
            <p className="text-sm text-ink/80 leading-relaxed mb-6"><strong className="text-ink">Why I chose this approach: </strong>{item.reason}</p>
            <div className="mt-auto border-t border-dashed border-line pt-4"><span className="block text-xs text-muted mb-2">Implementation evidence</span><p className="font-mono text-xs leading-relaxed break-words">{item.evidence}</p></div>
          </article>
        ))}</div>
      </div>

      <div>
        <h4 className="text-xl font-bold mb-6">What tools I used</h4>
        <div className="overflow-x-auto border-2 border-ink bg-surface">
          <table className="w-full text-left min-w-[640px]">
            <caption className="sr-only">Project tools, their role, and the reasons for choosing them</caption>
            <thead className="bg-ink text-surface text-sm"><tr><th scope="col" className="p-4">Tool</th><th scope="col" className="p-4">What I used it for</th><th scope="col" className="p-4">Why I chose it</th></tr></thead>
            <tbody className="text-sm">{tools.map(([tool, use, reason]) => <tr key={tool} className="border-b border-dashed border-line"><th scope="row" className="p-4 align-top font-bold w-1/4">{tool}</th><td className="p-4 align-top leading-relaxed text-ink/80">{use}</td><td className="p-4 align-top leading-relaxed text-ink/80">{reason}</td></tr>)}</tbody>
          </table>
        </div>
      </div>

      <div className="grid md:grid-cols-[1fr_2fr] gap-6 md:gap-12 border-t-2 border-ink pt-8">
        <h4 className="text-xl font-bold">How I checked the work</h4>
        <div className="space-y-4 text-sm leading-relaxed text-ink/80 max-w-3xl">
          <p><strong className="text-ink">Chronological evaluation.</strong> The backtest fits models on earlier seasons and evaluates them on a later season, rather than randomly mixing past and future matches.</p>
          <p><strong className="text-ink">Targeted leakage checks.</strong> The Elo tests change current and future results and check that earlier features stay unchanged. These tests cover the Elo feature path; they don’t certify every part of the ensemble pipeline.</p>
          <p><strong className="text-ink">Several measures of performance.</strong> The evaluation code includes log loss, Brier score, accuracy, calibration tables, and comparison with margin-free market probabilities. The charts above show the selected bet ledger, rather than every match the model predicted.</p>
          <p><strong className="text-ink">Limits of the evidence.</strong> A rising win rate across confidence groups alone does not establish calibration. Historical returns also depend on the selection rule and recorded odds; the displayed ledger only accepts recorded Bet365 odds that match the source CSVs. These are historical simulations, not a verified live betting record.</p>
          <div className="flex flex-wrap gap-4 pt-3">
            <a href="/data/bets.json" download className="border-2 border-ink bg-surface px-4 py-3 text-ink font-bold hover:bg-bg focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-4">Download the bet ledger</a>
            <a href="/data/predictions-all.json" download className="border-2 border-ink bg-surface px-4 py-3 text-ink font-bold hover:bg-bg focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-4">Download match predictions</a>
          </div>
          <p className="text-xs text-muted">The downloadable files are the JSON exports used by the frontend. Model and script filenames above identify the corresponding implementation in the project. The bet export is checked against cached historical source CSVs; source metadata is available above.</p>
        </div>
      </div>
    </section>
  );
}
