import { useState } from 'react'

import AdminCatalogPage from './AdminCatalogPage'
import AdminInventoryPage from './AdminInventoryPage'
import AdminOrdersPage from './AdminOrdersPage'
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

type AdminView =
  | 'orders'
  | 'catalog'
  | 'inventory'

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

  const [adminView, setAdminView] =
    useState<AdminView>('orders')

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
          {isCustomer ? (
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
          ) : (
            <nav
              className="dashboard-navigation"
              aria-label="ניווט בממשק המנהל"
            >
              <button
                type="button"
                className={
                  adminView === 'orders'
                    ? 'dashboard-navigation-button dashboard-navigation-button--active'
                    : 'dashboard-navigation-button'
                }
                aria-pressed={adminView === 'orders'}
                onClick={() => setAdminView('orders')}
              >
                הזמנות
              </button>

              <button
                type="button"
                className={
                  adminView === 'catalog'
                    ? 'dashboard-navigation-button dashboard-navigation-button--active'
                    : 'dashboard-navigation-button'
                }
                aria-pressed={adminView === 'catalog'}
                onClick={() => setAdminView('catalog')}
              >
                קטלוג
              </button>

              <button
                type="button"
                className={
                  adminView === 'inventory'
                    ? 'dashboard-navigation-button dashboard-navigation-button--active'
                    : 'dashboard-navigation-button'
                }
                aria-pressed={adminView === 'inventory'}
                onClick={() =>
                  setAdminView('inventory')
                }
              >
                התאמות מלאי  
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
          <>
            {adminView === 'orders' && (
              <AdminOrdersPage
                onUnauthorized={onLogout}
              />
            )}

            {adminView === 'catalog' && (
              <AdminCatalogPage
                onUnauthorized={onLogout}
              />
            )}

            {adminView === 'inventory' && (
              <AdminInventoryPage
                onUnauthorized={onLogout}
              />
            )}
          </>
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