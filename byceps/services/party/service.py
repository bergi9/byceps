"""
byceps.services.party.service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2020 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

import dataclasses
from datetime import datetime
from typing import Dict, List, Optional, Set

from ...database import db, paginate, Pagination
from ...typing import BrandID, PartyID

from ..brand.models.brand import Brand as DbBrand
from ..brand.transfer.models import Brand

from .models.party import Party as DbParty
from .models.setting import Setting as DbSetting
from .transfer.models import Party, PartyWithBrand


class UnknownPartyId(Exception):
    pass


def create_party(
    party_id: PartyID,
    brand_id: BrandID,
    title: str,
    starts_at: datetime,
    ends_at: datetime,
    *,
    max_ticket_quantity: Optional[int] = None,
) -> Party:
    """Create a party."""
    party = DbParty(
        party_id,
        brand_id,
        title,
        starts_at,
        ends_at,
        max_ticket_quantity=max_ticket_quantity,
    )

    db.session.add(party)
    db.session.commit()

    return _db_entity_to_party(party)


def update_party(
    party_id: PartyID,
    title: str,
    starts_at: datetime,
    ends_at: datetime,
    max_ticket_quantity: Optional[int],
    ticket_management_enabled: bool,
    seat_management_enabled: bool,
    archived: bool,
) -> Party:
    """Update a party."""
    party = DbParty.query.get(party_id)

    if party is None:
        raise UnknownPartyId(party_id)

    party.title = title
    party.starts_at = starts_at
    party.ends_at = ends_at
    party.max_ticket_quantity = max_ticket_quantity
    party.ticket_management_enabled = ticket_management_enabled
    party.seat_management_enabled = seat_management_enabled
    party.archived = archived

    db.session.commit()

    return _db_entity_to_party(party)


def delete_party(party_id: PartyID) -> None:
    """Delete a party."""
    db.session.query(DbSetting) \
        .filter_by(party_id=party_id) \
        .delete()

    db.session.query(DbParty) \
        .filter_by(id=party_id) \
        .delete()

    db.session.commit()


def count_parties() -> int:
    """Return the number of parties (of all brands)."""
    return DbParty.query.count()


def count_parties_for_brand(brand_id: BrandID) -> int:
    """Return the number of parties for that brand."""
    return DbParty.query \
        .filter_by(brand_id=brand_id) \
        .count()


def find_party(party_id: PartyID) -> Optional[Party]:
    """Return the party with that id, or `None` if not found."""
    party = DbParty.query.get(party_id)

    if party is None:
        return None

    return _db_entity_to_party(party)


def get_party(party_id: PartyID) -> Party:
    """Return the party with that id, or `None` if not found."""
    party = find_party(party_id)

    if party is None:
        raise UnknownPartyId(party_id)

    return party


def get_all_parties() -> List[Party]:
    """Return all parties."""
    parties = DbParty.query \
        .all()

    return [_db_entity_to_party(party) for party in parties]


def get_all_parties_with_brands() -> List[DbParty]:
    """Return all parties."""
    parties = DbParty.query \
        .options(db.joinedload('brand')) \
        .all()

    return [_db_entity_to_party_with_brand(party) for party in parties]


def get_active_parties(brand_id: Optional[BrandID] = None) -> List[Party]:
    """Return active (i.e. non-archived) parties."""
    query = DbParty.query

    if brand_id is not None:
        query = query \
            .filter_by(brand_id=brand_id)

    parties = query \
        .filter_by(archived=False) \
        .order_by(DbParty.starts_at) \
        .all()

    return [_db_entity_to_party(party) for party in parties]


def get_archived_parties_for_brand(brand_id: BrandID) -> List[Party]:
    """Return archived parties for that brand."""
    parties = DbParty.query \
        .filter_by(brand_id=brand_id) \
        .filter_by(archived=True) \
        .order_by(DbParty.starts_at.desc()) \
        .all()

    return [_db_entity_to_party(party) for party in parties]


def get_parties(party_ids: Set[PartyID]) -> List[Party]:
    """Return the parties with those IDs."""
    if not party_ids:
        return []

    parties = DbParty.query \
        .filter(DbParty.id.in_(party_ids)) \
        .all()

    return [_db_entity_to_party(party) for party in parties]


def get_parties_for_brand(brand_id: BrandID) -> List[Party]:
    """Return the parties for that brand."""
    parties = DbParty.query \
        .filter_by(brand_id=brand_id) \
        .all()

    return [_db_entity_to_party(party) for party in parties]


def get_parties_for_brand_paginated(
    brand_id: BrandID, page: int, per_page: int
) -> Pagination:
    """Return the parties for that brand to show on the specified page."""
    query = DbParty.query \
        .filter_by(brand_id=brand_id) \
        .order_by(DbParty.starts_at.desc())

    return paginate(query, page, per_page, item_mapper=_db_entity_to_party)


def get_party_count_by_brand_id() -> Dict[BrandID, int]:
    """Return party count (including 0) per brand, indexed by brand ID."""
    brand_ids_and_party_counts = db.session \
        .query(
            DbBrand.id,
            db.func.count(DbParty.id)
        ) \
        .outerjoin(DbParty) \
        .group_by(DbBrand.id) \
        .all()

    return dict(brand_ids_and_party_counts)


def _db_entity_to_party(party: DbParty) -> Party:
    return Party(
        party.id,
        party.brand_id,
        party.title,
        party.starts_at,
        party.ends_at,
        party.max_ticket_quantity,
        party.ticket_management_enabled,
        party.seat_management_enabled,
        party.archived,
    )


def _db_entity_to_party_with_brand(party_entity: DbParty) -> PartyWithBrand:
    brand = Brand(
        party_entity.brand.id,
        party_entity.brand.title,
    )

    party = _db_entity_to_party(party_entity)

    return PartyWithBrand(*dataclasses.astuple(party), brand=brand)
