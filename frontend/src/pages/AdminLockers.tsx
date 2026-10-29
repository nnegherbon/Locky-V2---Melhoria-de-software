import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import Pagination from '../components/Pagination'
import { getErrorMessage } from '../services/api'
import {
  createLocker,
  deleteLocker as deleteLockerRequest,
  getLockers,
  getLockerStats,
  updateLocker,
} from '../services/lockerService'
import type {
  Locker,
  LockerAdminStatus,
  LockerSize,
  LockerStats,
} from '../types/locker'
import { lockerSizeLabel, lockerStatusLabel } from '../utils/labels'
import './AdminLockers.css'

const TAMANHO_PAGINA = 20

/** Armários reservados/ocupados têm o status controlado pelas reservas. */
function statusControladoPorReserva(locker: Locker): boolean {
  return locker.status === 'reserved' || locker.status === 'occupied'
}

function AdminLockers() {
  const [lockers, setLockers] = useState<Locker[]>([])
  const [stats, setStats] = useState<LockerStats | null>(null)
  const [total, setTotal] = useState(0)
  const [offset, setOffset] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [busyId, setBusyId] = useState<number | null>(null)

  const [selectedLocker, setSelectedLocker] = useState<Locker | null>(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [saving, setSaving] = useState(false)
  const [formError, setFormError] = useState('')

  const [number, setNumber] = useState('')
  const [size, setSize] = useState<LockerSize>('small')
  const [status, setStatus] = useState<LockerAdminStatus>('available')

  // Incrementar `versao` força uma nova busca após criar/editar/excluir.
  const [versao, setVersao] = useState(0)
  const recarregar = () => setVersao((atual) => atual + 1)

  useEffect(() => {
    Promise.all([
      getLockers({ limit: TAMANHO_PAGINA, offset }),
      getLockerStats(),
    ])
      .then(([lista, resumo]) => {
        setLockers(lista.items)
        setTotal(lista.total)
        setStats(resumo)
        setError('')
      })
      .catch((err) => {
        setError(getErrorMessage(err, 'Não foi possível carregar os armários.'))
      })
      .finally(() => setLoading(false))
  }, [offset, versao])

  function irParaPagina(novoOffset: number) {
    setLoading(true)
    setOffset(novoOffset)
  }

  function openCreateModal() {
    setSelectedLocker(null)
    setIsCreating(true)
    setNumber('')
    setSize('small')
    setStatus('available')
    setFormError('')
    setModalOpen(true)
  }

  function openEditModal(locker: Locker) {
    setSelectedLocker(locker)
    setIsCreating(false)
    setNumber(locker.number)
    setSize(locker.size)
    setStatus(locker.status === 'maintenance' ? 'maintenance' : 'available')
    setFormError('')
    setModalOpen(true)
  }

  function closeModal() {
    if (saving) return
    setModalOpen(false)
    setSelectedLocker(null)
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!number.trim()) {
      setFormError('Informe o número do armário.')
      return
    }

    setSaving(true)
    setFormError('')

    try {
      if (isCreating) {
        await createLocker({ number: number.trim(), size, status })
      } else if (selectedLocker) {
        await updateLocker(selectedLocker.id, {
          number: number.trim(),
          size,
          // Só envia status quando o admin pode alterá-lo.
          ...(statusControladoPorReserva(selectedLocker) ? {} : { status }),
        })
      }
      setModalOpen(false)
      setSelectedLocker(null)
      recarregar()
    } catch (err) {
      setFormError(getErrorMessage(err, 'Não foi possível salvar o armário.'))
    } finally {
      setSaving(false)
    }
  }

  async function toggleMaintenance(locker: Locker) {
    setBusyId(locker.id)
    try {
      await updateLocker(locker.id, {
        status: locker.status === 'maintenance' ? 'available' : 'maintenance',
      })
      recarregar()
    } catch (err) {
      setError(getErrorMessage(err, 'Não foi possível alterar o status do armário.'))
    } finally {
      setBusyId(null)
    }
  }

  async function deleteLocker(locker: Locker) {
    const confirmed = window.confirm(
      `Deseja excluir o armário #${locker.number}?`,
    )

    if (!confirmed) return

    setBusyId(locker.id)
    try {
      await deleteLockerRequest(locker.id)
      // Se a página ficou vazia, volta uma página.
      const novoOffset =
        lockers.length === 1 && offset > 0 ? offset - TAMANHO_PAGINA : offset
      if (novoOffset !== offset) {
        setOffset(novoOffset)
      } else {
        recarregar()
      }
    } catch (err) {
      setError(getErrorMessage(err, 'Não foi possível excluir o armário.'))
    } finally {
      setBusyId(null)
    }
  }

  return (
    <>
      <section className="admin-lockers-page">
        <header className="admin-lockers-header">
          <div>
            <span className="page-label">ADMINISTRAÇÃO</span>
            <h1>Gerenciar armários</h1>
            <p>
              Cadastre, edite e controle a disponibilidade dos armários.
            </p>
          </div>

          <button
            type="button"
            className="new-locker-button"
            onClick={openCreateModal}
          >
            + Novo armário
          </button>
        </header>

        <section className="admin-summary-grid">
          <article>
            <span>Total</span>
            <strong>{stats?.total ?? '—'}</strong>
          </article>

          <article>
            <span>Disponíveis</span>
            <strong>{stats?.available ?? '—'}</strong>
          </article>

          <article>
            <span>Reservados</span>
            <strong>{stats?.reserved ?? '—'}</strong>
          </article>

          <article>
            <span>Manutenção</span>
            <strong>{stats?.maintenance ?? '—'}</strong>
          </article>
        </section>

        {error && <p className="api-error">{error}</p>}

        <section className="admin-lockers-section">
          <div className="admin-section-header">
            <div>
              <h2>Todos os armários</h2>
              <p>Gerencie os armários cadastrados no sistema.</p>
            </div>
          </div>

          <div className="admin-table-wrapper">
            <table className="admin-lockers-table">
              <thead>
                <tr>
                  <th>Armário</th>
                  <th>Tamanho</th>
                  <th>Status</th>
                  <th>Ações</th>
                </tr>
              </thead>

              <tbody>
                {!loading && lockers.length === 0 && (
                  <tr>
                    <td colSpan={4}>
                      Nenhum armário cadastrado. Use “+ Novo armário” para começar.
                    </td>
                  </tr>
                )}

                {lockers.map((locker) => (
                  <tr key={locker.id}>
                    <td>
                      <strong>#{locker.number}</strong>
                    </td>

                    <td>{lockerSizeLabel(locker.size)}</td>

                    <td>
                      <span
                        className={`admin-status ${locker.status}`}
                      >
                        {lockerStatusLabel(locker.status)}
                      </span>
                    </td>

                    <td>
                      <div className="admin-actions">
                        <button
                          type="button"
                          className="admin-edit-button"
                          onClick={() => openEditModal(locker)}
                        >
                          Editar
                        </button>

                        <button
                          type="button"
                          className={
                            locker.status === 'maintenance'
                              ? 'admin-maintenance-button active'
                              : 'admin-maintenance-button'
                          }
                          onClick={() => toggleMaintenance(locker)}
                          disabled={
                            busyId === locker.id ||
                            statusControladoPorReserva(locker)
                          }
                          title={
                            statusControladoPorReserva(locker)
                              ? 'Armário com reserva ativa'
                              : undefined
                          }
                        >
                          {locker.status === 'maintenance'
                            ? 'Retirar manutenção'
                            : 'Manutenção'}
                        </button>

                        <button
                          type="button"
                          className="admin-delete-button"
                          onClick={() => deleteLocker(locker)}
                          disabled={busyId === locker.id}
                        >
                          Excluir
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <Pagination
            total={total}
            limit={TAMANHO_PAGINA}
            offset={offset}
            onChangeOffset={irParaPagina}
          />
        </section>
      </section>

      {modalOpen && (
        <div className="admin-modal-overlay" onClick={closeModal}>
          <div
            className="admin-modal"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="admin-modal-header">
              <div>
                <span className="page-label">
                  {isCreating ? 'NOVO ARMÁRIO' : 'EDITAR ARMÁRIO'}
                </span>

                <h2>
                  {isCreating
                    ? 'Cadastrar armário'
                    : `Armário #${selectedLocker?.number}`}
                </h2>
              </div>

              <button
                type="button"
                className="admin-modal-close"
                onClick={closeModal}
              >
                ×
              </button>
            </div>

            <form
              className="admin-locker-form"
              onSubmit={handleSubmit}
            >
              <div className="admin-form-group">
                <label htmlFor="locker-number">Número</label>

                <input
                  id="locker-number"
                  type="text"
                  maxLength={10}
                  placeholder="Ex: 15"
                  value={number}
                  onChange={(event) =>
                    setNumber(event.target.value)
                  }
                />
              </div>

              <div className="admin-form-group">
                <label htmlFor="locker-size">Tamanho</label>

                <select
                  id="locker-size"
                  value={size}
                  onChange={(event) =>
                    setSize(event.target.value as LockerSize)
                  }
                >
                  <option value="small">Pequeno</option>
                  <option value="medium">Médio</option>
                  <option value="large">Grande</option>
                </select>
              </div>

              <div className="admin-form-group">
                <label htmlFor="locker-status">Status</label>

                <select
                  id="locker-status"
                  value={status}
                  disabled={
                    selectedLocker !== null &&
                    statusControladoPorReserva(selectedLocker)
                  }
                  onChange={(event) =>
                    setStatus(event.target.value as LockerAdminStatus)
                  }
                >
                  <option value="available">Disponível</option>
                  <option value="maintenance">Manutenção</option>
                </select>

                {selectedLocker && statusControladoPorReserva(selectedLocker) && (
                  <small>
                    Status atual: {lockerStatusLabel(selectedLocker.status)}. Ele
                    é controlado pela reserva ativa.
                  </small>
                )}
              </div>

              {formError && <p className="api-error">{formError}</p>}

              <div className="admin-modal-actions">
                <button
                  type="button"
                  className="admin-cancel-button"
                  onClick={closeModal}
                >
                  Cancelar
                </button>

                <button
                  type="submit"
                  className="admin-save-button"
                  disabled={saving}
                >
                  {saving
                    ? 'Salvando...'
                    : isCreating
                    ? 'Cadastrar armário'
                    : 'Salvar alterações'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </>
  )
}

export default AdminLockers