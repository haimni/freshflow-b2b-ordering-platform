import { useEffect, useState } from 'react'

import {
  cancelCustomerOrder,
  getCustomerOrders,
} from '../api/customerOrders'
import { ApiError } from '../api/http'
import type {
  CustomerOrder,
  OrderStatus,
} from '../types/order'
import './CustomerOrdersPage.css'

interface CustomerOrdersPageProps {
  onUnauthorized: () => void
}

type OrdersState =
  | { status: 'loading' }
  | { status: 'loaded'; orders: CustomerOrder[] }
  | { status: 'error'; message: string }

const statusLabels: Record<OrderStatus, string> = {
  pending: 'ממתינה לאישור',
  confirmed: 'אושרה',
  processing: 'בטיפול',
  completed: 'הושלמה',
  cancelled: 'בוטלה',
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

function createLoadErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 403) {
    return 'החשבון אינו משויך ללקוח.'
  }

  return 'לא ניתן לטעון את ההזמנות כרגע.'
}

function createCancelErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 404) {
      return 'ההזמנה לא נמצאה.'
    }

    if (error.status === 409) {
      return 'ניתן לבטל רק הזמנה שממתינה לאישור.'
    }
  }

  return 'לא ניתן לבטל את ההזמנה כרגע.'
}

function CustomerOrdersPage({
  onUnauthorized,
}: CustomerOrdersPageProps) {
  const [ordersState, setOrdersState] =
    useState<OrdersState>({
      status: 'loading',
    })

  const [cancellingOrderId, setCancellingOrderId] =
    useState<number | null>(null)

  const [actionError, setActionError] =
    useState<string | null>(null)

  useEffect(() => {
    let active = true

    getCustomerOrders()
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
          message: createLoadErrorMessage(error),
        })
      })

    return () => {
      active = false
    }
  }, [onUnauthorized])

  async function reloadOrders() {
    setActionError(null)
    setOrdersState({ status: 'loading' })

    try {
      const orders = await getCustomerOrders()

      setOrdersState({
        status: 'loaded',
        orders,
      })
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onUnauthorized()
        return
      }

      setOrdersState({
        status: 'error',
        message: createLoadErrorMessage(error),
      })
    }
  }

  async function handleCancel(order: CustomerOrder) {
    const confirmed = window.confirm(
      `לבטל את הזמנה מספר ${order.id}?`,
    )

    if (!confirmed) {
      return
    }

    setActionError(null)
    setCancellingOrderId(order.id)

    try {
      const cancelledOrder =
        await cancelCustomerOrder(order.id)

      setOrdersState((currentState) => {
        if (currentState.status !== 'loaded') {
          return currentState
        }

        return {
          status: 'loaded',
          orders: currentState.orders.map((currentOrder) =>
            currentOrder.id === cancelledOrder.id
              ? cancelledOrder
              : currentOrder,
          ),
        }
      })
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onUnauthorized()
        return
      }

      setActionError(createCancelErrorMessage(error))
    } finally {
      setCancellingOrderId(null)
    }
  }

  return (
    <section className="orders-page">
      <div className="orders-heading">
        <div>
          <span className="orders-eyebrow">
            היסטוריית פעילות
          </span>

          <h1>ההזמנות שלי</h1>

          <p>
            צפייה בפרטי הזמנות ובסטטוס הטיפול בהן.
          </p>
        </div>

        {ordersState.status === 'loaded' && (
          <span className="orders-count">
            {ordersState.orders.length} הזמנות
          </span>
        )}
      </div>

      {actionError && (
        <div className="orders-action-error" role="alert">
          {actionError}
        </div>
      )}

      {ordersState.status === 'loading' && (
        <div className="orders-message" role="status">
          טוען הזמנות...
        </div>
      )}

      {ordersState.status === 'error' && (
        <div className="orders-error" role="alert">
          <strong>טעינת ההזמנות נכשלה</strong>
          <span>{ordersState.message}</span>

          <button
            type="button"
            onClick={() => void reloadOrders()}
          >
            ניסיון נוסף
          </button>
        </div>
      )}

      {ordersState.status === 'loaded' &&
        ordersState.orders.length === 0 && (
          <div className="orders-empty">
            <strong>עדיין לא בוצעו הזמנות</strong>
            <p>
              הזמנות חדשות שתשלח מהקטלוג יופיעו כאן.
            </p>
          </div>
        )}

      {ordersState.status === 'loaded' &&
        ordersState.orders.length > 0 && (
          <div className="orders-list">
            {ordersState.orders.map((order) => {
              const cancelling =
                cancellingOrderId === order.id

              return (
                <article
                  className="order-card"
                  key={order.id}
                >
                  <div className="order-card-header">
                    <div>
                      <span className="order-number">
                        הזמנה מספר {order.id}
                      </span>

                      <span className="order-date">
                        {formatDate(order.created_at)}
                      </span>
                    </div>

                    <span
                      className={`order-status order-status--${order.status}`}
                    >
                      {statusLabels[order.status]}
                    </span>
                  </div>

                  <div className="order-items-table">
                    <div className="order-items-heading">
                      <span>מוצר</span>
                      <span>כמות</span>
                      <span>מחיר</span>
                      <span>סכום</span>
                    </div>

                    {order.items.map((item) => (
                      <div
                        className="order-item-row"
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

                  <div className="order-card-footer">
                    <div className="order-total">
                      <span>סה״כ הזמנה</span>
                      <strong>
                        {formatCurrency(order.total)}
                      </strong>
                    </div>

                    {order.status === 'pending' && (
                      <button
                        type="button"
                        className="cancel-order-button"
                        disabled={
                          cancellingOrderId !== null
                        }
                        onClick={() =>
                          void handleCancel(order)
                        }
                      >
                        {cancelling
                          ? 'מבטל הזמנה...'
                          : 'ביטול הזמנה'}
                      </button>
                    )}
                  </div>
                </article>
              )
            })}
          </div>
        )}
    </section>
  )
}

export default CustomerOrdersPage