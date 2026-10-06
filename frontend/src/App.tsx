import { MarginXRay } from './components/MarginXRay';

function App() {
  return (
    <div className="p-8 flex flex-col items-center">
      <header className="w-full max-w-6xl flex justify-between items-center mb-16">
        <h1 className="text-[30px] font-bold font-serif">THE HOUSE ALWAYS WINS</h1>
        <nav className="flex gap-6 text-sm font-medium">
          <a href="#" className="hover:underline">Predictions</a>
          <a href="#" className="hover:underline">Margin X-Ray</a>
          <a href="#" className="hover:underline">About</a>
        </nav>
      </header>

      <main className="w-full max-w-6xl">
        <h1 className="text-[44px] font-bold mb-6 font-serif">AFL Margin X-Ray</h1>
        <p className="mb-12 text-lg text-gray-700 max-w-3xl">
          Visualise the probability distribution of margins for AFL matches using our state-of-the-art predictive model. Explore the exact odds behind each possible outcome.
        </p>

        <MarginXRay />
      </main>
    </div>
  )
}

export default App
