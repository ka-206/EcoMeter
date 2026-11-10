import { useEffect, useState } from 'react'
import { BrowserRouter, Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { api } from './api'
import './App.css'

const categoryColors = ['#234f38', '#7da68d', '#bfd7bf', '#5b7f6a', '#dfe9df']

const formatKg = (value) => `${Number(value || 0).toFixed(2)} kg CO₂e`
const toLocalDateInput = (date = new Date()) => {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
const formatDate = (value) => {
  if (!value) return '—'
  const [year, month, day] = value.slice(0, 10).split('-').map(Number)
  return `${String(day).padStart(2, '0')}-${String(month).padStart(2, '0')}-${year}`
}

function StatCard({ label, value, accent = 'primary' }) {
  const icons = {
    Today: <><circle cx="12" cy="12" r="8.5" /><path d="M12 7v5l3.2 1.8" /></>,
    'This week': <><path d="M4 19V5M4 19h16" /><path d="m7 14 3.2-3.2 2.7 2 4.8-6" /><path d="M14.7 6.8h3v3" /></>,
    'This month': <><rect x="3.5" y="5" width="17" height="16" rx="2.5" /><path d="M7.5 3.5v3M16.5 3.5v3M3.5 9.5h17" /><path d="M7.5 13h.01M12 13h.01M16.5 13h.01M7.5 17h.01M12 17h.01" /></>,
    'Average / day': <><path d="M4 18.5h16" /><path d="M7 16v-4M12 16V7M17 16v-7" /><path d="m5.5 8.5 4-3 3.2 2 5.8-4" /></>,
  }
  return (
    <div className={`stat-card ${accent}`}>
      <div className="stat-topline"><span>{label}</span><span className="stat-symbol" aria-hidden="true"><svg className="metric-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{icons[label]}</svg></span></div>
      <strong>{formatKg(value)}</strong>
    </div>
  )
}

function NavIcon({ name }) {
  const paths = {
    dashboard: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="5" rx="1" /><rect x="14" y="12" width="7" height="9" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /></>,
    activities: <><path d="M12 5v14M5 12h14" /><circle cx="12" cy="12" r="9" /></>,
    analytics: <><path d="M4 19V5M4 19h17" /><path d="m7 15 4-4 3 2 5-6" /></>,
    goals: <><circle cx="12" cy="12" r="9" /><circle cx="12" cy="12" r="5" /><circle cx="12" cy="12" r="1" /></>,
  }
  return (
    <svg className="nav-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {paths[name]}
    </svg>
  )
}

function Layout({ children }) {
  const location = useLocation()
  const [todayLabel, setTodayLabel] = useState(() => new Intl.DateTimeFormat('en', { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date()))
  const pageTitles = {
    '/': 'Dashboard',
    '/activities': 'Activity log',
    '/analytics': 'Insights',
    '/goals': 'Your goals',
  }

  useEffect(() => {
    let timeoutId
    const updateDate = () => {
      setTodayLabel(new Intl.DateTimeFormat('en', { weekday: 'long', month: 'long', day: 'numeric' }).format(new Date()))
      const now = new Date()
      const nextMidnight = new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1)
      timeoutId = window.setTimeout(updateDate, nextMidnight.getTime() - now.getTime())
    }
    const updateOnFocus = () => {
      if (timeoutId) window.clearTimeout(timeoutId)
      updateDate()
    }

    updateDate()
    window.addEventListener('focus', updateOnFocus)
    return () => {
      window.clearTimeout(timeoutId)
      window.removeEventListener('focus', updateOnFocus)
    }
  }, [])

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <div className="brand-badge"><img src="/ecometer.svg" alt="EcoMeter leaf logo" /></div>
          <div>
            <p className="eyebrow">EcoMeter</p>
            <span className="brand-caption">Personal footprint</span>
          </div>
        </div>

        <nav className="nav-links">
          <NavLink to="/" end><NavIcon name="dashboard" />Dashboard</NavLink>
          <NavLink to="/activities"><NavIcon name="activities" />Activities</NavLink>
          <NavLink to="/analytics"><NavIcon name="analytics" />Analytics</NavLink>
          <NavLink to="/goals"><NavIcon name="goals" />Goals</NavLink>
        </nav>

        <div className="sidebar-note">
          <span className="status-dot" />
          <div><strong>Single-user workspace</strong><span>No account needed to track your footprint</span></div>
        </div>
      </aside>

      <main className="main-content">
        <div className="topbar">
          <span className="topbar-page">{pageTitles[location.pathname] || 'EcoMeter'}</span>
          <span className="topbar-date">{todayLabel}</span>
        </div>
        {children}
      </main>
    </div>
  )
}

function DashboardPage() {
  const [summary, setSummary] = useState(null)
  const [breakdown, setBreakdown] = useState([])
  const [trends, setTrends] = useState([])
  const [recommendations, setRecommendations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)
  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const [summaryResponse, breakdownResponse, trendsResponse, recommendationResponse] = await Promise.all([
          api.get('/emissions/summary'),
          api.get('/emissions/breakdown'),
          api.get('/emissions/trends'),
          api.get('/recommendations'),
        ])
        setSummary(summaryResponse.data)
        setBreakdown(breakdownResponse.data)
        setTrends(trendsResponse.data)
        setRecommendations(recommendationResponse.data)
      } catch (err) {
        setError(err.response?.data?.detail || 'Could not load dashboard data. Check that the backend is running.')
      } finally {
        setLoading(false)
      }
    }

    load()
  }, [refreshKey])

  if (loading) {
    return <div className="page-stack"><div className="loading-hero" /><div className="loading-stats"><span /><span /><span /><span /></div><div className="panel loading-panel">Preparing your footprint overview…</div></div>
  }

  if (!summary) {
    return (
      <div className="page-stack">
        <div className="page-header"><div><p className="eyebrow">Overview</p><h2>Your carbon dashboard</h2></div></div>
        <div className="notice error-notice" role="alert">{error || 'Dashboard data is not available.'}</div>
        <button type="button" className="secondary-btn retry-button" onClick={() => setRefreshKey((key) => key + 1)}>Try again</button>
      </div>
    )
  }

  return (
    <div className="page-stack">
      {error && <div className="notice error-notice" role="alert">{error}<button type="button" onClick={() => setRefreshKey((key) => key + 1)}>Retry</button></div>}
      <header className="page-header">
        <div>
          <p className="eyebrow">Overview</p>
          <h2>Your carbon dashboard</h2>
          <p className="page-subtitle">A clearer view of your everyday impact, one small step at a time.</p>
        </div>
        <Link className="primary-btn header-action" to="/activities"><span aria-hidden="true">＋</span> Log an activity</Link>
      </header>

      <section className="stats-grid">
        <StatCard label="Today" value={summary.today_kg_co2e} accent="primary" />
        <StatCard label="This week" value={summary.week_kg_co2e} accent="secondary" />
        <StatCard label="This month" value={summary.month_kg_co2e} accent="accent" />
        <StatCard label="Average / day" value={summary.average_daily_kg_co2e} accent="neutral" />
      </section>

      <section className="content-grid two-columns">
        <div className="panel">
          <div className="panel-header">
            <h3>Category breakdown</h3>
            <span className="panel-caption">Last 30 days · kg CO₂e</span>
          </div>
          {breakdown.length ? <div className="chart-box">
            <ResponsiveContainer width="100%" height={270}>
              <PieChart>
                <Pie data={breakdown} dataKey="total_kg" nameKey="category" innerRadius={45} outerRadius={90} paddingAngle={3}>
                  {breakdown.map((entry, index) => (
                    <Cell key={entry.category} fill={categoryColors[index % categoryColors.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={formatKg} />
              </PieChart>
            </ResponsiveContainer>
          </div> : <div className="chart-empty"><span className="empty-icon">◌</span><strong>No CO₂e activities in this period</strong><span>Log an activity to see its category here.</span></div>}
          <div className="legend-list">
            {breakdown.map((item, index) => (
              <div key={item.category} className="legend-item">
                <span className="dot" style={{ background: categoryColors[index % categoryColors.length] }} />
                <span>{item.category}</span>
                <strong>{formatKg(item.total_kg)}</strong>
              </div>
            ))}
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h3>Goal progress</h3>
            <Link to="/goals" className="text-link">Manage goals <span aria-hidden="true">→</span></Link>
          </div>
          {summary.active_goal ? (
            <div className="goal-card">
              <div className="goal-metric">
                <span>Target</span>
                <strong>{formatKg(summary.active_goal.monthly_target_kg)}</strong>
              </div>
              <div className="goal-progress-bar">
                <span style={{ width: `${Math.min(summary.goal_progress_percent, 100)}%` }} />
              </div>
              <div className="goal-meta">
                <span>{summary.goal_progress_percent.toFixed(1)}% of target used</span>
                <span>{formatKg(summary.goal_remaining_kg)} left</span>
              </div>
            </div>
          ) : (
            <div className="inline-empty"><strong>No monthly goal yet</strong><span>Set a target and keep your progress in view.</span><Link to="/goals" className="text-link">Set a goal <span aria-hidden="true">→</span></Link></div>
          )}

          <div className="recommendation-list">
            <p className="section-kicker">Personalized suggestions</p>
            {recommendations.map((item) => (
              <div key={item.title} className="recommendation-item">
                <span className={`priority ${item.priority.toLowerCase()}`}>{item.priority}</span>
                <div>
                  <strong>{item.title}</strong>
                  <p>{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="content-grid two-columns">
        <div className="panel">
          <div className="panel-header">
            <h3>Daily emissions trend</h3>
            <span className="panel-caption">Last 30 days</span>
          </div>
          {trends.some((point) => point.total_kg_co2e > 0) ? <div className="chart-box">
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={trends}>
                <CartesianGrid strokeDasharray="3 3" stroke="#dfe8e2" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={formatDate} minTickGap={28} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip labelFormatter={formatDate} formatter={formatKg} />
                <Line type="monotone" dataKey="total_kg_co2e" name="kg CO₂e" stroke="#7da68d" strokeWidth={3} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div> : <div className="chart-empty compact"><span className="empty-icon">↗</span><strong>Trend starts with your first log</strong><span>Daily activity totals will build a useful picture over time.</span></div>}
        </div>

        <div className="panel">
          <div className="panel-header">
            <h3>Category comparison</h3>
            <span className="panel-caption">Last 30 days · kg CO₂e</span>
          </div>
          {breakdown.length ? <div className="chart-box">
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={breakdown}>
                <CartesianGrid strokeDasharray="3 3" stroke="#dfe8e2" />
                <XAxis dataKey="category" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip formatter={formatKg} />
                <Bar dataKey="total_kg" radius={[8, 8, 0, 0]}>
                  {breakdown.map((entry, index) => (
                    <Cell key={entry.category} fill={categoryColors[index % categoryColors.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div> : <div className="chart-empty compact"><span className="empty-icon">▥</span><strong>Nothing to compare yet</strong><span>Log a few activities to compare your categories.</span></div>}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Recent activities</h3>
          <Link to="/activities" className="text-link">View activity log <span aria-hidden="true">→</span></Link>
        </div>
        {summary.recent_activities?.length ? <div className="activity-list">
          {summary.recent_activities?.map((activity) => (
            <div key={activity.id} className="activity-row">
              <div>
                <strong>{activity.activity_type}</strong>
                <p>{activity.category} • {activity.quantity} {activity.unit}</p>
              </div>
              <div className="activity-meta">
                <span>{formatDate(activity.activity_date)}</span>
                <strong>{formatKg(activity.calculated_emissions_kg)}</strong>
              </div>
            </div>
          ))}
        </div> : <div className="inline-empty"><strong>Your activity log is ready</strong><span>Start with a commute or household electricity use.</span><Link to="/activities" className="text-link">Add your first activity <span aria-hidden="true">→</span></Link></div>}
      </section>
    </div>
  )
}

function ActivitiesPage() {
  const [factors, setFactors] = useState([])
  const [activities, setActivities] = useState([])
  const [editingId, setEditingId] = useState(null)
  const [notice, setNotice] = useState(null)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({
    category: '',
    activity_type: '',
    quantity: 1,
    unit: '',
    activity_date: toLocalDateInput(),
    notes: '',
  })
  const categories = [...new Set(factors.map((factor) => factor.category))]
  const categoryFactors = factors.filter((factor) => factor.category === form.category)
  const selectedFactor = categoryFactors.find((factor) => factor.activity_type === form.activity_type)

  const loadData = async () => {
    try {
      const [factorResponse, activityResponse] = await Promise.all([
        api.get('/emission-factors'),
        api.get('/activities'),
      ])
      setFactors(factorResponse.data)
      setActivities(activityResponse.data)
      return true
    } catch (err) {
      setNotice({ type: 'error', text: err.response?.data?.detail || 'Could not load activities. Check that the backend is running.' })
      return false
    }
  }

  useEffect(() => {
    let active = true
    const loadInitialData = async () => {
      try {
        const [factorResponse, activityResponse] = await Promise.all([
          api.get('/emission-factors'),
          api.get('/activities'),
        ])
        if (active) {
          setFactors(factorResponse.data)
          setActivities(activityResponse.data)
          const firstFactor = factorResponse.data[0]
          if (firstFactor) {
            setForm((current) => {
              const selected = factorResponse.data.find((factor) =>
                factor.category === current.category && factor.activity_type === current.activity_type,
              ) || firstFactor
              return {
                ...current,
                category: selected.category,
                activity_type: selected.activity_type,
                unit: selected.unit,
              }
            })
          }
        }
      } catch (err) {
        if (active) {
          setNotice({ type: 'error', text: err.response?.data?.detail || 'Could not load activities. Check that the backend is running.' })
        }
      }
    }

    loadInitialData()
    return () => {
      active = false
    }
  }, [])

  const handleCategoryChange = (categoryName) => {
    const firstFactor = factors.find((factor) => factor.category === categoryName && factor.available)
      || factors.find((factor) => factor.category === categoryName)
    setForm((current) => ({
      ...current,
      category: categoryName,
      activity_type: firstFactor?.activity_type || '',
      unit: firstFactor?.unit || '',
    }))
  }

  const handleActivityTypeChange = (activityType) => {
    const factor = categoryFactors.find((item) => item.activity_type === activityType)
    setForm((current) => ({ ...current, activity_type: activityType, unit: factor?.unit || '' }))
  }

  const handleChange = (event) => {
    const { name, value } = event.target
    setForm((current) => ({ ...current, [name]: value }))
  }

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setNotice(null)
    const payload = {
      ...form,
      quantity: Number(form.quantity),
    }

    try {
      if (editingId) {
        await api.put(`/activities/${editingId}`, payload)
      } else {
        await api.post('/activities', payload)
      }
      const firstFactor = factors[0]
      setForm({
        category: firstFactor?.category || '',
        activity_type: firstFactor?.activity_type || '',
        quantity: 1,
        unit: firstFactor?.unit || '',
        activity_date: toLocalDateInput(),
        notes: '',
      })
      setEditingId(null)
      if (await loadData()) {
        setNotice({ type: 'success', text: 'Activity saved and emissions recalculated.' })
      } else {
        setNotice({ type: 'error', text: 'Activity saved, but the activity list could not be refreshed.' })
      }
    } catch (err) {
      setNotice({ type: 'error', text: err.response?.data?.detail || 'Could not save this activity. Please check the values and try again.' })
    } finally {
      setSaving(false)
    }
  }

  const handleEdit = (activity) => {
    const factor = factors.find((item) =>
      item.category === activity.category && item.activity_type === activity.activity_type,
    )
    setEditingId(activity.id)
    setForm({
      category: activity.category,
      activity_type: activity.activity_type,
      quantity: activity.quantity,
      unit: factor?.unit || activity.unit,
      activity_date: activity.activity_date,
      notes: activity.notes || '',
    })
  }

  const handleDelete = async (activityId) => {
    if (!window.confirm('Delete this activity? Its emissions will be removed from your dashboard.')) return
    setNotice(null)
    try {
      await api.delete(`/activities/${activityId}`)
      if (await loadData()) {
        setNotice({ type: 'success', text: 'Activity deleted.' })
      } else {
        setNotice({ type: 'error', text: 'Activity deleted, but the activity list could not be refreshed.' })
      }
    } catch (err) {
      setNotice({ type: 'error', text: err.response?.data?.detail || 'Could not delete this activity. Please try again.' })
    }
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Logbook</p>
          <h2>Track your activities</h2>
          <p className="page-subtitle">Record everyday choices and see their estimated carbon impact.</p>
        </div>
      </header>

      {notice && <div className={`notice ${notice.type === 'error' ? 'error-notice' : 'success-notice'}`} role={notice.type === 'error' ? 'alert' : 'status'}>{notice.text}</div>}

      <section className="panel">
        <div className="panel-header">
          <h3>{editingId ? 'Update activity' : 'Add new activity'}</h3>
          <span className="panel-caption">All fields marked by the form are required</span>
        </div>
        <div className="factor-note"><span className="note-icon" aria-hidden="true">i</span><span><strong>About these estimates</strong> All available factors and calculated totals are reported in kg CO₂e. Published estimates and illustrative assumptions are labeled with their source and methodology.</span></div>
        <form className="activity-form" onSubmit={handleSubmit}>
          <div className="form-grid">
            <label>
              Category
              <select name="category" value={form.category} onChange={(event) => handleCategoryChange(event.target.value)} required>
                {categories.map((category) => (
                  <option key={category} value={category}>{category}</option>
                ))}
              </select>
            </label>

            <label>
              Activity type
              <select name="activity_type" value={form.activity_type} onChange={(event) => handleActivityTypeChange(event.target.value)} required>
                {categoryFactors.map((factor) => (
                  <option key={factor.activity_type} value={factor.activity_type} disabled={!factor.available}>
                    {factor.activity_type}{factor.available ? '' : ' — unavailable'}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Quantity
              <input type="number" min="0.1" step="0.1" name="quantity" value={form.quantity} onChange={handleChange} required />
            </label>

            <label>
              Unit
              <input name="unit" value={selectedFactor?.unit || form.unit} readOnly required />
            </label>

            <label>
              Date
              <input type="date" name="activity_date" value={form.activity_date} onChange={handleChange} required />
            </label>
          </div>

          {categoryFactors.some((factor) => !factor.available) && <div className="factor-unavailable-list">
            <strong>Unavailable without a suitable factor</strong>
            <ul>
              {categoryFactors.filter((factor) => !factor.available).map((factor) => (
                <li key={factor.activity_type}><span>{factor.activity_type}</span> — {factor.notes}</li>
              ))}
            </ul>
          </div>}

          {selectedFactor && <div className="factor-details">
            <div className="factor-details-heading">
              <strong>{selectedFactor.available ? selectedFactor.verification_status : 'Unavailable'}</strong>
              <span>{selectedFactor.available
                ? `${selectedFactor.emission_factor} kg ${selectedFactor.gas_basis} / ${selectedFactor.unit}`
                : `No factor available per ${selectedFactor.unit}`}</span>
            </div>
            <p>{selectedFactor.notes}</p>
            <div className="factor-details-meta">
              {selectedFactor.geography && <span>{selectedFactor.geography}</span>}
              {selectedFactor.available && <span>{selectedFactor.reference_year ? `Reference year ${selectedFactor.reference_year}` : 'Reference year not specified'}</span>}
              <span>{selectedFactor.methodology}</span>
            </div>
            <span className="factor-source">
              {selectedFactor.available ? `Source: ${selectedFactor.source}` : selectedFactor.source}
              {selectedFactor.source_url && <> · <a href={selectedFactor.source_url} target="_blank" rel="noreferrer">Open reference</a></>}
            </span>
          </div>}

          <label>
            Notes
            <textarea name="notes" value={form.notes} onChange={handleChange} rows="3" placeholder="Optional notes" />
          </label>

          <div className="form-actions">
            <button type="submit" className="primary-btn" disabled={saving || !selectedFactor?.available}>{saving ? 'Saving…' : editingId ? 'Save changes' : 'Add activity'}</button>
            {editingId && (
              <button type="button" className="secondary-btn" onClick={() => {
                setEditingId(null)
                setForm({
                  category: factors[0]?.category || '',
                  activity_type: factors[0]?.activity_type || '',
                  quantity: 1,
                  unit: factors[0]?.unit || '',
                  activity_date: toLocalDateInput(),
                  notes: '',
                })
              }}>
                Cancel
              </button>
            )}
          </div>
        </form>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Recent entries</h3>
        </div>
        {activities.length ? <div className="activity-list">
          {activities.map((activity) => (
            <div key={activity.id} className="activity-row">
              <div>
                <strong>{activity.activity_type}</strong>
                <p>{activity.category} • {activity.quantity} {activity.unit}</p>
              </div>
              <div className="activity-meta">
                <span>{formatDate(activity.activity_date)}</span>
                <strong>{formatKg(activity.calculated_emissions_kg)}</strong>
                {!factors.some((factor) => factor.category === activity.category && factor.activity_type === activity.activity_type) && <span className="pill inactive">Historical factor unavailable</span>}
                <div className="mini-actions">
                  {factors.some((factor) => factor.category === activity.category && factor.activity_type === activity.activity_type) && <button type="button" onClick={() => handleEdit(activity)}>Edit</button>}
                  <button type="button" className="danger" onClick={() => handleDelete(activity.id)}>Delete</button>
                </div>
              </div>
            </div>
          ))}
        </div> : <div className="inline-empty"><strong>No activities logged yet</strong><span>Your entries will be calculated and reported in kg CO₂e.</span></div>}
      </section>
    </div>
  )
}

function GoalsPage() {
  const [goals, setGoals] = useState([])
  const [summary, setSummary] = useState(null)
  const [notice, setNotice] = useState(null)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ monthly_target_kg: 40, start_month: toLocalDateInput().slice(0, 7) })

  const loadGoals = async () => {
    try {
      const [goalsResponse, summaryResponse] = await Promise.all([
        api.get('/goals'),
        api.get('/emissions/summary'),
      ])
      setGoals(goalsResponse.data)
      setSummary(summaryResponse.data)
      return true
    } catch (err) {
      setNotice({ type: 'error', text: err.response?.data?.detail || 'Could not load goal information.' })
      return false
    }
  }

  useEffect(() => {
    let active = true
    const loadInitialGoals = async () => {
      try {
        const [goalsResponse, summaryResponse] = await Promise.all([
          api.get('/goals'),
          api.get('/emissions/summary'),
        ])
        if (active) {
          setGoals(goalsResponse.data)
          setSummary(summaryResponse.data)
        }
      } catch (err) {
        if (active) {
          setNotice({ type: 'error', text: err.response?.data?.detail || 'Could not load goal information.' })
        }
      }
    }

    loadInitialGoals()
    return () => {
      active = false
    }
  }, [])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setSaving(true)
    setNotice(null)
    try {
      await api.post('/goals', { ...form, monthly_target_kg: Number(form.monthly_target_kg) })
      setForm({ monthly_target_kg: 40, start_month: toLocalDateInput().slice(0, 7) })
      if (await loadGoals()) {
        setNotice({ type: 'success', text: 'Your monthly goal has been saved.' })
      } else {
        setNotice({ type: 'error', text: 'Goal saved, but the goal list could not be refreshed.' })
      }
    } catch (err) {
      setNotice({ type: 'error', text: err.response?.data?.detail || 'Could not save your goal. Please try again.' })
    } finally {
      setSaving(false)
    }
  }

  const handleDelete = async (goalId) => {
    if (!window.confirm('Delete this carbon goal?')) return
    setNotice(null)
    try {
      await api.delete(`/goals/${goalId}`)
      if (await loadGoals()) {
        setNotice({ type: 'success', text: 'Goal deleted.' })
      } else {
        setNotice({ type: 'error', text: 'Goal deleted, but the goal list could not be refreshed.' })
      }
    } catch (err) {
      setNotice({ type: 'error', text: err.response?.data?.detail || 'Could not delete this goal.' })
    }
  }

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Goals</p>
          <h2>Make a little progress</h2>
          <p className="page-subtitle">Set a monthly footprint target and keep your progress visible.</p>
        </div>
      </header>

      {notice && <div className={`notice ${notice.type === 'error' ? 'error-notice' : 'success-notice'}`} role={notice.type === 'error' ? 'alert' : 'status'}>{notice.text}</div>}

      {summary?.active_goal && (
        <section className="goal-spotlight">
          <div className="goal-spotlight-copy">
            <span className="eyebrow">Current month</span>
            <h3>{summary.goal_progress_percent.toFixed(1)}% of your target used</h3>
            <p>{formatKg(summary.month_kg_co2e)} this month · {formatKg(summary.goal_remaining_kg)} remaining</p>
          </div>
          <div className="goal-spotlight-bar" role="progressbar" aria-valuenow={Math.min(summary.goal_progress_percent, 100)} aria-valuemin="0" aria-valuemax="100">
            <span style={{ width: `${Math.min(summary.goal_progress_percent, 100)}%` }} />
          </div>
        </section>
      )}

      <section className="panel">
        <div className="panel-header">
          <h3>Set a monthly goal</h3>
          <span className="panel-caption">Choose a target that feels achievable</span>
        </div>
        <form className="goal-form" onSubmit={handleSubmit}>
          <label>
            Monthly target (kg CO₂e)
            <input type="number" min="1" step="1" value={form.monthly_target_kg} onChange={(event) => setForm({ ...form, monthly_target_kg: event.target.value })} required />
          </label>

          <label>
            Start month
            <input type="month" value={form.start_month} onChange={(event) => setForm({ ...form, start_month: event.target.value })} required />
          </label>

          <button type="submit" className="primary-btn" disabled={saving}>{saving ? 'Saving…' : 'Save goal'}</button>
        </form>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h3>Saved goals</h3>
        </div>
        {goals.length ? <div className="goal-list">
          {goals.map((goal) => (
            <div key={goal.id} className="goal-row">
              <div>
                <strong>{formatKg(goal.monthly_target_kg)}</strong>
                <p>Starting {goal.start_month.slice(5, 7)}-{goal.start_month.slice(0, 4)}</p>
              </div>
              <div className="goal-row-actions">
                <span className={`pill ${goal.is_active ? 'active' : 'inactive'}`}>{goal.is_active ? 'Active' : 'Previous'}</span>
                <button type="button" className="icon-button danger" aria-label="Delete goal" onClick={() => handleDelete(goal.id)}>×</button>
              </div>
            </div>
          ))}
        </div> : <div className="inline-empty"><strong>No goals yet</strong><span>Your saved monthly targets will appear here.</span></div>}
      </section>
    </div>
  )
}

function AnalyticsPage() {
  const [breakdown, setBreakdown] = useState([])
  const [trends, setTrends] = useState([])
  const [startDate, setStartDate] = useState(() => {
    const date = new Date()
    date.setDate(date.getDate() - 29)
    return toLocalDateInput(date)
  })
  const [endDate, setEndDate] = useState(() => toLocalDateInput())
  const [categoryFilter, setCategoryFilter] = useState('All categories')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [refreshKey, setRefreshKey] = useState(0)

  useEffect(() => {
    const load = async () => {
      setLoading(true)
      setError('')
      try {
        const [breakdownResponse, trendsResponse] = await Promise.all([
          api.get('/emissions/breakdown', { params: { start_date: startDate, end_date: endDate } }),
          api.get('/emissions/trends', {
            params: {
              start_date: startDate,
              end_date: endDate,
              category: categoryFilter === 'All categories' ? undefined : categoryFilter,
            },
          }),
        ])
        setBreakdown(breakdownResponse.data)
        setTrends(trendsResponse.data)
      } catch (err) {
        setError(err.response?.data?.detail || 'Could not load analytics. Check that the backend is running.')
      } finally {
        setLoading(false)
      }
    }
    load()
  }, [startDate, endDate, categoryFilter, refreshKey])

  const categories = [...new Set(breakdown.map((item) => item.category))]
  const visibleBreakdown = breakdown.filter((item) =>
    categoryFilter === 'All categories' || item.category === categoryFilter,
  )

  const totalEmissions = visibleBreakdown.reduce((total, item) => total + Number(item.total_kg || 0), 0)
  const hasTrend = trends.some((point) => point.total_kg_co2e > 0)

  return (
    <div className="page-stack">
      <header className="page-header">
        <div>
          <p className="eyebrow">Reports</p>
          <h2>Understand your footprint</h2>
          <p className="page-subtitle">Explore published and illustrative estimates, all reported in kg CO₂e.</p>
        </div>
      </header>

      <section className="filter-toolbar">
        <div className="filter-heading"><span className="filter-icon" aria-hidden="true">⌕</span><div><strong>Explore your emissions</strong><span>Date range and category apply to both charts</span></div></div>
        <label>From<input type="date" value={startDate} max={endDate} onChange={(event) => setStartDate(event.target.value)} /></label>
        <label>To<input type="date" value={endDate} min={startDate} onChange={(event) => setEndDate(event.target.value)} /></label>
        <label>Category<select value={categoryFilter} onChange={(event) => setCategoryFilter(event.target.value)}><option>All categories</option>{categories.map((category) => <option key={category}>{category}</option>)}</select></label>
      </section>

      {error && <div className="notice error-notice" role="alert">{error}<button type="button" onClick={() => setRefreshKey((key) => key + 1)}>Retry</button></div>}

      <div className="analytics-summary">
        <div><span>Selected period</span><strong>{formatDate(startDate)} — {formatDate(endDate)}</strong></div>
        <div><span>{`${categoryFilter === 'All categories' ? 'Total' : categoryFilter} · CO₂e`}</span><strong>{formatKg(totalEmissions)}</strong></div>
        <div><span>Categories contributing</span><strong>{visibleBreakdown.length}</strong></div>
      </div>

      <section className="panel">
        <div className="panel-header">
          <div><h3>Emissions by category</h3><span className="panel-caption">kg CO₂e · selected period</span></div>
        </div>
        {loading ? <div className="chart-empty"><span className="spinner" /><strong>Updating analytics…</strong></div> : visibleBreakdown.length ? <div className="chart-box">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={visibleBreakdown}>
              <CartesianGrid strokeDasharray="3 3" stroke="#dfe8e2" />
              <XAxis dataKey="category" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip formatter={formatKg} />
              <Bar dataKey="total_kg" radius={[8, 8, 0, 0]}>
                {visibleBreakdown.map((item, index) => (
                  <Cell key={item.category} fill={categoryColors[index % categoryColors.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div> : <div className="chart-empty"><span className="empty-icon">▥</span><strong>No emissions in this period</strong><span>Try a wider date range or log an activity.</span></div>}
      </section>

      <section className="panel">
        <div className="panel-header">
          <div><h3>Daily trend</h3><span className="panel-caption">kg CO₂e · selected period</span></div>
        </div>
        {loading ? <div className="chart-empty"><span className="spinner" /><strong>Updating analytics…</strong></div> : hasTrend ? <div className="chart-box">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="#dfe8e2" />
              <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={formatDate} minTickGap={28} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip labelFormatter={formatDate} formatter={formatKg} />
              <Line type="monotone" dataKey="total_kg_co2e" name="kg CO₂e" stroke="#7da68d" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div> : <div className="chart-empty"><span className="empty-icon">↗</span><strong>No daily activity to show</strong><span>Your footprint trend will appear when activities are logged.</span></div>}
      </section>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout><DashboardPage /></Layout>} />
        <Route path="/activities" element={<Layout><ActivitiesPage /></Layout>} />
        <Route path="/analytics" element={<Layout><AnalyticsPage /></Layout>} />
        <Route path="/goals" element={<Layout><GoalsPage /></Layout>} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
