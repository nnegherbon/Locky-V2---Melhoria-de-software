import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { getErrorMessage } from '../services/api'
import './Register.css'

function Register() {
  const navigate = useNavigate()
  const { register } = useAuth()

  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError('')

    if (!name || !email || !password || !confirmPassword) {
      setError('Preencha todos os campos.')
      return
    }

    if (name.trim().length < 2) {
      setError('Informe seu nome (mínimo de 2 caracteres).')
      return
    }

    // Mesmos limites do backend (o bcrypt considera no máximo 72 caracteres).
    if (password.length < 6 || password.length > 72) {
      setError('A senha deve ter entre 6 e 72 caracteres.')
      return
    }

    if (password !== confirmPassword) {
      setError('As senhas não coincidem.')
      return
    }

    setLoading(true)

    try {
      await register(name.trim(), email.trim(), password)
      navigate('/dashboard')
    } catch (err) {
      setError(getErrorMessage(err, 'Não foi possível criar sua conta. Tente novamente.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="register-page">
      <section className="register-hero">
        <div className="register-brand">
          <span className="register-brand-badge">LOCKY</span>

          <h1>
            Comece agora.
            <br />
            Reserve melhor.
            <br />
            <span>Treine tranquilo.</span>
          </h1>

          <p>
            Crie sua conta e tenha acesso rápido aos armários disponíveis da academia.
          </p>
        </div>

        <div className="register-decoration">
          <div className="register-locker locker-small">
            <span>P</span>
          </div>

          <div className="register-locker locker-medium">
            <span>M</span>
          </div>

          <div className="register-locker locker-large">
            <span>G</span>
          </div>
        </div>
      </section>

      <section className="register-form-area">
        <div className="register-form-container">
          <div className="register-heading">
            <span>NOVA CONTA</span>
            <h2>Crie sua conta</h2>
            <p>Preencha seus dados para começar a usar o Locky.</p>
          </div>

          <form className="register-form" onSubmit={handleSubmit}>
            <div className="register-group">
              <label htmlFor="name">Nome</label>

              <input
                id="name"
                type="text"
                placeholder="Seu nome"
                value={name}
                onChange={(event) => setName(event.target.value)}
              />
            </div>

            <div className="register-group">
              <label htmlFor="email">E-mail</label>

              <input
                id="email"
                type="email"
                placeholder="seuemail@exemplo.com"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
              />
            </div>

            <div className="register-group">
              <label htmlFor="password">Senha</label>

              <div className="register-password-wrapper">
                <input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Crie uma senha"
                  value={password}
                  onChange={(event) => setPassword(event.target.value)}
                />

                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                >
                  {showPassword ? 'Ocultar' : 'Mostrar'}
                </button>
              </div>
            </div>

            <div className="register-group">
              <label htmlFor="confirmPassword">Confirmar senha</label>

              <input
                id="confirmPassword"
                type={showPassword ? 'text' : 'password'}
                placeholder="Digite a senha novamente"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
              />
            </div>

            {error && <p className="register-error">{error}</p>}

            <button
              type="submit"
              className="register-button"
              disabled={loading}
            >
              {loading ? 'Criando conta...' : 'Criar conta'}
            </button>
          </form>

          <div className="register-login-link">
            <span>Já possui uma conta?</span>

            <button
              type="button"
              onClick={() => navigate('/login')}
            >
              Entrar
            </button>
          </div>

          <p className="register-footer">© 2026 Locky</p>
        </div>
      </section>
    </main>
  )
}

export default Register