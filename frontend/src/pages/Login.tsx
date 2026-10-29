import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getErrorMessage } from '../services/api'
import './Login.css'

function Login() {
  const navigate = useNavigate()
  const { login, sessionExpired } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    if (!email || !password) {
      setError('Preencha todos os campos.')
      return
    }

    setLoading(true)

    try {
      await login(email, password)
      navigate('/dashboard')
    } catch (err) {
      setError(getErrorMessage(err, 'Não foi possível entrar. Tente novamente.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="login-page">
      <section className="login-hero">
        <div className="login-brand">
          <span className="login-brand-badge">LOCKY</span>

          <h1>
            Seu armário.
            <br />
            Sua rotina.
            <br />
            <span>Sem complicação.</span>
          </h1>

          <p>
            Reserve armários da academia de forma rápida, segura e organizada.
          </p>
        </div>

        <div className="login-decoration">
          <div className="locker locker-one">
            <span>01</span>
          </div>

          <div className="locker locker-two">
            <span>02</span>
          </div>

          <div className="locker locker-three">
            <span>03</span>
          </div>
        </div>
      </section>

      <section className="login-form-area">
        <div className="login-form-container">
          <div className="login-heading">
            <span>Acesso ao sistema</span>
            <h2>Bem-vindo de volta</h2>
            <p>Entre com seus dados para acessar o Locky.</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="form-group">
              <label htmlFor="email">E-mail</label>

              <input
                id="email"
                type="email"
                placeholder="seuemail@exemplo.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>

            <div className="form-group">
              <div className="password-label">
                <label htmlFor="password">Senha</label>
              </div>

              <div className="password-input-wrapper">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Digite sua senha"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />

                <button
                  type="button"
                  className="password-toggle"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? 'Ocultar' : 'Mostrar'}
                </button>
              </div>
            </div>

            {sessionExpired && !error && (
              <p className="login-error">
                Sua sessão expirou. Entre novamente para continuar.
              </p>
            )}

            {error && (
              <p className="login-error">
                {error}
              </p>
            )}

            <button
              className="login-button"
              type="submit"
              disabled={loading}
            >
              {loading ? 'Entrando...' : 'Entrar'}
            </button>
          </form>

          <div className="login-register-link">
            <span>Ainda não possui uma conta?</span>

            <button
              type="button"
              onClick={() => navigate('/register')}
            >
              Criar conta
            </button>
          </div>

          <p className="login-footer">
            © 2026 Locky
          </p>
        </div>
      </section>
    </main>
  )
}

export default Login