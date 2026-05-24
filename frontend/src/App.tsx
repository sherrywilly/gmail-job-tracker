import './App.css'
import { type FormEvent, useEffect, useMemo, useState } from 'react'
import type { ApiError, EmailOut, EmailResponse } from './api'
import { classifyEmail, getEmail, listEmails, login, register, syncInbox } from './api'

function getStoredToken(): string | null {
  try {
    return localStorage.getItem('jwt') || null
  } catch {
    return null
  }
}

function setStoredToken(token: string | null) {
  try {
    if (token) localStorage.setItem('jwt', token)
    else localStorage.removeItem('jwt')
  } catch {
    // ignore
  }
}

function formatDate(iso: string | null): string {
  if (!iso) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString()
}

export default function App() {
  const [token, setToken] = useState<string | null>(() => getStoredToken())
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const [unreadOnly, setUnreadOnly] = useState(true)
  const [emails, setEmails] = useState<EmailOut[]>([])
  const [selectedId, setSelectedId] = useState<number | null>(null)
  const [selected, setSelected] = useState<EmailResponse | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  const isAuthed = !!token
  const title = useMemo(() => (unreadOnly ? 'Unread' : 'All'), [unreadOnly])

  async function refreshList(nextToken: string) {
    const list = await listEmails(nextToken, { unreadOnly, limit: 50, offset: 0 })
    setEmails(list)
    if (list.length && selectedId == null) setSelectedId(list[0]!.id)
  }

  useEffect(() => {
    if (!token) return
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refreshList(token)
      .then(() => setError(null))
      .catch((e: ApiError) => setError(e.message))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token, unreadOnly])

  useEffect(() => {
    if (!token || selectedId == null) return
    getEmail(token, selectedId)
      .then((data) => {
        setSelected(data)
        setError(null)
      })
      .catch((e: ApiError) => setError(e.message))
  }, [token, selectedId])

  async function onAuthSubmit(e: FormEvent) {
    e.preventDefault()
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      if (mode === 'register') {
        await register(email, password)
        setNotice('Account created. You can log in now.')
        setMode('login')
      } else {
        const t = await login(email, password)
        setStoredToken(t)
        setToken(t)
      }
    } catch (err) {
      const apiErr = err as ApiError
      setError(apiErr.message || 'Request failed')
    } finally {
      setBusy(false)
    }
  }

  async function onSync() {
    if (!token) return
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      await syncInbox(token)
      setNotice('Sync enqueued. Refresh in a bit.')
    } catch (err) {
      const apiErr = err as ApiError
      setError(apiErr.message || 'Sync failed')
    } finally {
      setBusy(false)
    }
  }

  async function onClassify() {
    if (!token || !selected) return
    setBusy(true)
    setError(null)
    setNotice(null)
    try {
      const cls = await classifyEmail(token, selected.id)
      setSelected({ ...selected, classification: cls })
      setNotice('Classification updated.')
    } catch (err) {
      const apiErr = err as ApiError
      setError(apiErr.message || 'Classification failed')
    } finally {
      setBusy(false)
    }
  }

  function onLogout() {
    setStoredToken(null)
    setToken(null)
    setEmails([])
    setSelected(null)
    setSelectedId(null)
  }

  if (!isAuthed) {
    return (
      <div className="page">
        <header className="topbar">
          <div className="brand">Gmail Job Tracker</div>
          <div className="pill">React Dashboard</div>
        </header>

        <main className="auth">
          <div>
            <h1>{mode === 'login' ? 'Log in' : 'Create account'}</h1>
            <p className="muted">
              Uses the FastAPI auth endpoints at <code>/api/auth</code>. Passwords must be 8+ characters.
            </p>

            <form className="card" onSubmit={onAuthSubmit}>
              <label>
                Email
                <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" required />
              </label>
              <label>
                Password
                <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" required />
              </label>

              <div className="row">
                <button type="submit" disabled={busy}>
                  {mode === 'login' ? 'Log in' : 'Register'}
                </button>
                <button
                  type="button"
                  className="secondary"
                  disabled={busy}
                  onClick={() => setMode(mode === 'login' ? 'register' : 'login')}
                >
                  {mode === 'login' ? 'Need an account?' : 'Have an account?'}
                </button>
              </div>

              {notice ? <div className="notice">{notice}</div> : null}
              {error ? <div className="error">{error}</div> : null}
            </form>
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">Gmail Job Tracker</div>
        <div className="row">
          <div className="toggle">
            <button
              type="button"
              className={unreadOnly ? 'active' : ''}
              onClick={() => setUnreadOnly(true)}
              disabled={busy}
            >
              Unread
            </button>
            <button
              type="button"
              className={!unreadOnly ? 'active' : ''}
              onClick={() => setUnreadOnly(false)}
              disabled={busy}
            >
              All
            </button>
          </div>
          <button type="button" className="secondary" onClick={onSync} disabled={busy}>
            Sync Inbox
          </button>
          <button type="button" className="secondary" onClick={onLogout} disabled={busy}>
            Log out
          </button>
        </div>
      </header>

      <main className="grid">
        <section className="card list">
          <div className="sectionTitle">
            <h2>{title} Emails</h2>
            <button
              type="button"
              className="secondary"
              disabled={busy || !token}
              onClick={() => token && refreshList(token)}
            >
              Refresh
            </button>
          </div>
          <div className="listBody">
            {emails.length === 0 ? (
              <div className="muted">No emails found.</div>
            ) : (
              <ul className="emailList">
                {emails.map((m) => (
                  <li key={m.id}>
                    <button
                      type="button"
                      className={m.id === selectedId ? 'selected' : ''}
                      onClick={() => setSelectedId(m.id)}
                    >
                      <div className="subject">{m.subject || '(no subject)'}</div>
                      <div className="meta">
                        <span>{m.sender || ''}</span>
                        <span>{formatDate(m.received_at)}</span>
                        {m.is_unread ? <span className="badge">unread</span> : null}
                      </div>
                      <div className="snippet">{m.snippet || ''}</div>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </section>

        <section className="card detail">
          <div className="sectionTitle">
            <h2>Details</h2>
            <div className="row">
              <button type="button" className="secondary" onClick={onClassify} disabled={busy || !selected}>
                Classify
              </button>
            </div>
          </div>

          {notice ? <div className="notice">{notice}</div> : null}
          {error ? <div className="error">{error}</div> : null}

          {!selected ? (
            <div className="muted">Select an email.</div>
          ) : (
            <div className="detailBody">
              <h3 className="detailSubject">{selected.subject || '(no subject)'}</h3>
              <div className="meta">
                <span>{selected.sender || ''}</span>
                <span>{formatDate(selected.received_at)}</span>
                {selected.is_unread ? <span className="badge">unread</span> : null}
              </div>

              <div className="detailGrid">
                <div className="panel">
                  <div className="panelTitle">Snippet</div>
                  <div className="panelBody">{selected.snippet || ''}</div>
                </div>
                <div className="panel">
                  <div className="panelTitle">Classification</div>
                  <div className="panelBody">
                    {selected.classification ? (
                      <>
                        <div className="kv">
                          <span className="k">Category</span>
                          <span className="v">{selected.classification.category}</span>
                        </div>
                        <div className="kv">
                          <span className="k">Urgency</span>
                          <span className="v">{selected.classification.urgency}</span>
                        </div>
                        <div className="kv">
                          <span className="k">Attention</span>
                          <span className="v">{selected.classification.requires_attention ? 'Yes' : 'No'}</span>
                        </div>
                        <div className="kv">
                          <span className="k">Confidence</span>
                          <span className="v">{selected.classification.confidence}%</span>
                        </div>
                        <div className="panelTitle">Summary</div>
                        <div className="panelBody">{selected.classification.short_summary}</div>
                        {selected.classification.suggested_reply ? (
                          <>
                            <div className="panelTitle">Suggested Reply</div>
                            <pre className="reply">{selected.classification.suggested_reply}</pre>
                          </>
                        ) : null}
                      </>
                    ) : (
                      <div className="muted">
                        Not classified yet. Click <b>Classify</b>.
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {selected.body ? (
                <div className="panel">
                  <div className="panelTitle">Body (text)</div>
                  <pre className="body">{selected.body}</pre>
                </div>
              ) : null}
            </div>
          )}
        </section>
      </main>
    </div>
  )
}
