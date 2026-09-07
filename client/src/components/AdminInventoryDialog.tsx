import { useMemo, useState } from 'react'

import { createAdminInventoryAdjustment } from '../api/adminInventory'
import { ApiError } from '../api/http'
import type { AdminProduct } from '../types/adminCatalog'
import type { AdminInventoryAdjustment } from '../types/adminInventory'
import './AdminInventoryDialog.css'

interface AdminInventoryDialogProps {
  product: AdminProduct
  onClose: () => void
  onAdjusted: (
    adjustment: AdminInventoryAdjustment,
  ) => void
  onUnauthorized: () => void
}

const QUANTITY_PATTERN =
  /^-?\d{1,9}(?:\.\d{1,3})?$/

function formatStock(value: number): string {
  if (!Number.isFinite(value)) {
    return '—'
  }

  return new Intl.NumberFormat('he-IL', {
    minimumFractionDigits: 3,
    maximumFractionDigits: 3,
  }).format(value)
}

function createErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'לא ניתן לעדכן את המלאי כרגע.'
  }

  if (error.status === 403) {
    return 'אין הרשאה לבצע התאמות מלאי.'
  }

  if (error.status === 404) {
    return 'המוצר אינו קיים עוד.'
  }

  if (error.status === 409) {
    return 'הפעולה נדחתה מפני שהיא תיצור מלאי שלילי.'
  }

  if (error.status === 422) {
    return 'כמות השינוי או סיבת השינוי אינן תקינות.'
  }

  return 'לא ניתן לעדכן את המלאי כרגע.'
}

function AdminInventoryDialog({
  product,
  onClose,
  onAdjusted,
  onUnauthorized,
}: AdminInventoryDialogProps) {
  const [quantityChange, setQuantityChange] =
    useState('')

  const [reason, setReason] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null)

  const currentStock = Number(product.stock)
  const numericChange = Number(quantityChange)

  const quantityIsValid =
    QUANTITY_PATTERN.test(quantityChange.trim()) &&
    Number.isFinite(numericChange) &&
    numericChange !== 0

  const trimmedReason = reason.trim()

  const reasonIsValid =
    trimmedReason.length >= 1 &&
    trimmedReason.length <= 500

  const projectedStock = useMemo(() => {
    if (
      !Number.isFinite(currentStock) ||
      !quantityIsValid
    ) {
      return null
    }

    return currentStock + numericChange
  }, [currentStock, numericChange, quantityIsValid])

  const projectedStockIsValid =
    projectedStock !== null && projectedStock >= 0

  const formIsValid =
    quantityIsValid &&
    reasonIsValid &&
    projectedStockIsValid

  async function handleSubmit(
    event: React.FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    setErrorMessage(null)

    if (!quantityIsValid) {
      setErrorMessage(
        'יש להזין שינוי שאינו אפס, עם עד שלוש ספרות אחרי הנקודה.',
      )
      return
    }

    if (!projectedStockIsValid) {
      setErrorMessage(
        'לא ניתן להפחית כמות גדולה מהמלאי הקיים.',
      )
      return
    }

    if (!reasonIsValid) {
      setErrorMessage(
        'יש להזין סיבה באורך של עד 500 תווים.',
      )
      return
    }

    setSubmitting(true)

    try {
      const adjustment =
        await createAdminInventoryAdjustment(
          product.id,
          {
            quantity_change: quantityChange.trim(),
            reason: trimmedReason,
          },
        )

      onAdjusted(adjustment)
    } catch (error) {
      if (
        error instanceof ApiError &&
        error.status === 401
      ) {
        onUnauthorized()
        return
      }

      setErrorMessage(createErrorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className="admin-inventory-dialog-backdrop"
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
        className="admin-inventory-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="admin-inventory-dialog-title"
      >
        <div className="admin-inventory-dialog-heading">
          <div>
            <span>התאמת מלאי ידנית</span>

            <h2 id="admin-inventory-dialog-title">
              {product.name}
            </h2>
          </div>

          <button
            type="button"
            className="admin-inventory-dialog-close"
            onClick={onClose}
            disabled={submitting}
            aria-label="סגירת חלון התאמת המלאי"
          >
            ×
          </button>
        </div>

        <form
          className="admin-inventory-form"
          onSubmit={(event) => void handleSubmit(event)}
        >
          <div className="admin-inventory-stock-summary">
            <div>
              <span>מלאי נוכחי</span>
              <strong>{formatStock(currentStock)}</strong>
            </div>

            <div>
              <span>מלאי לאחר השינוי</span>

              <strong
                className={
                  projectedStock !== null &&
                  projectedStock < 0
                    ? 'admin-inventory-negative-stock'
                    : undefined
                }
              >
                {projectedStock === null
                  ? '—'
                  : formatStock(projectedStock)}
              </strong>
            </div>
          </div>

          <label className="admin-inventory-field">
            <span>שינוי בכמות</span>

            <input
              type="number"
              inputMode="decimal"
              step="0.001"
              value={quantityChange}
              onChange={(event) => {
                setQuantityChange(event.target.value)
                setErrorMessage(null)
              }}
              disabled={submitting}
              placeholder="לדוגמה: 10.500 או ‎-3.000"
              autoFocus
              required
            />

            <small>
              מספר חיובי מוסיף למלאי ומספר שלילי מפחית
              ממנו.
            </small>
          </label>

          <label className="admin-inventory-field">
            <span>סיבת ההתאמה</span>

            <textarea
              value={reason}
              onChange={(event) => {
                setReason(event.target.value)
                setErrorMessage(null)
              }}
              disabled={submitting}
              maxLength={500}
              rows={4}
              placeholder="לדוגמה: קליטת משלוח, תיקון ספירה או סחורה פגומה"
              required
            />

            <small>
              {reason.length}/500 תווים
            </small>
          </label>

          {errorMessage && (
            <div
              className="admin-inventory-form-error"
              role="alert"
            >
              {errorMessage}
            </div>
          )}

          <div className="admin-inventory-form-actions">
            <button
              type="button"
              className="admin-inventory-cancel-button"
              onClick={onClose}
              disabled={submitting}
            >
              ביטול
            </button>

            <button
              type="submit"
              className="admin-inventory-submit-button"
              disabled={!formIsValid || submitting}
            >
              {submitting
                ? 'מעדכן מלאי...'
                : 'אישור התאמת מלאי'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

export default AdminInventoryDialog