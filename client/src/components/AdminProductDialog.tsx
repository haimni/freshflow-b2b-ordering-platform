import {
  useState,
  type FormEvent,
} from 'react'

import { createAdminProduct } from '../api/adminCatalog'
import { ApiError } from '../api/http'
import type {
  AdminCategory,
  AdminProduct,
} from '../types/adminCatalog'
import './AdminProductDialog.css'

interface AdminProductDialogProps {
  categories: AdminCategory[]
  onClose: () => void
  onCreated: (product: AdminProduct) => void
  onUnauthorized: () => void
}

const PRICE_PATTERN = /^\d{1,8}(\.\d{1,2})?$/
const STOCK_PATTERN = /^\d{1,9}(\.\d{1,3})?$/

function createErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return 'פג תוקף ההתחברות.'
    }

    if (error.status === 403) {
      return 'אין הרשאה ליצור מוצר.'
    }

    if (error.status === 404) {
      return 'הקטגוריה שנבחרה אינה קיימת.'
    }

    if (error.status === 409) {
      return 'לא ניתן להפעיל מוצר תחת קטגוריה מושבתת.'
    }

    if (error.status === 422) {
      return 'פרטי המוצר אינם תקינים.'
    }
  }

  return 'לא ניתן ליצור את המוצר כרגע.'
}

function AdminProductDialog({
  categories,
  onClose,
  onCreated,
  onUnauthorized,
}: AdminProductDialogProps) {
  const initialCategory =
    categories.find((category) => category.active) ??
    categories[0]

  const [categoryId, setCategoryId] = useState(
    initialCategory?.id ?? 0,
  )

  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [defaultPrice, setDefaultPrice] = useState('')
  const [stock, setStock] = useState('0.000')
  const [imageUrl, setImageUrl] = useState('')
  const [active, setActive] = useState(true)
  const [submitting, setSubmitting] = useState(false)

  const [errorMessage, setErrorMessage] =
    useState<string | null>(null)

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    setErrorMessage(null)

    const normalizedName = name.trim()
    const normalizedDescription = description.trim()
    const normalizedPrice = defaultPrice.trim()
    const normalizedStock = stock.trim()
    const normalizedImageUrl = imageUrl.trim()

    if (!normalizedName) {
      setErrorMessage('חובה להזין שם מוצר.')
      return
    }

    const selectedCategory = categories.find(
      (category) => category.id === categoryId,
    )

    if (!selectedCategory) {
      setErrorMessage('חובה לבחור קטגוריה קיימת.')
      return
    }

    if (active && !selectedCategory.active) {
      setErrorMessage(
        'לא ניתן להפעיל מוצר תחת קטגוריה מושבתת.',
      )
      return
    }

    if (!PRICE_PATTERN.test(normalizedPrice)) {
      setErrorMessage(
        'המחיר חייב להיות מספר שאינו שלילי, עם עד שתי ספרות אחרי הנקודה.',
      )
      return
    }

    if (!STOCK_PATTERN.test(normalizedStock)) {
      setErrorMessage(
        'המלאי חייב להיות מספר שאינו שלילי, עם עד שלוש ספרות אחרי הנקודה.',
      )
      return
    }

    setSubmitting(true)

    try {
      const product = await createAdminProduct({
        category_id: categoryId,
        name: normalizedName,
        description: normalizedDescription || null,
        default_price: normalizedPrice,
        stock: normalizedStock,
        image_url: normalizedImageUrl || null,
        active,
      })

      onCreated(product)
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
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
      className="admin-product-dialog-backdrop"
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
        className="admin-product-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="admin-product-dialog-title"
      >
        <div className="admin-product-dialog-header">
          <div>
            <span>מוצר חדש</span>

            <h2 id="admin-product-dialog-title">
              יצירת מוצר
            </h2>
          </div>

          <button
            type="button"
            className="admin-product-dialog-close"
            onClick={onClose}
            disabled={submitting}
            aria-label="סגירת החלון"
          >
            ×
          </button>
        </div>

        <form
          className="admin-product-form"
          onSubmit={(event) => void handleSubmit(event)}
        >
          <div className="admin-product-form-grid">
            <label>
              <span>שם המוצר</span>

              <input
                type="text"
                value={name}
                maxLength={150}
                autoFocus
                required
                disabled={submitting}
                onChange={(event) =>
                  setName(event.target.value)
                }
              />
            </label>

            <label>
              <span>קטגוריה</span>

              <select
                value={categoryId}
                required
                disabled={
                  submitting || categories.length === 0
                }
                onChange={(event) =>
                  setCategoryId(
                    Number(event.target.value),
                  )
                }
              >
                {categories.length === 0 && (
                  <option value={0}>
                    אין קטגוריות זמינות
                  </option>
                )}

                {categories.map((category) => (
                  <option
                    value={category.id}
                    key={category.id}
                  >
                    {category.name}
                    {category.active
                      ? ''
                      : ' — מושבתת'}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>מחיר רגיל</span>

              <input
                type="text"
                inputMode="decimal"
                value={defaultPrice}
                placeholder="0.00"
                required
                disabled={submitting}
                onChange={(event) =>
                  setDefaultPrice(event.target.value)
                }
              />
            </label>

            <label>
              <span>מלאי התחלתי</span>

              <input
                type="text"
                inputMode="decimal"
                value={stock}
                placeholder="0.000"
                required
                disabled={submitting}
                onChange={(event) =>
                  setStock(event.target.value)
                }
              />
            </label>
          </div>

          <label>
            <span>תיאור המוצר</span>

            <textarea
              value={description}
              rows={3}
              disabled={submitting}
              onChange={(event) =>
                setDescription(event.target.value)
              }
            />
          </label>

          <label>
            <span>כתובת תמונה</span>

            <input
              type="url"
              value={imageUrl}
              maxLength={2048}
              placeholder="https://example.com/product.jpg"
              disabled={submitting}
              onChange={(event) =>
                setImageUrl(event.target.value)
              }
            />
          </label>

          <label className="admin-product-active-field">
            <input
              type="checkbox"
              checked={active}
              disabled={submitting}
              onChange={(event) =>
                setActive(event.target.checked)
              }
            />

            <span>
              המוצר פעיל ומוצג ללקוחות מורשים
            </span>
          </label>

          {errorMessage && (
            <div
              className="admin-product-form-error"
              role="alert"
            >
              {errorMessage}
            </div>
          )}

          <div className="admin-product-form-actions">
            <button
              type="button"
              className="admin-product-cancel-button"
              onClick={onClose}
              disabled={submitting}
            >
              ביטול
            </button>

            <button
              type="submit"
              className="admin-product-submit-button"
              disabled={
                submitting || categories.length === 0
              }
            >
              {submitting
                ? 'יוצר מוצר...'
                : 'יצירת מוצר'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

export default AdminProductDialog