import { useEffect, useState } from 'react'

import {
  getAdminOrders,
  updateAdminOrderStatus,
} from '../api/adminOrders'
import { ApiError } from '../api/http'
import type { AdminOrder } from '../types/adminOrder'
import type { OrderStatus } from '../types/order'
import './AdminOrdersPage.css'

interface AdminOrdersPageProps {
  onUnauthorized: () => void
}

type OrdersState =
  | { status: 'loading' }
  | { status: 'loaded'; orders: AdminOrder[] }
  | { status: 'error'; message: string }

type StatusFilter = 'all' | OrderStatus

const statusLabels: Record<OrderStatus, string> = {
  pending: 'ממתינה לאישור',
  confirmed: 'אושרה',
  processing: 'בטיפול',
  completed: 'הושלמה',
  cancelled: 'בוטלה',
}

const nextStatus: Partial<Record<OrderStatus, OrderStatus>> = {
  pending: 'confirmed',
  confirmed: 'processing',
  processing: 'completed',
}

const nextStatusLabels: Partial<
  Record<OrderStatus, string>
> = {
  pending: 'אישור הזמנה',
  confirmed: 'העברה לטיפול',
  processing: 'סיום הזמנה',
}

function formatCurrency(value: string): string {
  const numericValue = Number(value)

  if (!Number.isFinite(numericValue)) {
    return value
  }

  return new Intl.NumberFormat('he-IL', {
    style: 'currency',
    currency: 'ILS',
    minimumFractionDigits: 2,
  }).format(numericValue)
}

function formatQuantity(value: string): string {
  const numericValue = Number(value)

  if (!Number.isFinite(numericValue)) {
    return value
  }

  return new Intl.NumberFormat('he-IL', {
    maximumFractionDigits: 3,
  }).format(numericValue)
}

function formatDate(value: string): string {
  const date = new Date(value)

  if (Number.isNaN(date.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('he-IL', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date)
}

function createErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 403) {
      return 'אין הרשאה לביצוע פעולת ניהול.'
    }

    if (error.status === 404) {
      return 'ההזמנה לא נמצאה.'
    }

    if (error.status === 409) {
      return 'מעבר הסטטוס המבוקש אינו חוקי.'
    }
  }

  return 'הפעולה נכשלה. נסה שוב.'
}

