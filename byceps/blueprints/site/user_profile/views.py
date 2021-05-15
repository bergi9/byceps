"""
byceps.blueprints.site.user_profile.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2021 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from operator import attrgetter

from flask import abort, g

from ....services.orga_team import service as orga_team_service
from ....services.ticketing import attendance_service, ticket_service
from ....services.user import service as user_service
from ....services.user_badge import awarding_service as badge_awarding_service
from ....util.framework.blueprint import create_blueprint
from ....util.framework.templating import templated


blueprint = create_blueprint('user_profile', __name__)


@blueprint.get('/<uuid:user_id>')
@templated
def view(user_id):
    """Show a user's profile."""
    user = user_service.find_active_user(user_id, include_avatar=True)
    if user is None:
        abort(404)

    badges_with_awarding_quantity = (
        badge_awarding_service.get_badges_awarded_to_user(user.id)
    )

    orga_team = orga_team_service.find_orga_team_for_user_and_party(
        user.id, g.party_id
    )

    _current_party_tickets = ticket_service.find_tickets_used_by_user(
        user.id, g.party_id
    )
    current_party_tickets = [t for t in _current_party_tickets if not t.revoked]

    attended_parties = attendance_service.get_attended_parties(user.id)
    attended_parties.sort(key=attrgetter('starts_at'), reverse=True)

    return {
        'user': user,
        'badges_with_awarding_quantity': badges_with_awarding_quantity,
        'orga_team': orga_team,
        'current_party_tickets': current_party_tickets,
        'attended_parties': attended_parties,
    }
