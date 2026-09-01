import type { HealthResponse } from '../api/system'

export type ConnectionState =
  | { status: 'loading' }
  | { status: 'connected'; health: HealthResponse }
  | { status: 'error'; message: string }

interface HomePageProps {
  connection: ConnectionState
  onLogin: () => void
  onRegister: () => void
}

function HomePage({
  connection,
  onLogin,
  onRegister,
}: HomePageProps) {
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

          {connection.status === 'loading' &&
            'בודק חיבור לשרת'}

          {connection.status === 'connected' &&
            `השרת מחובר — ${connection.health.service}`}

          {connection.status === 'error' &&
            'השרת אינו זמין'}
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
                onClick={onLogin}
              >
                כניסה למערכת
              </button>

              <button
                className="secondary-button"
                type="button"
                onClick={onRegister}
              >
                הרשמת לקוח חדש
              </button>
            </div>

            {connection.status === 'error' && (
              <p className="connection-error">
                שגיאת חיבור: {connection.message}. ודא
                ששרת FastAPI פועל בכתובת 127.0.0.1:8000.
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
    </div>
  )
}

export default HomePage