function AdminOrdersPage({
  onUnauthorized,
}: AdminOrdersPageProps) {
  const [ordersState, setOrdersState] =
    useState<OrdersState>({
      status: 'loading',
    })

  const [statusFilter, setStatusFilter] =
    useState<StatusFilter>('all')

  const [updatingOrderId, setUpdatingOrderId] =
    useState<number | null>(null)

  const [actionError, setActionError] =
    useState<string | null>(null)

  useEffect(() => {
    let active = true

    getAdminOrders({
      status:
        statusFilter === 'all'
          ? undefined
          : statusFilter,
    })
      .then((orders) => {
        if (active) {
          setOrdersState({
            status: 'loaded',
            orders,
          })
        }
      })
      .catch((error: unknown) => {
        if (!active) {
          return
        }

        if (error instanceof ApiError && error.status === 401) {
          onUnauthorized()
          return
        }

        setOrdersState({
          status: 'error',
          message: createErrorMessage(error),
        })
      })

    return () => {
      active = false
    }
  }, [onUnauthorized, statusFilter])

  function replaceOrder(updatedOrder: AdminOrder) {
    setOrdersState((currentState) => {
      if (currentState.status !== 'loaded') {
        return currentState
      }

      const orderStillMatchesFilter =
        statusFilter === 'all' ||
        updatedOrder.status === statusFilter

      return {
        status: 'loaded',
        orders: orderStillMatchesFilter
          ? currentState.orders.map((order) =>
              order.id === updatedOrder.id
                ? updatedOrder
                : order,
            )
          : currentState.orders.filter(
              (order) => order.id !== updatedOrder.id,
            ),
      }
    })
  }

  async function changeOrderStatus(
    order: AdminOrder,
    requestedStatus: OrderStatus,
  ) {
    if (requestedStatus === 'cancelled') {
      const confirmed = window.confirm(
        `לבטל את הזמנה מספר ${order.id} של ${order.customer.company_name}?`,
      )

      if (!confirmed) {
        return
      }
    }

    setActionError(null)
    setUpdatingOrderId(order.id)

    try {
      const updatedOrder =
        await updateAdminOrderStatus(order.id, {
          status: requestedStatus,
        })

      replaceOrder(updatedOrder)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onUnauthorized()
        return
      }

      setActionError(createErrorMessage(error))
    } finally {
      setUpdatingOrderId(null)
    }
  }

  function handleFilterChange(filter: StatusFilter) {
    setActionError(null)
    setOrdersState({ status: 'loading' })
    setStatusFilter(filter)
  }

  return (
    <section className="admin-orders-page">
      <div className="admin-orders-heading">
        <div>
          <span className="admin-orders-eyebrow">
            ממשק מנהל
          </span>

          <h1>ניהול הזמנות</h1>

          <p>
            צפייה בהזמנות וקידומן לאורך תהליך הטיפול.
          </p>
        </div>

        {ordersState.status === 'loaded' && (
          <span className="admin-orders-count">
            {ordersState.orders.length} הזמנות
          </span>
        )}
      </div>

      <div
        className="admin-order-filters"
        aria-label="סינון הזמנות לפי סטטוס"
      >
        {(
          [
            ['all', 'הכול'],
            ['pending', 'ממתינות'],
            ['confirmed', 'מאושרות'],
            ['processing', 'בטיפול'],
            ['completed', 'הושלמו'],
            ['cancelled', 'בוטלו'],
          ] as const
        ).map(([value, label]) => (
          <button
            type="button"
            key={value}
            className={
              statusFilter === value
                ? 'admin-filter-button admin-filter-button--active'
                : 'admin-filter-button'
            }
            aria-pressed={statusFilter === value}
            onClick={() => handleFilterChange(value)}
          >
            {label}
          </button>
        ))}
      </div>

      {actionError && (
        <div className="admin-orders-error" role="alert">
          {actionError}
        </div>
      )}

      {ordersState.status === 'loading' && (
        <div className="admin-orders-message" role="status">
          טוען הזמנות...
        </div>
      )}

      {ordersState.status === 'error' && (
        <div className="admin-orders-message" role="alert">
          {ordersState.message}
        </div>
      )}

      {ordersState.status === 'loaded' &&
        ordersState.orders.length === 0 && (
          <div className="admin-orders-message">
            אין הזמנות התואמות לסינון שנבחר.
          </div>
        )}

      {ordersState.status === 'loaded' &&
        ordersState.orders.length > 0 && (
          <div className="admin-orders-list">
            {ordersState.orders.map((order) => {
              const allowedNextStatus =
                nextStatus[order.status]

              const updating =
                updatingOrderId === order.id

              const canCancel =
                order.status === 'pending' ||
                order.status === 'confirmed'

              return (
                <article
                  className="admin-order-card"
                  key={order.id}
                >
                  <div className="admin-order-header">
                    <div>
                      <strong>
                        הזמנה מספר {order.id}
                      </strong>

                      <span>
                        {order.customer.company_name}
                        {' · '}
                        לקוח מספר {order.customer.id}
                      </span>

                      <span>
                        {formatDate(order.created_at)}
                      </span>
                    </div>

                    <span
                      className={`admin-order-status admin-order-status--${order.status}`}
                    >
                      {statusLabels[order.status]}
                    </span>
                  </div>

                  <div className="admin-order-table">
                    <div className="admin-order-table-heading">
                      <span>מוצר</span>
                      <span>כמות</span>
                      <span>מחיר</span>
                      <span>סכום</span>
                    </div>

                    {order.items.map((item) => (
                      <div
                        className="admin-order-item"
                        key={item.id}
                      >
                        <strong>{item.product_name}</strong>

                        <span>
                          {formatQuantity(item.quantity)}
                        </span>

                        <span>
                          {formatCurrency(item.unit_price)}
                        </span>

                        <strong>
                          {formatCurrency(item.line_total)}
                        </strong>
                      </div>
                    ))}
                  </div>

                  <div className="admin-order-footer">
                    <div>
                      <span>סה״כ הזמנה</span>

                      <strong>
                        {formatCurrency(order.total)}
                      </strong>
                    </div>

                    <div className="admin-order-actions">
                      {canCancel && (
                        <button
                          type="button"
                          className="admin-order-cancel"
                          disabled={
                            updatingOrderId !== null
                          }
                          onClick={() =>
                            void changeOrderStatus(
                              order,
                              'cancelled',
                            )
                          }
                        >
                          ביטול הזמנה
                        </button>
                      )}

                      {allowedNextStatus && (
                        <button
                          type="button"
                          className="admin-order-advance"
                          disabled={
                            updatingOrderId !== null
                          }
                          onClick={() =>
                            void changeOrderStatus(
                              order,
                              allowedNextStatus,
                            )
                          }
                        >
                          {updating
                            ? 'מעדכן...'
                            : nextStatusLabels[
                                order.status
                              ]}
                        </button>
                      )}
                    </div>
                  </div>
                </article>
              )
            })}
          </div>
        )}
    </section>
  )
}

export default AdminOrdersPage