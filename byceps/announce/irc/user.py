"""
byceps.announce.irc.user
~~~~~~~~~~~~~~~~~~~~~~~~

Announce user events on IRC.

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from ...blueprints.user import signals
from ...events.user import (
    UserAccountCreated,
    UserAccountDeleted,
    UserAccountSuspended,
    UserAccountUnsuspended,
    UserDetailsUpdated,
    UserEmailAddressInvalidated,
    UserScreenNameChanged,
)
from ...services.user import service as user_service
from ...util.irc import send_message
from ...util.jobqueue import enqueue

from ._config import CHANNEL_ORGA_LOG, CHANNEL_PUBLIC


@signals.account_created.connect
def _on_user_account_created(sender, *, event: UserAccountCreated) -> None:
    enqueue(announce_user_account_created, event)


def announce_user_account_created(event: UserAccountCreated) -> None:
    """Announce that a user account has been created."""
    channels = [CHANNEL_ORGA_LOG]

    user = user_service.find_user(event.user_id)

    if event.initiator_id is not None:
        initiator = user_service.find_user(event.initiator_id)
        initiator_label = initiator.screen_name
    else:
        initiator_label = 'Jemand'

    text = (
        f'{initiator_label} '
        f'hat das Benutzerkonto "{user.screen_name}" angelegt.'
    )

    send_message(channels, text)


@signals.screen_name_changed.connect
def _on_user_screen_name_changed(
    sender, *, event: UserScreenNameChanged
) -> None:
    enqueue(announce_user_screen_name_changed, event)


def announce_user_screen_name_changed(event: UserScreenNameChanged) -> None:
    """Announce that a user's screen name has been changed."""
    channels = [CHANNEL_ORGA_LOG]

    initiator = user_service.find_user(event.initiator_id)

    text = (
        f'{initiator.screen_name} hat das Benutzerkonto '
        f'"{event.old_screen_name}" in "{event.new_screen_name}" umbenannt.'
    )

    send_message(channels, text)


@signals.email_address_invalidated.connect
def _on_user_email_address_invalidated(
    sender, *, event: UserEmailAddressInvalidated
) -> None:
    enqueue(announce_user_email_address_invalidated, event)


def announce_user_email_address_invalidated(
    event: UserEmailAddressInvalidated,
) -> None:
    """Announce that a user's email address has been invalidated."""
    channels = [CHANNEL_ORGA_LOG]

    user = user_service.find_user(event.user_id)
    initiator = user_service.find_user(event.initiator_id)

    text = (
        f'{initiator.screen_name} hat die E-Mail-Adresse '
        f'des Benutzerkontos "{user.screen_name}" invalidiert.'
    )

    send_message(channels, text)


@signals.details_updated.connect
def _on_user_details_updated_changed(
    sender, *, event: UserDetailsUpdated
) -> None:
    enqueue(announce_user_details_updated_changed, event)


def announce_user_details_updated_changed(event: UserDetailsUpdated) -> None:
    """Announce that a user's details have been changed."""
    channels = [CHANNEL_ORGA_LOG]

    user = user_service.find_user(event.user_id)
    initiator = user_service.find_user(event.initiator_id)

    text = (
        f'{initiator.screen_name} hat die persönlichen Daten '
        f'des Benutzerkontos "{user.screen_name}" geändert.'
    )

    send_message(channels, text)


@signals.account_suspended.connect
def _on_user_account_suspended(sender, *, event: UserAccountSuspended) -> None:
    enqueue(announce_user_account_suspended, event)


def announce_user_account_suspended(event: UserAccountSuspended) -> None:
    """Announce that a user account has been suspended."""
    channels = [CHANNEL_ORGA_LOG]

    user = user_service.find_user(event.user_id)
    initiator = user_service.find_user(event.initiator_id)

    text = (
        f'{initiator.screen_name} hat das Benutzerkonto '
        f'"{user.screen_name}" gesperrt.'
    )

    send_message(channels, text)


@signals.account_unsuspended.connect
def _on_user_account_unsuspended(
    sender, *, event: UserAccountUnsuspended
) -> None:
    enqueue(announce_user_account_unsuspended, event)


def announce_user_account_unsuspended(event: UserAccountUnsuspended) -> None:
    """Announce that a user account has been unsuspended."""
    channels = [CHANNEL_ORGA_LOG]

    user = user_service.find_user(event.user_id)
    initiator = user_service.find_user(event.initiator_id)

    text = (
        f'{initiator.screen_name} hat das Benutzerkonto '
        f'"{user.screen_name}" entsperrt.'
    )

    send_message(channels, text)


@signals.account_deleted.connect
def _on_user_account_deleted(sender, *, event: UserAccountDeleted) -> None:
    enqueue(announce_user_account_deleted, event)


def announce_user_account_deleted(event: UserAccountDeleted) -> None:
    """Announce that a user account has been created."""
    channels = [CHANNEL_ORGA_LOG]

    user = user_service.find_user(event.user_id)
    initiator = user_service.find_user(event.initiator_id)

    text = (
        f'{initiator.screen_name} hat das Benutzerkonto '
        f'mit der ID "{user.id}" gelöscht.'
    )

    send_message(channels, text)