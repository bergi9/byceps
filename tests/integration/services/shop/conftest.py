"""
:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

import pytest

from byceps.services.shop.cart.models import Cart
from byceps.services.shop.sequence import service as sequence_service
from byceps.services.shop.shop import service as shop_service
from byceps.services.user import command_service as user_command_service

from testfixtures.shop_order import create_orderer

from tests.helpers import create_user_with_detail


@pytest.fixture
def shop(email_config):
    shop = shop_service.create_shop('shop-01', 'Some Shop', email_config.id)
    yield shop
    shop_service.delete_shop(shop.id)


@pytest.fixture
def orderer():
    user = create_user_with_detail('Besteller')
    yield create_orderer(user)
    user_command_service.delete_account(user.id, user.id, 'clean up')


@pytest.fixture
def empty_cart() -> Cart:
    return Cart()


@pytest.fixture
def order_number_sequence(shop) -> None:
    sequence_service.create_order_number_sequence(shop.id, 'order-')
    yield
    sequence_service.delete_order_number_sequence(shop.id)