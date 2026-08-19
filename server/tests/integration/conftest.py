"""Fixtures for MySQL integration tests."""

from collections.abc import Generator
from datetime import date
from decimal import Decimal
import os
from typing import Any

import pytest
from sqlalchemy import (
    create_engine,
    delete,
    text,
)
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.contract import Contract
from app.models.contract_price import ContractPrice
from app.models.customer import Customer
from app.models.enums import ContractType, UserRole
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.product import Product
from app.models.user import User

EXPECTED_TEST_DATABASE = "freshflow_b2b_test"
EXPECTED_ALEMBIC_REVISION = "28cccd78d28f"


def clean_database(engine: Engine) -> None:
    """Delete test rows in foreign-key-safe order."""

    with Session(engine) as session:
        try:
            session.execute(delete(OrderItem))
            session.execute(delete(Order))
            session.execute(delete(ContractPrice))
            session.execute(delete(Contract))
            session.execute(delete(User))
            session.execute(delete(Product))
            session.execute(delete(Category))
            session.execute(delete(Customer))

            session.commit()

        except Exception:
            session.rollback()
            raise


@pytest.fixture(scope="session")
def integration_engine() -> Generator[Engine, None, None]:
    """Create an engine that is allowed to use only the test DB."""

    database_url = os.getenv("TEST_DATABASE_URL")

    if not database_url:
        pytest.skip(
            "TEST_DATABASE_URL is not configured"
        )

    parsed_url = make_url(database_url)

    if parsed_url.database != EXPECTED_TEST_DATABASE:
        pytest.fail(
            "Integration tests may run only against "
            f"{EXPECTED_TEST_DATABASE!r}; "
            f"received {parsed_url.database!r}"
        )

    if not parsed_url.drivername.startswith("mysql"):
        pytest.fail(
            "Integration tests require a MySQL database"
        )

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    with engine.connect() as connection:
        current_revision = connection.scalar(
            text(
                "SELECT version_num "
                "FROM alembic_version"
            )
        )

    if current_revision != EXPECTED_ALEMBIC_REVISION:
        engine.dispose()

        pytest.fail(
            "Test database migration is not current: "
            f"expected {EXPECTED_ALEMBIC_REVISION}, "
            f"received {current_revision}"
        )

    clean_database(engine)

    try:
        yield engine
    finally:
        clean_database(engine)
        engine.dispose()


@pytest.fixture
def db_session(
    integration_engine: Engine,
) -> Generator[Session, None, None]:
    """Return a clean real MySQL session for one test."""

    clean_database(integration_engine)

    session = Session(
        integration_engine,
        autoflush=False,
        expire_on_commit=False,
    )

    try:
        yield session
    finally:
        session.close()
        clean_database(integration_engine)


@pytest.fixture
def order_scenario(
    db_session: Session,
) -> dict[str, Any]:
    """Insert the minimum data required for an order."""

    category = Category(
        name="Integration Test Vegetables",
        description="Category used only by tests",
        active=True,
    )

    customer = Customer(
        company_name="Integration Test Customer",
        phone="02-5550100",
        business_number="integration-test-001",
        active=True,
    )

    db_session.add_all([
        category,
        customer,
    ])

    db_session.flush()

    product = Product(
        category_id=category.id,
        name="Integration Test Tomatoes",
        description="Product used only by tests",
        default_price=Decimal("9.00"),
        stock=Decimal("10.000"),
        image_url=None,
        active=True,
    )

    user = User(
        customer_id=customer.id,
        name="Integration Test Manager",
        email="integration.manager@example.com",
        password_hash="not-a-real-password-hash",
        role=UserRole.CUSTOMER_MANAGER,
        active=True,
    )

    contract = Contract(
        customer_id=customer.id,
        contract_name="Integration Test Contract",
        contract_type=ContractType.CUSTOM,
        valid_from=date.today(),
        valid_until=None,
        active=True,
    )

    db_session.add_all([
        product,
        user,
        contract,
    ])

    db_session.flush()

    contract_price = ContractPrice(
        contract_id=contract.id,
        product_id=product.id,
        price=Decimal("7.50"),
    )

    db_session.add(contract_price)
    db_session.commit()

    return {
        "category_id": category.id,
        "customer_id": customer.id,
        "product_id": product.id,
        "user_id": user.id,
        "contract_id": contract.id,
        "contract_price_id": contract_price.id,
        "initial_stock": Decimal("10.000"),
        "contract_price": Decimal("7.50"),
        "default_price": Decimal("9.00"),
    }