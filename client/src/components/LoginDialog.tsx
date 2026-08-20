import {
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from 'react'

import {
  getCurrentUser,
  login,
  saveAccessToken,
} from '../api/auth'
import { ApiError } from '../api/http'
import type { AuthenticatedUser } from '../types/auth'
import './LoginDialog.css'

interface LoginDialogProps {
  onClose: () => void
  onAuthenticated: (user: AuthenticatedUser) => void
}

function LoginDialog({
  onClose,
  onAuthenticated,
}: LoginDialogProps) {
  const emailInputRef = useRef<HTMLInputElement>(null)

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(
    null,
  )

  useEffect(() => {
    emailInputRef.current?.focus()

    function closeWithEscape(event: KeyboardEvent) {
      if (event.key === 'Escape' && !submitting) {
        onClose()
      }
    }

    window.addEventListener('keydown', closeWithEscape)

    return () => {
      window.removeEventListener('keydown', closeWithEscape)
    }
  }, [onClose, submitting])

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setErrorMessage(null)
    setSubmitting(true)

    try {
      const token = await login(email, password)

      saveAccessToken(token.access_token)

      const user = await getCurrentUser(token.access_token)

      onAuthenticated(user)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        setErrorMessage('כתובת הדוא״ל או הסיסמה שגויות')
      } else {
        setErrorMessage(
          'לא ניתן להתחבר למערכת כרגע. נסה שוב מאוחר יותר.',
        )
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className="login-overlay"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget && !submitting) {
          onClose()
        }
      }}
    >
      <section
        className="login-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="login-title"
        dir="rtl"
      >
        <button
          type="button"
          className="login-close"
          onClick={onClose}
          disabled={submitting}
          aria-label="סגירת חלון הכניסה"
        >
          ×
        </button>

        <div className="login-heading">
          <span className="login-logo">F</span>

          <div>
            <span className="login-eyebrow">FreshFlow</span>
            <h2 id="login-title">כניסה למערכת</h2>
          </div>
        </div>

        <p className="login-description">
          הזן את כתובת הדוא״ל והסיסמה שלך כדי להמשיך.
        </p>

        <form onSubmit={handleSubmit}>
          <label className="form-field">
            <span>כתובת דוא״ל</span>

            <input
              ref={emailInputRef}
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="name@example.com"
              autoComplete="username"
              required
              disabled={submitting}
            />
          </label>

          <label className="form-field">
            <span>סיסמה</span>

            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="הזן סיסמה"
              autoComplete="current-password"
              required
              disabled={submitting}
            />
          </label>

          {errorMessage && (
            <div className="login-error" role="alert">
              {errorMessage}
            </div>
          )}

          <button
            type="submit"
            className="login-submit"
            disabled={submitting}
          >
            {submitting ? 'מתחבר...' : 'כניסה'}
          </button>
        </form>
      </section>
    </div>
  )
}

export default LoginDialog