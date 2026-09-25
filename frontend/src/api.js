const API_BASE = import.meta.env.VITE_API_BASE || ''

export async function fetchBackendStatus() {
  const res = await fetch(`${API_BASE}/api/backend-status`)
  if (!res.ok) throw new Error('Failed to load backend status')
  return res.json()
}

export async function scanSample() {
  const res = await fetch(`${API_BASE}/api/scan/sample`, { method: 'POST' })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || 'Scan failed')
  }
  return res.json()
}

export async function scanGithub(owner, repo) {
  const res = await fetch(`${API_BASE}/api/scan/github`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ owner, repo }),
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || 'Scan failed')
  }
  return res.json()
}
