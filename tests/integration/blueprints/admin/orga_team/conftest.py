"""
:Copyright: 2006-2022 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask import Flask
import pytest

from byceps.services.user.transfer.models import User

from tests.helpers import log_in_user


@pytest.fixture(scope='package')
def orga_team_admin(make_admin) -> User:
    permission_ids = {
        'admin.access',
        'orga_team.administrate_memberships',
        'orga_team.create',
        'orga_team.delete',
        'orga_team.view',
    }
    admin = make_admin('OrgaTeamAdmin', permission_ids)
    log_in_user(admin.id)
    return admin


@pytest.fixture(scope='package')
def orga_team_admin_client(
    make_client, admin_app: Flask, orga_team_admin: User
):
    return make_client(admin_app, user_id=orga_team_admin.id)
