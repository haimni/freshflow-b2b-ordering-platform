import { useEffect, useMemo, useState } from 'react'

import { getAdminProducts } from '../api/adminCatalog'
import { getAdminInventoryAdjustments } from '../api/adminInventory'
import { ApiError } from '../api/http'
import type { AdminProduct } from '../types/adminCatalog'
import type { AdminInventoryAdjustment } from '../types/adminInventory'
import './AdminInventoryPage.css'

interface AdminInventoryPageProps {
  onUnauthorized: () => void
}

type InventoryState =
  | { status: 'loading' }
  | {
      status: 'loaded'
      products: AdminProduct[]
      adjustments: AdminInventoryAdjustment[]
    }
  | { status: 'error'; message: string }

function formatQuantity(value: string): string {
  const numericValue = Number(value)

  if (!Number.isFinite(numericValue)) {
    return value
  }

  const formattedValue = new Intl.NumberFormat('he-IL', {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  }).format(Math.abs(numericValue))

  return numericValue > 0
    ? `+${formattedValue}`
    : `-${formattedValue}`
}

function formatStock(value: string): string {
  const numericValue = Number(value)

  if (!Number.isFinite(numericValue)) {
    return value
  }

  return new Intl.NumberFormat('he-IL', {
    minimumFractionDigits: 3,
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
    return 'אין הרשאה לצפות בהיסטוריית המלאי.'
  }

  return 'לא ניתן לטעון את היסטוריית המלאי כרגע.'
}

function AdminInventoryPage({
  onUnauthorized,
}: AdminInventoryPageProps) {
  const [inventoryState, setInventoryState] =
    useState<InventoryState>({
      status: 'loading',
    })

  const [productFilter, setProductFilter] =
    useState<number | 'all'>('all')

  useEffect(() => {
    let active = true

    Promise.all([
      getAdminProducts(),
      getAdminInventoryAdjustments(),
    ])
      .then(([products, adjustments]) => {
        if (!active) {
          return
        }

        setInventoryState({
          status: 'loaded',
          products,
          adjustments,
        })
      })
      .catch((error: unknown) => {
        if (!active) {
          return
        }

        if (
          error instanceof ApiError &&
          error.status === 401
        ) {
          onUnauthorized()
          return
        }

        setInventoryState({
          status: 'error',
          message: createLoadErrorMessage(error),
        })
      })

    return () => {
      active = false
    }
  }, [onUnauthorized])

  const filteredAdjustments = useMemo(() => {
    if (inventoryState.status !== 'loaded') {
      return []
    }

    if (productFilter === 'all') {
      return inventoryState.adjustments
    }

    return inventoryState.adjustments.filter(
      (adjustment) =>
        adjustment.product_id === productFilter,
    )
  }, [inventoryState, productFilter])

  return (
    <section className="admin-inventory-page">
      <div className="admin-inventory-heading">
        <div>
          <span className="admin-inventory-eyebrow">
            ביקורת ותיעוד
          </span>

          <h1>היסטוריית התאמות מלאי</h1>

          <p>
            תיעוד התאמות מלאי ידניות שבוצעו על ידי מנהלי
            המערכת, כולל הכמות לפני ואחרי השינוי והסיבה
            לביצועו.
          </p>
        </div>

        {inventoryState.status === 'loaded' && (
          <span className="admin-inventory-count">
            {filteredAdjustments.length} התאמות
          </span>
        )}
      </div>

      {inventoryState.status === 'loading' && (
        <div
          className="admin-inventory-message"
          role="status"
        >
          טוען היסטוריית מלאי...
        </div>
      )}

      {inventoryState.status === 'error' && (
        <div
          className="admin-inventory-error"
          role="alert"
        >
          {inventoryState.message}
        </div>
      )}

      {inventoryState.status === 'loaded' && (
        <>
          <div className="admin-inventory-filters">
            <label>
              <span>סינון לפי מוצר</span>

              <select
                value={productFilter}
                onChange={(event) => {
                  const value = event.target.value

                  setProductFilter(
                    value === 'all'
                      ? 'all'
                      : Number(value),
                  )
                }}
              >
                <option value="all">כל המוצרים</option>

                {inventoryState.products.map((product) => (
                  <option
                    value={product.id}
                    key={product.id}
                  >
                    {product.name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {filteredAdjustments.length === 0 ? (
            <div className="admin-inventory-message">
              לא נמצאו התאמות מלאי עבור הסינון שנבחר.
            </div>
          ) : (
            <div className="admin-inventory-table-wrapper">
              <table className="admin-inventory-table">
                <thead>
                  <tr>
                    <th>תאריך</th>
                    <th>מוצר</th>
                    <th>שינוי</th>
                    <th>לפני</th>
                    <th>אחרי</th>
                    <th>בוצע על ידי</th>
                    <th>סיבה</th>
                  </tr>
                </thead>

                <tbody>
                  {filteredAdjustments.map(
                    (adjustment) => {
                      const numericChange = Number(
                        adjustment.quantity_change,
                      )

                      return (
                        <tr key={adjustment.id}>
                          <td>
                            {formatDate(
                              adjustment.created_at,
                            )}
                          </td>

                          <td>
                            <strong>
                              {adjustment.product.name}
                            </strong>

                            <small>
                              מוצר #{adjustment.product_id}
                            </small>
                          </td>

                          <td>
                            <span
                              className={
                                numericChange > 0
                                  ? 'admin-inventory-change admin-inventory-change--positive'
                                  : 'admin-inventory-change admin-inventory-change--negative'
                              }
                            >
                              {formatQuantity(
                                adjustment.quantity_change,
                              )}
                            </span>
                          </td>

                          <td>
                            {formatStock(
                              adjustment.stock_before,
                            )}
                          </td>

                          <td>
                            <strong>
                              {formatStock(
                                adjustment.stock_after,
                              )}
                            </strong>
                          </td>

                          <td>
                            {
                              adjustment.performed_by_user
                                .name
                            }

                            <small>
                              משתמש #
                              {
                                adjustment.performed_by_user_id
                              }
                            </small>
                          </td>

                          <td className="admin-inventory-reason">
                            {adjustment.reason}
                          </td>
                        </tr>
                      )
                    },
                  )}
                </tbody>
              </table>
            </div>
          )}

          <p className="admin-inventory-limit-note">
            מוצגות עד 100 ההתאמות האחרונות.
          </p>
        </>
      )}
    </section>
  )
}

export default AdminInventoryPage