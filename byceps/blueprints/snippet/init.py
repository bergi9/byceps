"""
byceps.blueprints.snippet.init
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2019 Jochen Kupperschmidt
:License: Modified BSD, see LICENSE for details.
"""

from flask import current_app

from ...services.snippet import mountpoint_service

from .views import blueprint, view_latest_by_name


def add_routes_for_snippets(scope):
    """Register routes for snippets with the application."""
    mountpoints = mountpoint_service.get_mountpoints_for_scope(scope)

    for mountpoint in mountpoints:
        add_route_for_snippet(mountpoint)


def add_route_for_snippet(mountpoint):
    """Register a route for the snippet."""
    endpoint = '{}.{}'.format(blueprint.name, mountpoint.endpoint_suffix)
    defaults = {'name': mountpoint.snippet.name}

    current_app.add_url_rule(
        mountpoint.url_path,
        endpoint,
        view_func=view_latest_by_name,
        defaults=defaults)
