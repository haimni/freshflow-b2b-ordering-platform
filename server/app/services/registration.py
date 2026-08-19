"""Transactional customer self-registration."""

from datetime import date

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models.contract import Contract
from app.models.customer import Customer
from app.models.enums import ContractType, UserRole
from app.models.user import User


class RegistrationConflictError(Exception):
    """Raised when unique registration data already exists."""


def register_customer(
    db: Session,
    *,
    company_name: str,
    business_number: str,
    phone: str | None,
    name: str,
    email: str,
    password: str,
) -> User:
    """Create a customer, manager and default contract atomically."""

    customer = Customer(
        company_name=company_name,
        business_number=business_number,
        phone=phone,
        active=True,
    )

    try:
        db.add(customer)
        db.flush()

        user = User(
            customer_id=customer.id,
            name=name,
            email=email,
            password_hash=hash_password(password),
            role=UserRole.CUSTOMER_MANAGER,
            active=True,
        )

        default_contract = Contract(
            customer_id=customer.id,
            contract_name="Default pricing contract",
            contract_type=ContractType.DEFAULT,
            valid_from=date.today(),
            valid_until=None,
            active=True,
        )

        db.add_all([
            user,
            default_contract,
        ])

        db.commit()
        db.refresh(user)

        return user

    except IntegrityError as error:
        db.rollback()

        raise RegistrationConflictError(
            "Email or business number already exists"
        ) from error

    except Exception:
        db.rollback()
        raise