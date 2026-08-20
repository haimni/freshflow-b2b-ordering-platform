import { useEffect, useState } from 'react'

import {
  getCurrentUser,
  readAccessToken,
  removeAccessToken,
} from './api/auth'
import { getHealth, type HealthResponse } from './api/system'
import LoginDialog from './components/LoginDialog'
import type {
  AuthenticatedUser,
  UserRole,
} from './types/auth'
import './App.css'

type ConnectionState =
  | { status: 'loading' }
  | { status: 'connected'; health: HealthResponse }
  | { status: 'error'; message: string }

const roleLabels: Record<UserRole, string> = {
  admin: 'מנהל מערכת',
  customer_manager: 'מנהל לקוח',
  customer_user: 'משתמש לקוח',
}

function App() {
  const [connection, setConnection] =
    useState<ConnectionState>({
      status: 'loading',
    })

  const [showLogin, setShowLogin] = useState(false)
  const [currentUser, setCurrentUser] =
    useState<AuthenticatedUser | null>(null)
  const [restoringSession, setRestoringSession] =
    useState(true)

  useEffect(() => {
    let active = true

    async function checkServer() {
      try {
        const health = await getHealth()

        if (active) {
          setConnection({
            status: 'connected',
            health,
          })
        }
      } catch (error) {
        if (active) {
          setConnection({
            status: 'error',
            message:
              error instanceof Error
                ? error.message
                : 'לא ניתן להתחבר לשרת',
          })
        }
      }
    }

    void checkServer()

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    let active = true

    async function restoreSession() {
      const accessToken = readAccessToken()

      if (!accessToken) {
        setRestoringSession(false)
        return
      }

      try {
        const user = await getCurrentUser(accessToken)

        if (active) {
          setCurrentUser(user)
        }
      } catch {
        removeAccessToken()
      } finally {
        if (active) {
          setRestoringSession(false)
        }
      }
    }

    void restoreSession()

    return () => {
      active = false
    }
  }, [])

  function handleAuthenticated(user: AuthenticatedUser) {
    setCurrentUser(user)
    setShowLogin(false)
  }

  function handleLogout() {
    removeAccessToken()
    setCurrentUser(null)
  }

  if (restoringSession) {
    return (
      <div className="app-shell" dir="rtl">
        <main className="authenticated-panel">
          <span className="user-role">FreshFlow</span>
          <h1>טוען את המערכת...</h1>
          <p>בודק אם קיימת התחברות פעילה.</p>
        </main>
      </div>
    )
  }

  if (currentUser) {
    return (
      <div className="app-shell" dir="rtl">
        <header className="topbar">
          <a className="brand" href="/">
            <span className="brand-mark">F</span>

            <span>
              <strong>FreshFlow</strong>
              <small>מערכת הזמנות לעסקים</small>
            </span>
          </a>

          <button
            type="button"
            className="logout-button"
            onClick={handleLogout}
          >
            התנתקות
          </button>
        </header>

        <main>
          <section className="authenticated-panel">
            <span className="user-role">
              {roleLabels[currentUser.role]}
            </span>

            <h1>שלום, {currentUser.name}</h1>

            <p>
              התחברת בהצלחה באמצעות {currentUser.email}
            </p>

            <div className="authenticated-actions">
              <button className="primary-button" type="button">
                מעבר למערכת
              </button>
            </div>
          </section>
        </main>

        <footer>
          <span>FreshFlow B2B Ordering Platform</span>
          <span>© 2026</span>
        </footer>
      </div>
    )
  }

  return (
    <div className="app-shell" dir="rtl">
      <header className="topbar">
        <a className="brand" href="/">
          <span className="brand-mark">F</span>

          <span>
            <strong>FreshFlow</strong>
            <small>מערכת הזמנות לעסקים</small>
          </span>
        </a>

        <div
          className={`server-status server-status--${connection.status}`}
          role="status"
        >
          <span className="status-dot" />

          {connection.status === 'loading' && 'בודק חיבור לשרת'}

          {connection.status === 'connected' &&
            `השרת מחובר — ${connection.health.service}`}

          {connection.status === 'error' && 'השרת אינו זמין'}
        </div>
      </header>

      <main>
        <section className="hero">
          <div className="hero-content">
            <span className="eyebrow">
              הזמנות טריות. ניהול פשוט.
            </span>

            <h1>
              כל ההזמנות העסקיות
              <span> במקום אחד</span>
            </h1>

            <p>
              FreshFlow מחברת בין לקוחות עסקיים, מוצרים,
              מחירים חוזיים, מלאי והזמנות במערכת אחת
              פשוטה ונוחה.
            </p>

            <div className="hero-actions">
              <button
                className="primary-button"
                type="button"
                onClick={() => setShowLogin(true)}
              >
                כניסה למערכת
              </button>

              <button
                className="secondary-button"
                type="button"
                disabled
                title="ההרשמה תחובר בשלב הבא"
              >
                הרשמת לקוח חדש
              </button>
            </div>

            {connection.status === 'error' && (
              <p className="connection-error">
                שגיאת חיבור: {connection.message}. ודא ששרת
                FastAPI פועל בכתובת 127.0.0.1:8000.
              </p>
            )}
          </div>

          <div className="hero-card">
            <div className="produce-icon">🥬</div>

            <h2>קטלוג טרי ועדכני</h2>

            <p>
              מחירים מותאמים לחוזה, מלאי בזמן אמת ותהליך
              הזמנה ברור.
            </p>

            <div className="feature-list">
              <div>
                <span>✓</span>
                מחירים לפי חוזה
              </div>

              <div>
                <span>✓</span>
                הזמנות מאובטחות
              </div>

              <div>
                <span>✓</span>
                ניהול מלאי
              </div>
            </div>
          </div>
        </section>

        <section className="features">
          <article>
            <span className="feature-number">01</span>
            <h2>קטלוג מוצרים</h2>
            <p>
              הצגת מוצרים פעילים, קטגוריות ומלאי זמין.
            </p>
          </article>

          <article>
            <span className="feature-number">02</span>
            <h2>מחירים אישיים</h2>
            <p>
              כל לקוח רואה את המחירים שהוגדרו בחוזה שלו.
            </p>
          </article>

          <article>
            <span className="feature-number">03</span>
            <h2>מעקב הזמנות</h2>
            <p>
              צפייה במצב ההזמנה מרגע היצירה ועד להשלמה.
            </p>
          </article>
        </section>
      </main>

      <footer>
        <span>FreshFlow B2B Ordering Platform</span>
        <span>© 2026</span>
      </footer>

      {showLogin && (
        <LoginDialog
          onClose={() => setShowLogin(false)}
          onAuthenticated={handleAuthenticated}
        />
      )}
    </div>
  )
}

export default App