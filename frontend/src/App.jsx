import { useEffect, useState } from 'react'
import Header from './components/Header.jsx'
import Sidebar from './components/Sidebar.jsx'
import KpiCards from './components/KpiCards.jsx'
import ScoreChart from './components/ScoreChart.jsx'
import WeeklyDetail from './components/WeeklyDetail.jsx'
import { fetchBackendStatus, scanSample, scanGithub } from './api.js'

export default function App() {
  const [backendStatus, setBackendStatus] = useState(null)
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    fetchBackendStatus()
      .then(setBackendStatus)
      .catch(() => setBackendStatus(null))
  }, [])

  async function handleRun({ mode, owner, repo }) {
    setLoading(true)
    setError(null)
    try {
      const data = mode === 'github' ? await scanGithub(owner, repo) : await scanSample()
      setResult(data)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen">
      <div className="max-w-6xl mx-auto px-6 py-10">
        <Header />
        <div className="flex flex-col lg:flex-row gap-6">
          <Sidebar onRun={handleRun} loading={loading} backendStatus={backendStatus} />

          <main className="flex-1 min-w-0 space-y-6">
            {error && (
              <div className="bg-danger/[0.10] border border-danger/25 text-danger rounded-2xl px-4 py-3 text-sm">
                {error}
              </div>
            )}

            {!result && !error && (
              <div className="bg-white/[0.035] backdrop-blur-md border border-border rounded-2xl px-5 py-10 text-center text-textLo text-sm">
                Choose a data source in the sidebar and click{' '}
                <span className="font-semibold text-textHi">Run scan</span> to see results.
              </div>
            )}

            {result && (
              <>
                <div className="text-sm text-textLo">
                  Results for{' '}
                  <span className="font-mono text-textHi font-semibold">{result.entity_id}</span>
                </div>
                <KpiCards summary={result.summary} />
                <ScoreChart weeks={result.weeks} />
                <WeeklyDetail weeks={result.weeks} />
              </>
            )}
          </main>
        </div>
      </div>
    </div>
  )
}
