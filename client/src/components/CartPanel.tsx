import type { CartItem } from '../types/cart'
import './CartPanel.css'

interface CartPanelProps {
  items: CartItem[]
  submitting: boolean
  errorMessage: string | null
  onQuantityChange: (
    productId: number,
    quantity: string,
  ) => void
  onRemove: (productId: number) => void
  onSubmit: () => void
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('he-IL', {
    style: 'currency',
    currency: 'ILS',
    minimumFractionDigits: 2,
  }).format(value)
}

function quantityIsValid(item: CartItem): boolean {
  const quantity = Number(item.quantity)
  const stock = Number(item.product.stock)

  return (
    Number.isFinite(quantity) &&
    quantity > 0 &&
    quantity <= stock
  )
}

function CartPanel({
  items,
  submitting,
  errorMessage,
  onQuantityChange,
  onRemove,
  onSubmit,
}: CartPanelProps) {
  const estimatedTotal = items.reduce(
    (total, item) =>
      total +
      Number(item.quantity) *
        Number(item.product.effective_price),
    0,
  )

  const cartIsValid =
    items.length > 0 && items.every(quantityIsValid)

  return (
    <aside className="cart-panel" aria-label="סל הזמנה">
      <div className="cart-heading">
        <div>
          <span className="cart-eyebrow">ההזמנה שלך</span>
          <h2>סל קניות</h2>
        </div>

        <span className="cart-count">{items.length}</span>
      </div>

      {items.length === 0 ? (
        <div className="cart-empty">
          <span className="cart-empty-icon">🛒</span>
          <strong>הסל עדיין ריק</strong>
          <p>הוסף מוצרים מהקטלוג כדי להתחיל הזמנה.</p>
        </div>
      ) : (
        <>
          <div className="cart-items">
            {items.map((item) => {
              const quantityValid = quantityIsValid(item)

              return (
                <article
                  className="cart-item"
                  key={item.product.id}
                >
                  <div className="cart-item-heading">
                    <div>
                      <strong>{item.product.name}</strong>

                      <span>
                        {formatCurrency(
                          Number(
                            item.product.effective_price,
                          ),
                        )}{' '}
                        ליחידה
                      </span>
                    </div>

                    <button
                      type="button"
                      className="cart-remove"
                      onClick={() =>
                        onRemove(item.product.id)
                      }
                      disabled={submitting}
                      aria-label={`הסרת ${item.product.name} מהסל`}
                    >
                      ×
                    </button>
                  </div>

                  <label className="cart-quantity">
                    <span>כמות</span>

                    <input
                      type="number"
                      min="0.001"
                      max={item.product.stock}
                      step="0.001"
                      value={item.quantity}
                      onChange={(event) =>
                        onQuantityChange(
                          item.product.id,
                          event.target.value,
                        )
                      }
                      disabled={submitting}
                      aria-invalid={!quantityValid}
                    />
                  </label>

                  {!quantityValid && (
                    <p className="cart-quantity-error">
                      הכמות חייבת להיות גדולה מאפס ולא
                      לחרוג מהמלאי הזמין.
                    </p>
                  )}

                  <div className="cart-line-total">
                    <span>סכום משוער</span>

                    <strong>
                      {formatCurrency(
                        Number(item.quantity) *
                          Number(
                            item.product.effective_price,
                          ),
                      )}
                    </strong>
                  </div>
                </article>
              )
            })}
          </div>

          <div className="cart-summary">
            <span>סה״כ משוער</span>
            <strong>
              {formatCurrency(
                Number.isFinite(estimatedTotal)
                  ? estimatedTotal
                  : 0,
              )}
            </strong>
          </div>

          {errorMessage && (
            <div className="cart-error" role="alert">
              {errorMessage}
            </div>
          )}

          <button
            type="button"
            className="cart-submit"
            onClick={onSubmit}
            disabled={!cartIsValid || submitting}
          >
            {submitting
              ? 'שולח הזמנה...'
              : 'שליחת הזמנה'}
          </button>

          <p className="cart-disclaimer">
            הסכום הסופי, המחירים והמלאי יאומתו בשרת בעת
            שליחת ההזמנה.
          </p>
        </>
      )}
    </aside>
  )
}

export default CartPanel