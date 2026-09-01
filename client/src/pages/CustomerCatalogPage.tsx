import {
  useCallback,
  useEffect,
  useState,
} from 'react'

import { getCustomerProducts } from '../api/customerCatalog'
import { createCustomerOrder } from '../api/customerOrders'
import { ApiError } from '../api/http'
import CartPanel from '../components/CartPanel'
import type { CartItem } from '../types/cart'
import type { CustomerProduct } from '../types/catalog'
import type { CustomerOrder } from '../types/order'
import './CustomerCatalogPage.css'

interface CustomerCatalogPageProps {
  onUnauthorized: () => void
}

type CatalogState =
  | { status: 'loading' }
  | { status: 'loaded'; products: CustomerProduct[] }
  | { status: 'error'; message: string }

function formatPrice(price: string): string {
  const numericPrice = Number(price)

  if (!Number.isFinite(numericPrice)) {
    return price
  }

  return new Intl.NumberFormat('he-IL', {
    style: 'currency',
    currency: 'ILS',
    minimumFractionDigits: 2,
  }).format(numericPrice)
}

function formatStock(stock: string): string {
  const numericStock = Number(stock)

  if (!Number.isFinite(numericStock)) {
    return stock
  }

  return new Intl.NumberFormat('he-IL', {
    maximumFractionDigits: 3,
  }).format(numericStock)
}

function createOrderErrorMessage(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'לא ניתן לשלוח את ההזמנה כרגע.'
  }

  if (error.status === 404) {
    return 'אחד המוצרים אינו זמין יותר.'
  }

  if (error.status === 409) {
    if (
      error.message.includes(
        'A current contract is required',
      )
    ) {
      return 'לא נמצא חוזה פעיל. לא ניתן לבצע הזמנה.'
    }

    if (
      error.message.includes(
        'Multiple current contracts found',
      )
    ) {
      return 'נמצאו מספר חוזים פעילים. יש לפנות למנהל.'
    }

    if (error.message.includes('Insufficient stock')) {
      return 'המלאי השתנה ואין כמות מספקת לאחד המוצרים.'
    }

    return 'לא ניתן ליצור את ההזמנה במצבה הנוכחי.'
  }

  if (error.status === 422) {
    return 'פרטי ההזמנה אינם תקינים.'
  }

  return 'לא ניתן לשלוח את ההזמנה כרגע.'
}

