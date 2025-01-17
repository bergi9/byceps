"""
byceps.blueprints.site.site.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask import g, url_for

from ..page.templating import url_for_site_page

from ....services.site_navigation.models import (
    NavItemForRendering,
    NavItemTargetType,
)
from ....services.site_navigation import site_navigation_service
from ....util.framework.blueprint import create_blueprint
from ....util.l10n import get_locale_str


blueprint = create_blueprint('site', __name__)


@blueprint.app_template_global()
def get_nav_menu_items(menu_name: str) -> list[NavItemForRendering]:
    """Make navigation menus accessible to templates."""
    locale_str = get_locale_str()
    if locale_str is None:  # outside of request
        return []

    items = site_navigation_service.get_items_for_menu(
        g.site_id, menu_name, locale_str
    )
    return [_to_item_for_rendering(g.site_id, item) for item in items]


def _to_item_for_rendering(site_id: str, item) -> NavItemForRendering:
    target = _assemble_target(site_id, item.target_type, item.target)

    return NavItemForRendering(
        target=target,
        label=item.label,
        current_page_id=item.current_page_id,
        children=[],
    )


def _assemble_target(
    site_id: str, target_type: NavItemTargetType, target: str
) -> str:
    if target_type == NavItemTargetType.endpoint:
        return url_for(target)
    elif target_type == NavItemTargetType.page:
        return url_for_site_page(site_id, target)
    elif target_type == NavItemTargetType.url:
        return target
    else:
        raise ValueError('Unknown target type')
