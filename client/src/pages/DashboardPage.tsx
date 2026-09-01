import { useState } from 'react'

import CustomerCatalogPage from './CustomerCatalogPage'
import CustomerOrdersPage from './CustomerOrdersPage'
import type {
  AuthenticatedUser,
  UserRole,
} from '../types/auth'

interface DashboardPageProps {
  user: AuthenticatedUser
  onLogout: () => void
}

type CustomerView = 'catalog' | 'orders'

const roleLabels: Record<UserRole, string> = {
  admin: 'מנהל מערכת',
  customer_manager: 'מנהל לקוח',
  customer_user: 'משתמש לקוח',
}

function DashboardPage({
  user,
  onLogout,
}: DashboardPageProps) {
  const [customerView, setCustomerView] =
    useState<CustomerView>('catalog')

  const isCustomer =
    user.role === 'customer_manager' ||
    user.role === 'customer_user'

  return (
    <div className="app-shell" dir="rtl">
      <header className="topbar">
        <a className="brand" href="/">
          <span className="brand-mark">F</span>

          <span>
            <strong>FreshFlow</strong>
            <small>
              {user.name} · {roleLabels[user.role]}
            </small>
          </span>
        </a>

        <div className="dashboard-actions">
          {isCustomer && (
            <nav
              className="dashboard-navigation"
              aria-label="ניווט באזור הלקוח"
            >
              <button
                type="button"
                className={
                  customerView === 'catalog'
                    ? 'dashboard-navigation-button dashboard-navigation-button--active'
                    : 'dashboard-navigation-button'
                }
                aria-pressed={customerView === 'catalog'}
                onClick={() =>
                  setCustomerView('catalog')
                }
              >
                קטלוג
              </button>

              <button
                type="button"
                className={
                  customerView === 'orders'
                    ? 'dashboard-navigation-button dashboard-navigation-button--active'
                    : 'dashboard-navigation-button'
                }
                aria-pressed={customerView === 'orders'}
                onClick={() =>
                  setCustomerView('orders')
                }
              >
                ההזמנות שלי
              </button>
            </nav>
          )}

          <button
            type="button"
            className="logout-button"
            onClick={onLogout}
          >
            התנתקות
          </button>
        </div>
      </header>

      <main>
        {isCustomer ? (
          customerView === 'catalog' ? (
            <CustomerCatalogPage
              onUnauthorized={onLogout}
            />
          ) : (
            <CustomerOrdersPage
              onUnauthorized={onLogout}
            />
          )
        ) : (
          <section className="authenticated-panel">
            <span className="user-role">
              {roleLabels[user.role]}
            </span>

            <h1>שלום, {user.name}</h1>

            <p>ממשק הניהול יחובר בשלב הבא.</p>
          </section>
        )}
      </main>

      <footer>
        <span>FreshFlow B2B Ordering Platform</span>
        <span>© 2026</span>
      </footer>
    </div>
  )
}

export default DashboardPage