import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getErrorMessage } from '../services/api'
import { getLockers, getLockerStats } from '../services/lockerService'
import type { Locker, LockerStats } from '../types/locker'
import { lockerSizeLabel, lockerStatusLabel } from '../utils/labels'
import './Dashboard.css'

function Dashboard() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const [lockers, setLockers] = useState<Locker[]>([])
  const [stats, setStats] = useState<LockerStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    Promise.all([getLockers({ limit: 8 }), getLockerStats()])
      .then(([lockersResponse, statsResponse]) => {
        setLockers(lockersResponse.items)
        setStats(statsResponse)
        setError('')
      })
      .catch((err) => {
        setError(getErrorMessage(err, 'Não foi possível carregar o dashboard.'))
      })
      .finally(() => setLoading(false))
  }, [])

  const iniciais = user?.name.slice(0, 2).toUpperCase() ?? ''

  return (
    <section className="dashboard-content">
      <header className="dashboard-header">
        <div>
          <span className="dashboard-label">VISÃO GERAL</span>
          <h1>Dashboard</h1>
          <p>Acompanhe a situação dos armários em tempo real.</p>
        </div>

        <div className="dashboard-user">
          <div className="user-avatar">{iniciais}</div>

          <div>
            <strong>{user?.name}</strong>
            <span>{user?.role === 'admin' ? 'Administrador' : 'Usuário'}</span>
          </div>
        </div>
      </header>

      {error && <p className="api-error">{error}</p>}

      <section className="stats-grid">
        <article className="stat-card">
          <span>Total de armários</span>
          <strong>{stats?.total ?? '—'}</strong>
          <small>
            {stats ? `${stats.maintenance} em manutenção` : 'Todos os armários'}
          </small>
        </article>

        <article className="stat-card stat-highlight">
          <span>Disponíveis</span>
          <strong>{stats?.available ?? '—'}</strong>
          <small>Prontos para reserva</small>
        </article>

        <article className="stat-card">
          <span>Reservados</span>
          <strong>{stats?.reserved ?? '—'}</strong>
          <small>Aguardando utilização</small>
        </article>

        <article className="stat-card">
          <span>Ocupados</span>
          <strong>{stats?.occupied ?? '—'}</strong>
          <small>Em utilização agora</small>
        </article>
      </section>

      <section className="lockers-section">
        <div className="section-header">
          <div>
            <h2>Armários</h2>
            <p>Visualize rapidamente a disponibilidade.</p>
          </div>

          <button
            className="view-all-button"
            type="button"
            onClick={() => navigate('/lockers')}
          >
            Ver todos
          </button>
        </div>

        <div className="status-legend">
          <span>
            <i className="status-dot available-dot" />
            Disponível
          </span>

          <span>
            <i className="status-dot reserved-dot" />
            Reservado
          </span>

          <span>
            <i className="status-dot occupied-dot" />
            Ocupado
          </span>
        </div>

        {loading ? (
          <p>Carregando armários...</p>
        ) : (
          <div className="lockers-grid">
            {lockers.map((locker) => (
              <button key={locker.id} className={`locker-card ${locker.status}`}>
                <div className="locker-top">
                  <span>ARMÁRIO</span>
                  <i />
                </div>

                <strong>{locker.number}</strong>

                <div className="locker-info">
                  <span className="locker-size">{lockerSizeLabel(locker.size)}</span>

                  <span className="locker-status">
                    {lockerStatusLabel(locker.status)}
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </section>
    </section>
  )
}

export default Dashboard
