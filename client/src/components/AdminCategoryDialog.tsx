import {
  useState,
  type FormEvent,
} from 'react'

import { createAdminCategory } from '../api/adminCatalog'
import { ApiError } from '../api/http'
import type { AdminCategory } from '../types/adminCatalog'
import './AdminCategoryDialog.css'

interface AdminCategoryDialogProps {
  onClose: () => void
  onCreated: (category: AdminCategory) => void
  onUnauthorized: () => void
}

function createErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      return 'פג תוקף ההתחברות.'
    }

    if (error.status === 403) {
      return 'אין הרשאה ליצור קטגוריה.'
    }

    if (error.status === 409) {
      return 'כבר קיימת קטגוריה בשם הזה.'
    }

    if (error.status === 422) {
      return 'פרטי הקטגוריה אינם תקינים.'
    }
  }

  return 'לא ניתן ליצור את הקטגוריה כרגע.'
}

function AdminCategoryDialog({
  onClose,
  onCreated,
  onUnauthorized,
}: AdminCategoryDialogProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
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

    if (!normalizedName) {
      setErrorMessage('חובה להזין שם קטגוריה.')
      return
    }

    setSubmitting(true)

    try {
      const category = await createAdminCategory({
        name: normalizedName,
        description: normalizedDescription || null,
        active,
      })

      onCreated(category)
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
        if (event.target === event.currentTarget) {
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
            <span>קטגוריה חדשה</span>

            <h2 id="admin-category-dialog-title">
              יצירת קטגוריה
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

            <span>
              הקטגוריה פעילה וניתן לשייך אליה מוצרים
            </span>
          </label>

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
                ? 'יוצר קטגוריה...'
                : 'יצירת קטגוריה'}
            </button>
          </div>
        </form>
      </section>
    </div>
  )
}

export default AdminCategoryDialog