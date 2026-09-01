import { useEffect, useState } from 'react'
import RegisterDialog from './components/RegisterDialog'

import {
  getCurrentUser,
  readAccessToken,
  removeAccessToken,
} from './api/auth'
import { getHealth } from './api/system'
import LoginDialog from './components/LoginDialog'
import DashboardPage from './pages/DashboardPage'
import HomePage, {
  type ConnectionState,
} from './pages/HomePage'
import type { AuthenticatedUser } from './types/auth'
import './App.css'

function App() {
  const [connection, setConnection] =
    useState<ConnectionState>({
      status: 'loading',
    })

  const [showLogin, setShowLogin] = useState(false)

  const [showRegistration, setShowRegistration] = useState(false)

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
    setShowRegistration(false)
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
      <DashboardPage
        user={currentUser}
        onLogout={handleLogout}
      />
    )
  }

    return (
    <>
      <HomePage
        connection={connection}
        onLogin={() => {
          setShowRegistration(false)
          setShowLogin(true)
        }}
        onRegister={() => {
          setShowLogin(false)
          setShowRegistration(true)
        }}
      />

      {showLogin && (
        <LoginDialog
          onClose={() => setShowLogin(false)}
          onAuthenticated={handleAuthenticated}
        />
      )}

      {showRegistration && (
        <RegisterDialog
          onClose={() => setShowRegistration(false)}
          onAuthenticated={handleAuthenticated}
        />
      )}
    </>
  )
}

export default App