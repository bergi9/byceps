"""
:Copyright: 2006-2021 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

import pytest

from byceps.services.authorization import service as authorization_service
from byceps.services.user import service as user_service
from byceps.services.verification_token import (
    service as verification_token_service,
)

from tests.helpers import http_client


@pytest.fixture(scope='module')
def user1(make_user):
    return make_user('EAC-User1', initialized=False)


@pytest.fixture(scope='module')
def user2(make_user):
    return make_user('EAC-User2', initialized=False)


@pytest.fixture
def role(admin_app, site, user1, user2):
    role = authorization_service.create_role('board_user', 'Board User')

    yield role

    for user in user1, user2:
        authorization_service.deassign_all_roles_from_user(user.id)

    authorization_service.delete_role(role.id)


def test_confirm_email_address_with_valid_token(site_app, user1, role):
    user_id = user1.id

    user_before = user_service.get_db_user(user_id)
    assert not user_before.email_address_verified
    assert not user_before.initialized

    token = create_confirmation_token(user_id)

    # -------------------------------- #

    response = confirm(site_app, token)

    # -------------------------------- #

    assert response.status_code == 302

    user_after = user_service.get_db_user(user_id)
    assert user_before.email_address_verified
    assert user_after.initialized

    assert get_role_ids(user_id) == {'board_user'}


def test_confirm_email_address_with_unknown_token(site_app, site, user2, role):
    user_id = user2.id

    user_before = user_service.get_db_user(user_id)
    assert not user_before.initialized

    unknown_token = 'wZdSLzkT-zRf2x2T6AR7yGa3Nc_X3Nn3F3XGPvPtOhw'

    # -------------------------------- #

    response = confirm(site_app, unknown_token)

    # -------------------------------- #

    assert response.status_code == 404

    user_after = user_service.get_db_user(user_id)
    assert not user_after.initialized

    assert get_role_ids(user_id) == set()


# helpers


def confirm(app, token):
    url = f'/users/email_address/confirmation/{token}'
    with http_client(app) as client:
        return client.get(url)


def get_role_ids(user_id):
    return authorization_service.find_role_ids_for_user(user_id)


def create_confirmation_token(user_id):
    token = verification_token_service.create_for_email_address_confirmation(
        user_id
    )
    return token.token
