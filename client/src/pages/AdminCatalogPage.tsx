import { useEffect, useMemo, useState } from 'react'

import {
  getAdminCategories,
  getAdminProducts,
} from '../api/adminCatalog'
import { ApiError } from '../api/http'
import type {
  AdminCategory,
  AdminProduct,
} from '../types/adminCatalog'
import './AdminCatalogPage.css'

interface AdminCatalogPageProps {
  onUnauthorized: () => void
}

type CatalogState =
  | { status: 'loading' }
  | {
      status: 'loaded'
      categories: AdminCategory[]
      products: AdminProduct[]
    }
  | { status: 'error'; message: string }

type ActiveFilter = 'all' | 'active' | 'inactive'

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

function formatStock(value: string): string {
  const numericValue = Number(value)

  if (!Number.isFinite(numericValue)) {
    return value
  }

  return new Intl.NumberFormat('he-IL', {
    maximumFractionDigits: 3,
  }).format(numericValue)
}

function createLoadErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 403) {
    return 'אין הרשאה לצפות בקטלוג הניהולי.'
  }

  return 'לא ניתן לטעון את הקטלוג כרגע.'
}

function AdminCatalogPage({
  onUnauthorized,
}: AdminCatalogPageProps) {
  const [catalogState, setCatalogState] =
    useState<CatalogState>({
      status: 'loading',
    })

  const [categoryFilter, setCategoryFilter] =
    useState<number | 'all'>('all')

  const [activeFilter, setActiveFilter] =
    useState<ActiveFilter>('all')

  useEffect(() => {
    let active = true

    Promise.all([
      getAdminCategories(),
      getAdminProducts(),
    ])
      .then(([categories, products]) => {
        if (active) {
          setCatalogState({
            status: 'loaded',
            categories,
            products,
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

        setCatalogState({
          status: 'error',
          message: createLoadErrorMessage(error),
        })
      })

    return () => {
      active = false
    }
  }, [onUnauthorized])

  const filteredProducts = useMemo(() => {
    if (catalogState.status !== 'loaded') {
      return []
    }

    return catalogState.products.filter((product) => {
      const matchesCategory =
        categoryFilter === 'all' ||
        product.category_id === categoryFilter

      const matchesActiveState =
        activeFilter === 'all' ||
        (activeFilter === 'active'
          ? product.active
          : !product.active)

      return matchesCategory && matchesActiveState
    })
  }, [activeFilter, catalogState, categoryFilter])

  const categoryNames = useMemo(() => {
    if (catalogState.status !== 'loaded') {
      return new Map<number, string>()
    }

    return new Map(
      catalogState.categories.map((category) => [
        category.id,
        category.name,
      ]),
    )
  }, [catalogState])

  return (
    <section className="admin-catalog-page">
      <div className="admin-catalog-heading">
        <div>
          <span className="admin-catalog-eyebrow">
            ממשק מנהל
          </span>

          <h1>ניהול קטלוג</h1>

          <p>
            צפייה במוצרים, קטגוריות, מחירים ומלאי.
          </p>
        </div>

        {catalogState.status === 'loaded' && (
          <div className="admin-catalog-counters">
            <span>
              {catalogState.categories.length} קטגוריות
            </span>

            <span>
              {catalogState.products.length} מוצרים
            </span>
          </div>
        )}
      </div>

      {catalogState.status === 'loading' && (
        <div className="admin-catalog-message" role="status">
          טוען קטלוג...
        </div>
      )}

      {catalogState.status === 'error' && (
        <div className="admin-catalog-error" role="alert">
          {catalogState.message}
        </div>
      )}

      {catalogState.status === 'loaded' && (
        <>
          <section className="admin-category-section">
            <div className="admin-section-heading">
              <div>
                <span>מבנה הקטלוג</span>
                <h2>קטגוריות</h2>
              </div>
            </div>

            {catalogState.categories.length === 0 ? (
              <div className="admin-catalog-message">
                עדיין לא נוצרו קטגוריות.
              </div>
            ) : (
              <div className="admin-category-grid">
                {catalogState.categories.map((category) => (
                  <article
                    className="admin-category-card"
                    key={category.id}
                  >
                    <div>
                      <strong>{category.name}</strong>

                      <span>
                        {category.description ??
                          'ללא תיאור'}
                      </span>
                    </div>

                    <span
                      className={
                        category.active
                          ? 'admin-catalog-state admin-catalog-state--active'
                          : 'admin-catalog-state admin-catalog-state--inactive'
                      }
                    >
                      {category.active
                        ? 'פעילה'
                        : 'מושבתת'}
                    </span>
                  </article>
                ))}
              </div>
            )}
          </section>

          <section className="admin-product-section">
            <div className="admin-section-heading">
              <div>
                <span>מלאי ומחירים</span>
                <h2>מוצרים</h2>
              </div>

              <span className="admin-filter-result">
                {filteredProducts.length} תוצאות
              </span>
            </div>

            <div className="admin-catalog-filters">
              <label>
                <span>קטגוריה</span>

                <select
                  value={categoryFilter}
                  onChange={(event) => {
                    const value = event.target.value

                    setCategoryFilter(
                      value === 'all'
                        ? 'all'
                        : Number(value),
                    )
                  }}
                >
                  <option value="all">
                    כל הקטגוריות
                  </option>

                  {catalogState.categories.map(
                    (category) => (
                      <option
                        value={category.id}
                        key={category.id}
                      >
                        {category.name}
                      </option>
                    ),
                  )}
                </select>
              </label>

              <div
                className="admin-active-filter"
                aria-label="סינון לפי מצב מוצר"
              >
                {(
                  [
                    ['all', 'הכול'],
                    ['active', 'פעילים'],
                    ['inactive', 'מושבתים'],
                  ] as const
                ).map(([value, label]) => (
                  <button
                    type="button"
                    key={value}
                    className={
                      activeFilter === value
                        ? 'admin-active-filter-button admin-active-filter-button--selected'
                        : 'admin-active-filter-button'
                    }
                    aria-pressed={
                      activeFilter === value
                    }
                    onClick={() =>
                      setActiveFilter(value)
                    }
                  >
                    {label}
                  </button>
                ))}
              </div>
            </div>

            {filteredProducts.length === 0 ? (
              <div className="admin-catalog-message">
                אין מוצרים התואמים לסינון שנבחר.
              </div>
            ) : (
              <div className="admin-product-grid">
                {filteredProducts.map((product) => (
                  <article
                    className="admin-product-card"
                    key={product.id}
                  >
                    <div className="admin-product-image">
                      {product.image_url ? (
                        <img
                          src={product.image_url}
                          alt={product.name}
                        />
                      ) : (
                        <span
                          role="img"
                          aria-label="מוצר ללא תמונה"
                        >
                          🥬
                        </span>
                      )}
                    </div>

                    <div className="admin-product-content">
                      <div className="admin-product-title">
                        <div>
                          <strong>{product.name}</strong>

                          <span>
                            {categoryNames.get(
                              product.category_id,
                            ) ?? 'קטגוריה לא ידועה'}
                          </span>
                        </div>

                        <span
                          className={
                            product.active
                              ? 'admin-catalog-state admin-catalog-state--active'
                              : 'admin-catalog-state admin-catalog-state--inactive'
                          }
                        >
                          {product.active
                            ? 'פעיל'
                            : 'מושבת'}
                        </span>
                      </div>

                      <p>
                        {product.description ??
                          'ללא תיאור מוצר.'}
                      </p>

                      <div className="admin-product-metrics">
                        <div>
                          <span>מחיר רגיל</span>
                          <strong>
                            {formatCurrency(
                              product.default_price,
                            )}
                          </strong>
                        </div>

                        <div>
                          <span>מלאי נוכחי</span>
                          <strong>
                            {formatStock(product.stock)}
                          </strong>
                        </div>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </section>
  )
}

export default AdminCatalogPage