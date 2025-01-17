"""
byceps.services.newsletter.newsletter_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from typing import Iterable, Iterator, Optional

from sqlalchemy import select

from ...database import db
from ...typing import UserID

from ..user.dbmodels.user import DbUser

from .dbmodels import DbList, DbSubscription, DbSubscriptionUpdate
from .models import List, ListID, Subscriber


def find_list(list_id: ListID) -> Optional[List]:
    """Return the list with that ID, or `None` if not found."""
    db_list = db.session.get(DbList, list_id)

    if db_list is None:
        return None

    return _db_entity_to_list(db_list)


def get_all_lists() -> list[List]:
    """Return all lists."""
    db_lists = db.session.scalars(select(DbList)).all()

    return [_db_entity_to_list(db_list) for db_list in db_lists]


def count_subscribers_for_list(list_id: ListID) -> int:
    """Return the number of users that are currently subscribed to that list."""
    return db.session.scalar(
        select(db.func.count())
        .select_from(DbSubscription)
        .filter_by(list_id=list_id)
    )


def get_subscribers(list_id: ListID) -> Iterable[Subscriber]:
    """Yield screen name and email address of the initialized users that
    are currently subscribed to the list.
    """
    subscriber_ids = db.session.scalars(
        select(DbSubscription.user_id).filter_by(list_id=list_id)
    ).all()

    return _get_subscriber_details(set(subscriber_ids))


def _get_subscriber_details(user_ids: set[UserID]) -> Iterator[Subscriber]:
    """Yield screen name and email address of each eligible user."""
    if not user_ids:
        return []

    rows = db.session.execute(
        select(
            DbUser.screen_name,
            DbUser.email_address,
        )
        .filter(DbUser.id.in_(user_ids))
        .filter(DbUser.email_address.is_not(None))
        .filter_by(initialized=True)
        .filter_by(email_address_verified=True)
        .filter_by(suspended=False)
        .filter_by(deleted=False)
    ).all()

    for row in rows:
        yield Subscriber(
            screen_name=row.screen_name,
            email_address=row.email_address,
        )


def get_subscription_updates_for_user(
    user_id: UserID,
) -> list[DbSubscriptionUpdate]:
    """Return subscription updates made by the user, for any list."""
    return db.session.scalars(
        select(DbSubscriptionUpdate).filter_by(user_id=user_id)
    ).all()


def is_subscribed(user_id: UserID, list_id: ListID) -> bool:
    """Return if the user is subscribed to the list or not."""
    return db.session.scalar(
        select(
            db.exists()
            .where(DbSubscription.user_id == user_id)
            .where(DbSubscription.list_id == list_id)
        )
    )


def _db_entity_to_list(db_list: DbList) -> List:
    return List(
        id=db_list.id,
        title=db_list.title,
    )
