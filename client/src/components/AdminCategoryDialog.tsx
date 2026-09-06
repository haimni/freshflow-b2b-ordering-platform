import {
  useState,
  type FormEvent,
} from 'react'

import {
  createAdminCategory,
  updateAdminCategory,
} from '../api/adminCatalog'
import { ApiError } from '../api/http'
import type { AdminCategory } from '../types/adminCatalog'
import './AdminCategoryDialog.css'

interface AdminCategoryDialogProps {
  category?: AdminCategory
  onClose: () => void
  onCreated: (category: AdminCategory) => void
  onUpdated?: (category: AdminCategory) => void
  onUnauthorized: () => void
}

function createErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return 'פג תוקף ההתחברות.'
    }

    if (error.status === 403) {
      return 'אין הרשאה לבצע את הפעולה.'
    }

    if (error.status === 409) {
      if (
        error.message.includes(
          'Category has active products',
        )
      ) {
        return 'לא ניתן להשבית קטגוריה שיש בה מוצרים פעילים.'
      }

      return 'כבר קיימת קטגוריה בשם הזה.'
    }

    if (error.status === 404) {
      return 'הקטגוריה לא נמצאה.'
    }

    if (error.status === 422) {
      return 'פרטי הקטגוריה אינם תקינים.'
    }
  }

  return 'לא ניתן לשמור את הקטגוריה כרגע.'
}

function AdminCategoryDialog({
  category,
  onClose,
  onCreated,
  onUpdated,
  onUnauthorized,
}: AdminCategoryDialogProps) {
  const editing = category !== undefined

  const [name, setName] = useState(
    category?.name ?? '',
  )

  const [description, setDescription] = useState(
    category?.description ?? '',
  )

  const [active, setActive] = useState(
    category?.active ?? true,
  )

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

    if (!normalizedName) {
      setErrorMessage('חובה להזין שם קטגוריה.')
      return
    }

    setSubmitting(true)

    try {
      if (category) {
        const updatedCategory =
          await updateAdminCategory(category.id, {
            name: normalizedName,
            description: normalizedDescription || null,
            active,
          })

        onUpdated?.(updatedCategory)
      } else {
        const createdCategory =
          await createAdminCategory({
            name: normalizedName,
            description: normalizedDescription || null,
            active,
          })

        onCreated(createdCategory)
      }
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
      className="admin-category-dialog-backdrop"
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
        className="admin-category-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="admin-category-dialog-title"
      >
        <div className="admin-category-dialog-header">
          <div>
            <span>
              {editing
                ? 'עדכון קטגוריה'
                : 'קטגוריה חדשה'}
            </span>

            <h2 id="admin-category-dialog-title">
              {editing
                ? `עריכת ${category.name}`
                : 'יצירת קטגוריה'}
            </h2>
          </div>

          <button
            type="button"
            className="admin-category-dialog-close"
            onClick={onClose}
            disabled={submitting}
            aria-label="סגירת החלון"
          >
            ×
          </button>
        </div>

        <form
          className="admin-category-form"
          onSubmit={(event) => void handleSubmit(event)}
        >
          <label>
            <span>שם הקטגוריה</span>

            <input
              type="text"
              value={name}
              maxLength={120}
              autoFocus
              required
              disabled={submitting}
              onChange={(event) =>
                setName(event.target.value)
              }
            />
          </label>

          <label>
            <span>תיאור</span>

            <textarea
              value={description}
              rows={4}
              disabled={submitting}
              onChange={(event) =>
                setDescription(event.target.value)
              }
            />
          </label>

          <label className="admin-category-active-field">
            <input
              type="checkbox"
              checked={active}
              disabled={submitting}
              onChange={(event) =>
                setActive(event.target.checked)
              }
            />

            <span>הקטגוריה פעילה</span>
          </label>

          {editing && category.active && !active && (
            <p className="admin-category-form-warning">
              ניתן להשבית קטגוריה רק אם אין בה מוצרים
              פעילים.
            </p>
          )}

          {errorMessage && (
            <div
              className="admin-category-form-error"
              role="alert"
            >
              {errorMessage}
            </div>
          )}

          <div className="admin-category-form-actions">
            <button
              type="button"
              className="admin-category-cancel-button"
              onClick={onClose}
              disabled={submitting}
            >
              ביטול
            </button>

            <button
              type="submit"
              className="admin-category-submit-button"
              disabled={submitting}
            >
              {submitting
                ? 'שומר...'
                : editing
                  ? 'שמירת שינויים'
                  : 'יצירת קטגוריה'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

export default AdminCategoryDialog