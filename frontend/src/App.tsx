import { useState } from 'react';
import { MainPage } from './components/MainPage';
import { TechnicalPage } from './components/TechnicalPage';

function App() {
  const [activeTab, setActiveTab] = useState<'main' | 'technical'>('main');

  return (
    <div className="min-h-screen p-4 md:p-12 flex flex-col items-center">
      <a href="#main-content" className="sr-only focus:not-sr-only focus:fixed focus:top-4 focus:left-4 focus:z-50 focus:bg-surface focus:p-3 focus:border-2 focus:border-ink">Skip to content</a>
      <header className="w-full max-w-7xl flex flex-col md:flex-row justify-between items-baseline mb-12 border-b-4 border-ink pb-6">
        <div>
          <h1 className="text-3xl md:text-4xl font-bold tracking-tight uppercase">The Football Experiment</h1>
          <p className="text-muted text-sm mt-2 max-w-xl leading-relaxed">I built a prediction bot to find out why winning picks still lose money.</p>
        </div>
        <nav aria-label="Main navigation" className="flex flex-wrap items-center gap-6 text-sm font-bold mt-6 md:mt-0 uppercase tracking-wide">
          <button
            onClick={() => setActiveTab('main')}
            aria-pressed={activeTab === 'main'}
            className={`hover:text-accent transition-colors ${activeTab === 'main' ? 'text-ink border-b-2 border-ink' : 'text-muted'}`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('technical')}
            aria-pressed={activeTab === 'technical'}
            className={`hover:text-accent transition-colors ${activeTab === 'technical' ? 'text-ink border-b-2 border-ink' : 'text-muted'}`}
          >
            Behind the Model
          </button>
          <a href="https://github.com/keammakola/Football-Predictor" target="_blank" rel="noreferrer" className="inline-flex min-h-11 items-center text-muted hover:text-accent transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-4">GitHub</a>
        </nav>
      </header>

      <main id="main-content" tabIndex={-1} className="w-full min-w-0 max-w-7xl">
        {activeTab === 'main' && <MainPage />}

        {activeTab === 'technical' && <TechnicalPage />}
      </main>

      {/* Responsible Gambling Disclaimer */}
      <div className="w-full max-w-7xl mt-16 border-2 border-ink bg-surface shadow-[6px_6px_0px_0px_rgba(17,24,39,1)]">
        <div className="bg-ink text-surface font-mono text-xs uppercase tracking-widest px-6 py-3 flex items-center gap-3">
          <span className="text-cost font-bold text-sm">⚠</span>
          <span>Responsible Gambling</span>
        </div>
        <div className="p-6">
          <p className="font-sans text-sm text-ink leading-relaxed mb-4">
            <strong>This site is for educational and informational purposes only.</strong> It examines a historical football backtest where winning picks still produced a loss. These results describe this model, selection rule and dataset; they do not establish that every betting strategy will lose. No content here constitutes financial or betting advice.
          </p>
          <p className="font-sans text-sm text-ink leading-relaxed mb-6">
            Gambling can be addictive. Only ever gamble with money you can afford to lose. If you or someone you know is struggling with gambling, free and confidential help is available 24/7:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 xl:grid-cols-6 gap-4">
            {[
              { name: 'BeGambleAware', region: 'UK', url: 'https://www.begambleaware.org', phone: '0808 8020 133' },
              { name: 'GamCare', region: 'UK', url: 'https://www.gamcare.org.uk', phone: '0808 8020 133' },
              { name: 'Gamblers Anonymous', region: 'International', url: 'https://www.gamblersanonymous.org', phone: 'Find local chapter' },
              { name: 'National Council on Problem Gambling', region: 'US', url: 'https://www.ncpgambling.org', phone: '1-800-522-4700' },
              { name: 'National Responsible Gambling Programme', region: 'South Africa', url: 'https://www.responsiblegambling.org.za', phone: '0800 006 008' },
            ].map((org) => (
              <a
                key={org.name}
                href={org.url}
                target="_blank"
                rel="noreferrer"
                className="block border-2 border-ink p-4 hover:bg-bg transition-colors group"
              >
                <div className="font-mono text-xs text-muted uppercase tracking-wider mb-1">{org.region}</div>
                <div className="font-sans font-bold text-sm text-ink group-hover:text-accent transition-colors mb-2">{org.name}</div>
                <div className="font-mono text-xs text-muted">{org.phone}</div>
              </a>
            ))}
          </div>
        </div>
      </div>

      <footer className="w-full max-w-7xl mt-8 pt-6 border-t-2 border-dashed border-line text-sm font-mono text-muted flex flex-wrap gap-4 justify-between">
        <a href="https://keabetswe.online" target="_blank" rel="noreferrer" className="inline-flex items-center justify-center border-2 border-ink bg-ink px-5 py-2 font-bold text-surface hover:bg-accent transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-accent focus-visible:outline-offset-4">My Portfolio</a>
        <span>Winning picks. A losing backtest.</span>
      </footer>
    </div>
  )
}

export default App