function CustomerCatalogPage({
  onUnauthorized,
}: CustomerCatalogPageProps) {
  const [catalog, setCatalog] = useState<CatalogState>({
    status: 'loading',
  })

  const [cartItems, setCartItems] = useState<CartItem[]>([])
  const [submitting, setSubmitting] = useState(false)

  const [orderError, setOrderError] = useState<string | null>(
    null,
  )

  const [createdOrder, setCreatedOrder] =
    useState<CustomerOrder | null>(null)

  const loadCatalog = useCallback(async () => {
    try {
      const products = await getCustomerProducts()

      setCatalog({
        status: 'loaded',
        products,
      })
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onUnauthorized()
        return
      }

      if (error instanceof ApiError && error.status === 409) {
        setCatalog({
          status: 'error',
          message:
            'נמצאו מספר חוזים פעילים. יש לפנות למנהל המערכת.',
        })
        return
      }

      setCatalog({
        status: 'error',
        message: 'לא ניתן לטעון את הקטלוג כרגע.',
      })
    }
  }, [onUnauthorized])

  useEffect(() => {
    let active = true

    getCustomerProducts()
      .then((products) => {
        if (!active) {
          return
        }

        setCatalog({
          status: 'loaded',
          products,
        })
      })
      .catch((error: unknown) => {
        if (!active) {
          return
        }

        if (error instanceof ApiError && error.status === 401) {
          onUnauthorized()
          return
        }

        if (error instanceof ApiError && error.status === 409) {
          setCatalog({
            status: 'error',
            message:
              'נמצאו מספר חוזים פעילים. יש לפנות למנהל המערכת.',
          })
          return
        }

        setCatalog({
          status: 'error',
          message: 'לא ניתן לטעון את הקטלוג כרגע.',
        })
      })

    return () => {
      active = false
    }
  }, [onUnauthorized])

  function addProductToCart(product: CustomerProduct) {
    setOrderError(null)
    setCreatedOrder(null)

    setCartItems((currentItems) => {
      const productAlreadyExists = currentItems.some(
        (item) => item.product.id === product.id,
      )

      if (productAlreadyExists) {
        return currentItems
      }

      const availableStock = Number(product.stock)
      const initialQuantity = Math.min(1, availableStock)

      return [
        ...currentItems,
        {
          product,
          quantity: initialQuantity.toFixed(3),
        },
      ]
    })
  }

  function updateCartQuantity(
    productId: number,
    quantity: string,
  ) {
    setOrderError(null)
    setCreatedOrder(null)

    setCartItems((currentItems) =>
      currentItems.map((item) =>
        item.product.id === productId
          ? {
              ...item,
              quantity,
            }
          : item,
      ),
    )
  }

  function removeCartItem(productId: number) {
    setOrderError(null)
    setCreatedOrder(null)

    setCartItems((currentItems) =>
      currentItems.filter(
        (item) => item.product.id !== productId,
      ),
    )
  }

  async function submitOrder() {
    setOrderError(null)
    setCreatedOrder(null)

    if (cartItems.length === 0) {
      setOrderError('הסל ריק.')
      return
    }

    const invalidItem = cartItems.find((item) => {
      const quantity = Number(item.quantity)
      const stock = Number(item.product.stock)

      return (
        !Number.isFinite(quantity) ||
        quantity <= 0 ||
        quantity > stock
      )
    })

    if (invalidItem) {
      setOrderError(
        `הכמות שנבחרה עבור ${invalidItem.product.name} אינה תקינה.`,
      )
      return
    }

    setSubmitting(true)

    try {
      const order = await createCustomerOrder({
        items: cartItems.map((item) => ({
          product_id: item.product.id,
          quantity: Number(item.quantity).toFixed(3),
        })),
      })

      setCreatedOrder(order)
      setCartItems([])

      await loadCatalog()
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        onUnauthorized()
        return
      }

      setOrderError(createOrderErrorMessage(error))
    } finally {
      setSubmitting(false)
    }
  }

  const loadedProducts =
    catalog.status === 'loaded' ? catalog.products : []

  return (
    <section className="catalog-page">
      <div className="catalog-heading">
        <div>
          <span className="catalog-eyebrow">
            הקטלוג האישי שלך
          </span>

          <h1>מוצרים להזמנה</h1>

          <p>
            המחירים המוצגים מותאמים לחוזה הפעיל של העסק.
          </p>
        </div>

        {catalog.status === 'loaded' && (
          <span className="catalog-count">
            {catalog.products.length} מוצרים
          </span>
        )}
      </div>

      {createdOrder && (
        <div className="order-success" role="status">
          <div>
            <strong>ההזמנה נוצרה בהצלחה</strong>

            <span>
              הזמנה מספר {createdOrder.id} נוצרה במצב
              ממתינה לאישור.
            </span>
          </div>

          <strong className="order-success-total">
            {formatPrice(createdOrder.total)}
          </strong>
        </div>
      )}

      <div className="catalog-layout">
        <div className="catalog-products">
          {catalog.status === 'loading' && (
            <div className="catalog-message" role="status">
              <span className="catalog-spinner" />
              טוען מוצרים ומחירים...
            </div>
          )}

          {catalog.status === 'error' && (
            <div className="catalog-error" role="alert">
              <strong>טעינת הקטלוג נכשלה</strong>
              <span>{catalog.message}</span>

              <button
                type="button"
                className="catalog-retry"
                onClick={() => {
                  setCatalog({ status: 'loading' })
                  void loadCatalog()
                }}
              >
                ניסיון נוסף
              </button>
            </div>
          )}

          {catalog.status === 'loaded' &&
            catalog.products.length === 0 && (
              <div className="catalog-message">
                אין כרגע מוצרים פעילים להצגה.
              </div>
            )}

          {catalog.status === 'loaded' &&
            catalog.products.length > 0 && (
              <div className="product-grid">
                {catalog.products.map((product) => {
                  const productInCart = cartItems.some(
                    (item) =>
                      item.product.id === product.id,
                  )

                  const productAvailable =
                    Number(product.stock) > 0

                  return (
                    <article
                      className="product-card"
                      key={product.id}
                    >
                      <div className="product-image">
                        {product.image_url ? (
                          <img
                            src={product.image_url}
                            alt={product.name}
                          />
                        ) : (
                          <span
                            role="img"
                            aria-label="מוצר טרי"
                          >
                            🥬
                          </span>
                        )}
                      </div>

                      <div className="product-content">
                        <div className="product-header">
                          <h2>{product.name}</h2>

                          <span
                            className={`stock-badge ${
                              productAvailable
                                ? 'stock-badge--available'
                                : 'stock-badge--empty'
                            }`}
                          >
                            {productAvailable
                              ? `במלאי: ${formatStock(
                                  product.stock,
                                )}`
                              : 'אזל מהמלאי'}
                          </span>
                        </div>

                        <p className="product-description">
                          {product.description ??
                            'לא קיים תיאור למוצר זה.'}
                        </p>

                        <div className="product-footer">
                          <div>
                            <span className="price-label">
                              מחיר ליחידה
                            </span>

                            <strong className="product-price">
                              {formatPrice(
                                product.effective_price,
                              )}
                            </strong>
                          </div>

                          <span
                            className={`price-source price-source--${product.price_source}`}
                          >
                            {product.price_source ===
                            'contract'
                              ? 'מחיר חוזה'
                              : 'מחיר רגיל'}
                          </span>
                        </div>

                        <button
                          type="button"
                          className="add-product-button"
                          onClick={() =>
                            addProductToCart(product)
                          }
                          disabled={
                            !productAvailable ||
                            productInCart ||
                            submitting
                          }
                        >
                          {!productAvailable
                            ? 'לא זמין'
                            : productInCart
                              ? 'נמצא בסל'
                              : 'הוספה להזמנה'}
                        </button>
                      </div>
                    </article>
                  )
                })}
              </div>
            )}
        </div>

        <CartPanel
          items={cartItems}
          submitting={submitting}
          errorMessage={orderError}
          onQuantityChange={updateCartQuantity}
          onRemove={removeCartItem}
          onSubmit={() => void submitOrder()}
        />
      </div>

      {catalog.status === 'loaded' &&
        loadedProducts.length > 0 && (
          <p className="catalog-server-note">
            המחירים, המלאי והסכום הסופי מחושבים ומאומתים
            מחדש בשרת בעת יצירת ההזמנה.
          </p>
        )}
    </section>
  )
}

export default CustomerCatalogPage