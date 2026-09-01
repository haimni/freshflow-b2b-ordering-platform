import {
  type FormEvent,
  useEffect,
  useRef,
  useState,
} from 'react'

import {
  getCurrentUser,
  login,
  registerCustomer,
  saveAccessToken,
} from '../api/auth'
import { ApiError } from '../api/http'
import type { AuthenticatedUser } from '../types/auth'
import './LoginDialog.css'

interface RegisterDialogProps {
  onClose: () => void
  onAuthenticated: (user: AuthenticatedUser) => void
}

function RegisterDialog({
  onClose,
  onAuthenticated,
}: RegisterDialogProps) {
  const companyInputRef = useRef<HTMLInputElement>(null)

  const [companyName, setCompanyName] = useState('')
  const [businessNumber, setBusinessNumber] = useState('')
  const [phone, setPhone] = useState('')
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordConfirmation, setPasswordConfirmation] =
    useState('')

  const [submitting, setSubmitting] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(
    null,
  )

  useEffect(() => {
    companyInputRef.current?.focus()

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

    if (password !== passwordConfirmation) {
      setErrorMessage('הסיסמאות אינן זהות')
      return
    }

    if (password.length < 12) {
      setErrorMessage('הסיסמה חייבת להכיל לפחות 12 תווים')
      return
    }

    setSubmitting(true)

    try {
      await registerCustomer({
        company_name: companyName.trim(),
        business_number: businessNumber.trim(),
        phone: phone.trim() || null,
        name: name.trim(),
        email: email.trim().toLowerCase(),
        password,
      })

      const token = await login(email, password)

      saveAccessToken(token.access_token)

      const user = await getCurrentUser(token.access_token)

      onAuthenticated(user)
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) {
        setErrorMessage(
          'כתובת הדוא״ל או מספר העסק כבר רשומים במערכת',
        )
      } else if (
        error instanceof ApiError &&
        error.status === 422
      ) {
        setErrorMessage(
          'אחד מהפרטים אינו תקין. בדוק את כל השדות.',
        )
      } else {
        setErrorMessage(
          'לא ניתן להשלים את ההרשמה כרגע. נסה שוב.',
        )
      }
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className="login-overlay registration-overlay"
      role="presentation"
      onMouseDown={(event) => {
        if (
          event.target === event.currentTarget &&
          !submitting
        ) {
          onClose()
        }
      }}
    >
      <section
        className="login-dialog registration-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="registration-title"
        dir="rtl"
      >
        <button
          type="button"
          className="login-close"
          onClick={onClose}
          disabled={submitting}
          aria-label="סגירת חלון ההרשמה"
        >
          ×
        </button>

        <div className="login-heading">
          <span className="login-logo">F</span>

          <div>
            <span className="login-eyebrow">FreshFlow</span>
            <h2 id="registration-title">
              הרשמת לקוח חדש
            </h2>
          </div>
        </div>

        <p className="login-description">
          ההרשמה תיצור עסק, משתמש מנהל וחוזה תמחור
          כברירת מחדל.
        </p>

        <form
          className="registration-form"
          onSubmit={handleSubmit}
        >
          <label className="form-field">
            <span>שם העסק</span>

            <input
              ref={companyInputRef}
              type="text"
              value={companyName}
              onChange={(event) =>
                setCompanyName(event.target.value)
              }
              minLength={2}
              maxLength={150}
              autoComplete="organization"
              required
              disabled={submitting}
            />
          </label>

          <label className="form-field">
            <span>מספר עוסק / ח״פ</span>

            <input
              type="text"
              value={businessNumber}
              onChange={(event) =>
                setBusinessNumber(event.target.value)
              }
              minLength={2}
              maxLength={30}
              required
              disabled={submitting}
            />
          </label>

          <label className="form-field">
            <span>שם מלא</span>

            <input
              type="text"
              value={name}
              onChange={(event) => setName(event.target.value)}
              minLength={2}
              maxLength={120}
              autoComplete="name"
              required
              disabled={submitting}
            />
          </label>

          <label className="form-field">
            <span>טלפון — לא חובה</span>

            <input
              type="tel"
              value={phone}
              onChange={(event) =>
                setPhone(event.target.value)
              }
              maxLength={30}
              autoComplete="tel"
              disabled={submitting}
            />
          </label>

          <label className="form-field registration-full-width">
            <span>כתובת דוא״ל</span>

            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              placeholder="name@example.com"
              autoComplete="email"
              required
              disabled={submitting}
            />
          </label>

          <label className="form-field">
            <span>סיסמה</span>

            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              minLength={12}
              maxLength={128}
              autoComplete="new-password"
              required
              disabled={submitting}
            />
          </label>

          <label className="form-field">
            <span>אימות סיסמה</span>

            <input
              type="password"
              value={passwordConfirmation}
              onChange={(event) =>
                setPasswordConfirmation(event.target.value)
              }
              minLength={12}
              maxLength={128}
              autoComplete="new-password"
              required
              disabled={submitting}
            />
          </label>

          <p className="password-hint registration-full-width">
            הסיסמה חייבת להכיל לפחות 12 תווים.
          </p>

          {errorMessage && (
            <div
              className="login-error registration-full-width"
              role="alert"
            >
              {errorMessage}
            </div>
          )}

          <button
            type="submit"
            className="login-submit registration-full-width"
            disabled={submitting}
          >
            {submitting
              ? 'יוצר חשבון...'
              : 'יצירת חשבון וכניסה'}
          </button>
        </form>
      </section>
    </div>
  )
}

export default RegisterDialog