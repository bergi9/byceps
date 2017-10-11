"""
byceps.services.shop.order.action_service
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2017 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from typing import Any, Callable, Dict, Sequence, Set

from ....database import db

from ..article.models.article import ArticleNumber

from .actions.award_badge import award_badge
from .actions.create_tickets import create_tickets
from .models.order import OrderID, OrderTuple
from .models.order_action import OrderAction
from . import service as order_service


Parameters = Dict[str, Any]

OrderActionType = Callable[[OrderTuple, ArticleNumber, int, Parameters], None]


PROCEDURES_BY_NAME = {
    'award_badge': award_badge,
    'create_tickets': create_tickets,
}  # type: Dict[str, OrderActionType]


def create_order_action(article_number: ArticleNumber, procedure: str,
                        parameters: Parameters) -> None:
    """Create an order action."""
    action = OrderAction(article_number, procedure, parameters)

    db.session.add(action)
    db.session.commit()


def execute_order_actions(order_id: OrderID) -> None:
    """Execute relevant actions for order."""
    order = order_service.find_order_with_details(order_id)

    article_numbers = {item.article_number for item in order.items}

    if not article_numbers:
        return

    quantities_by_article_number = {
        item.article_number: item.quantity for item in order.items
    }

    actions = _get_actions(article_numbers)

    for action in actions:
        article_quantity = quantities_by_article_number[action.article_number]

        _execute_procedure(order, action, article_quantity)


def _get_actions(article_numbers: Set[ArticleNumber]) -> Sequence[OrderAction]:
    """Return the order actions for those article numbers."""
    return OrderAction.query \
        .filter(OrderAction.article_number.in_(article_numbers)) \
        .all()


def _execute_procedure(order: OrderTuple, action: OrderAction,
                       article_quantity: int) -> None:
    """Execute the procedure configured for that order action."""
    article_number = action.article_number
    procedure_name = action.procedure
    params = action.parameters

    procedure = _get_procedure(procedure_name)

    procedure(order, article_number, article_quantity, params)


def _get_procedure(name: str) -> OrderActionType:
    """Return procedure with that name, or raise an exception if the
    name is not registerd.
    """
    procedure = PROCEDURES_BY_NAME.get(name)

    if procedure is None:
        raise Exception(
            "Unknown procedure '{}' configured for article number '{}'."
                .format(procedure_name, article_number))

    return procedure
