"""
byceps.application
~~~~~~~~~~~~~~~~~~

:Copyright: 2014-2023 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations
from collections.abc import Iterator
from importlib import import_module
import os
from pathlib import Path
from typing import Any, Callable, Optional

from flask import abort, current_app, Flask, g
from flask_babel import Babel
import jinja2
from redis import Redis
import rtoml
import structlog

from .blueprints.blueprints import register_blueprints
from . import config, config_defaults
from .database import db
from .util.authorization import has_current_user_permission, load_permissions
from .util.l10n import get_current_user_locale
from .util import templatefilters, templatefunctions
from .util.templating import SiteTemplateOverridesLoader


log = structlog.get_logger()


def create_app(
    *,
    config_filename: Optional[Path | str] = None,
    config_overrides: Optional[dict[str, Any]] = None,
) -> Flask:
    """Create the actual Flask application."""
    app = Flask('byceps')

    _configure(app, config_filename, config_overrides)

    # Throw an exception when an undefined name is referenced in a template.
    # NB: Set via `app.jinja_options['undefined'] = ` instead of
    #     `app.jinja_env.undefined = ` as that would create the Jinja
    #      environment too early.
    app.jinja_options['undefined'] = jinja2.StrictUndefined

    babel = Babel(app)
    babel.locale_selector_func = get_current_user_locale

    # Initialize database.
    db.init_app(app)

    # Initialize Redis client.
    app.redis_client = Redis.from_url(app.config['REDIS_URL'])

    app_mode = config.get_app_mode(app)

    load_permissions()

    register_blueprints(app, app_mode)

    templatefilters.register(app)
    templatefunctions.register(app)

    _add_static_file_url_rules(app)

    if app_mode.is_admin():
        _init_admin_app(app)
    elif app_mode.is_site():
        _init_site_app(app)

    _load_announce_signal_handlers()

    log.info('Application created', app_mode=app_mode.name, debug=app.debug)

    return app


def _configure(
    app: Flask,
    config_filename: Optional[Path | str] = None,
    config_overrides: Optional[dict[str, Any]] = None,
) -> None:
    """Configure application from file, environment variables, and defaults."""
    app.config.from_object(config_defaults)

    if config_filename is None:
        config_filename = os.environ.get('BYCEPS_CONFIG')

    if config_filename is not None:
        if isinstance(config_filename, str):
            config_filename = Path(config_filename)

        if config_filename.suffix == '.py':
            app.config.from_pyfile(str(config_filename))
        else:
            app.config.from_file(str(config_filename), load=rtoml.load)

    if config_overrides is not None:
        app.config.from_mapping(config_overrides)

    # Allow configuration values to be overridden by environment variables.
    app.config.update(_get_config_from_environment())

    _ensure_required_config_keys(app)

    config.init_app(app)


def _get_config_from_environment() -> Iterator[tuple[str, str]]:
    """Obtain selected config values from environment variables."""
    for key in (
        'APP_MODE',
        'MAIL_HOST',
        'MAIL_PASSWORD',
        'MAIL_PORT',
        'MAIL_STARTTLS',
        'MAIL_SUPPRESS_SEND',
        'MAIL_USE_SSL',
        'MAIL_USERNAME',
        'METRICS_ENABLED',
        'REDIS_URL',
        'SECRET_KEY',
        'SITE_ID',
        'SQLALCHEMY_DATABASE_URI',
    ):
        value = os.environ.get(key)
        if value:
            yield key, value


def _ensure_required_config_keys(app: Flask) -> None:
    """Ensure the required configuration keys have values."""
    for key in (
        'APP_MODE',
        'REDIS_URL',
        'SECRET_KEY',
        'SQLALCHEMY_DATABASE_URI',
    ):
        if not app.config.get(key):
            raise config.ConfigurationError(
                f'Missing value for configuration key "{key}".'
            )


def _add_static_file_url_rules(app: Flask) -> None:
    """Add URL rules to for static files."""
    app.add_url_rule(
        '/sites/<site_id>/<path:filename>',
        endpoint='site_file',
        methods=['GET'],
        build_only=True,
    )


def _init_admin_app(app: Flask) -> None:
    """Initialize admin application."""
    import rq_dashboard

    @rq_dashboard.blueprint.before_request
    def require_permission():
        if not has_current_user_permission('jobs.view'):
            abort(403)

    app.register_blueprint(rq_dashboard.blueprint, url_prefix='/admin/rq')


def _init_site_app(app: Flask) -> None:
    """Initialize site application."""
    # Incorporate site-specific template overrides.
    app.jinja_loader = SiteTemplateOverridesLoader()

    # Set up site-aware template context processor.
    app._site_context_processors = {}
    app.context_processor(_get_site_template_context)


def _get_site_template_context() -> dict[str, Any]:
    """Return the site-specific additions to the template context."""
    site_context_processor = _find_site_template_context_processor_cached(
        g.site_id
    )

    if not site_context_processor:
        return {}

    return site_context_processor()


def _find_site_template_context_processor_cached(
    site_id: str,
) -> Optional[Callable[[], dict[str, Any]]]:
    """Return the template context processor for the site.

    A processor will be cached after it has been obtained for the first
    time.
    """
    # `None` is a valid value for a site that does not specify a
    # template context processor.

    if site_id in current_app._site_context_processors:
        return current_app._site_context_processors.get(site_id)
    else:
        context_processor = _find_site_template_context_processor(site_id)
        current_app._site_context_processors[site_id] = context_processor
        return context_processor


def _find_site_template_context_processor(
    site_id: str,
) -> Optional[Callable[[], dict[str, Any]]]:
    """Import a template context processor from the site's package.

    If a site package contains a module named `extension` and that
    contains a top-level callable named `template_context_processor`,
    then that callable is imported and returned.
    """
    module_name = f'sites.{site_id}.extension'
    try:
        module = import_module(module_name)
    except ModuleNotFoundError:
        # No extension module found in site package.
        return None

    context_processor = getattr(module, 'template_context_processor', None)
    if context_processor is None:
        # Context processor not found in module.
        return None

    if not callable(context_processor):
        # Context processor object is not callable.
        return None

    return context_processor


def _load_announce_signal_handlers() -> None:
    """Import modules containing handlers so they connect to the
    corresponding signals.
    """
    from .announce import connections  # noqa: F401
