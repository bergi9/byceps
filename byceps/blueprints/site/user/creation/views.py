"""
byceps.blueprints.site.user.creation.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2021 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from __future__ import annotations
from datetime import datetime
from typing import Optional

from flask import abort, g, request
from flask_babel import gettext

from .....services.brand import settings_service as brand_settings_service
from .....services.consent import subject_service as consent_subject_service
from .....services.consent.transfer.models import Consent, Subject, SubjectID
from .....services.newsletter import (
    command_service as newsletter_command_service,
)
from .....services.newsletter.transfer.models import ListID as NewsletterListID
from .....services.site import (
    settings_service as site_settings_service,
    service as site_service,
)
from .....services.user import creation_service as user_creation_service
from .....signals import user as user_signals
from .....util.framework.blueprint import create_blueprint
from .....util.framework.flash import flash_error, flash_success
from .....util.framework.templating import templated
from .....util.views import redirect_to

from .forms import assemble_user_create_form


blueprint = create_blueprint('user_creation', __name__)


@blueprint.get('/create')
@templated
def create_form(erroneous_form=None):
    """Show a form to create a user."""
    _abort_if_user_account_creation_disabled()

    required_consent_subjects = _get_required_consent_subjects()
    newsletter_list_id = _find_newsletter_list_for_brand()

    real_name_required = _is_real_name_required()
    newsletter_offered = newsletter_list_id is not None

    if erroneous_form:
        form = erroneous_form
    else:
        UserCreateForm = assemble_user_create_form(
            real_name_required=real_name_required,
            required_consent_subjects=required_consent_subjects,
            newsletter_offered=newsletter_offered,
        )
        form = UserCreateForm()

    return {
        'form': form,
        'required_consent_subjects': required_consent_subjects,
    }


@blueprint.post('/')
def create():
    """Create a user."""
    _abort_if_user_account_creation_disabled()

    required_consent_subjects = _get_required_consent_subjects()
    newsletter_list_id = _find_newsletter_list_for_brand()

    real_name_required = _is_real_name_required()
    newsletter_offered = newsletter_list_id is not None

    UserCreateForm = assemble_user_create_form(
        real_name_required=real_name_required,
        required_consent_subjects=required_consent_subjects,
        newsletter_offered=newsletter_offered,
    )
    form = UserCreateForm(request.form)

    if not form.validate():
        return create_form(form)

    screen_name = form.screen_name.data.strip()
    email_address = form.email_address.data.strip().lower()
    password = form.password.data

    now_utc = datetime.utcnow()

    if real_name_required:
        first_names = form.first_names.data.strip()
        last_name = form.last_name.data.strip()
    else:
        first_names = None
        last_name = None

    consents = {
        _assemble_consent(subject.id, now_utc)
        for subject in required_consent_subjects
    }

    try:
        user, event = user_creation_service.create_user(
            screen_name,
            email_address,
            password,
            first_names,
            last_name,
            g.site_id,
            consents=consents,
        )
    except user_creation_service.UserCreationFailed:
        flash_error(
            gettext(
                'User "%(screen_name)s" could not be created.',
                screen_name=screen_name,
            )
        )
        return create_form(form)

    flash_success(
        gettext(
            'User "%(screen_name)s" has been created. Before you can log in, '
            'please visit the link emailed to you to verify your email address.',
            screen_name=user.screen_name,
        )
    )

    user_signals.account_created.send(None, event=event)

    if newsletter_offered:
        subscribe_to_newsletter = form.subscribe_to_newsletter.data
        if subscribe_to_newsletter:
            newsletter_command_service.subscribe(
                user.id, newsletter_list_id, now_utc
            )

    return redirect_to('authentication.login.login_form')


def _abort_if_user_account_creation_disabled():
    site = site_service.get_site(g.site_id)
    if not site.user_account_creation_enabled:
        flash_error(gettext('User account creation is disabled.'))
        abort(403)


def _is_real_name_required() -> bool:
    """Return `True` if real name is required.

    By default, real name is required. It can be disabled by configuring
    the string `false` for the site setting `real_name_required`.
    """
    value = _find_site_setting_value('real_name_required')

    return value != 'false'


def _get_required_consent_subjects() -> set[Subject]:
    """Return the consent subjects required for this brand."""
    return consent_subject_service.get_subjects_required_for_brand(g.brand_id)


def _find_newsletter_list_for_brand() -> Optional[NewsletterListID]:
    """Return the newsletter list configured for this brand, or `None`
    if none is configured.
    """
    value = _find_brand_setting_value('newsletter_list_id')

    if not value:
        return None

    return NewsletterListID(value)


def _find_brand_setting_value(setting_name: str) -> Optional[str]:
    """Return the value configured for this brand and the given setting
    name, or `None` if not configured.
    """
    return brand_settings_service.find_setting_value(g.brand_id, setting_name)


def _find_site_setting_value(setting_name: str) -> Optional[str]:
    """Return the value configured for this site and the given setting
    name, or `None` if not configured.
    """
    return site_settings_service.find_setting_value(g.site_id, setting_name)


def _assemble_consent(subject_id: SubjectID, expressed_at: datetime) -> Consent:
    return Consent(
        user_id=None,  # not available at this point
        subject_id=subject_id,
        expressed_at=expressed_at,
    )
