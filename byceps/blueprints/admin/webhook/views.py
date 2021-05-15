"""
byceps.blueprints.admin.webhook.views
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2021 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from flask import abort, request
from flask_babel import gettext

from ....announce.events import EVENT_TYPES_TO_NAMES
from ....announce.helpers import call_webhook
from ....services.webhooks import service as webhook_service
from ....services.webhooks.transfer.models import OutgoingWebhook, WebhookID
from ....util.authorization import register_permission_enum
from ....util.framework.blueprint import create_blueprint
from ....util.framework.flash import flash_error, flash_success
from ....util.framework.templating import templated
from ....util.views import permission_required, redirect_to, respond_no_content

from .authorization import WebhookPermission
from .forms import (
    assemble_create_form,
    assemble_update_form,
    _create_event_field_name,
)


blueprint = create_blueprint('webhook_admin', __name__)


register_permission_enum(WebhookPermission)


WEBHOOK_EVENT_NAMES = frozenset(EVENT_TYPES_TO_NAMES.values())


@blueprint.get('/')
@permission_required(WebhookPermission.view)
@templated
def index():
    """Show webhooks."""
    webhooks = webhook_service.get_all_webhooks()

    webhooks.sort(key=lambda w: (w.description is None, w.description or ''))

    return {
        'webhooks': webhooks,
    }


@blueprint.get('/create')
@permission_required(WebhookPermission.administrate)
@templated
def create_form(erroneous_form=None):
    """Show form to create a webhook."""
    event_names = WEBHOOK_EVENT_NAMES
    CreateForm = assemble_create_form(event_names)

    form = erroneous_form if erroneous_form else CreateForm()

    return {
        'form': form,
        'event_names': event_names,
    }


@blueprint.post('/')
@permission_required(WebhookPermission.administrate)
def create():
    """Create a webhook."""
    event_names = WEBHOOK_EVENT_NAMES
    CreateForm = assemble_create_form(event_names)

    form = CreateForm(request.form)

    if not form.validate():
        return create_form(form)

    event_selectors = {}
    for event_name in event_names:
        if form.get_field_for_event_name(event_name).data:
            event_selectors[event_name] = None

    format = form.format.data.strip()
    url = form.url.data.strip()
    description = form.description.data.strip()
    enabled = False

    webhook = webhook_service.create_outgoing_webhook(
        event_selectors, format, url, enabled, description=description
    )

    flash_success(gettext('Webhook has been created.'))

    return redirect_to('.index')


@blueprint.get('/webhooks/<uuid:webhook_id>/update')
@permission_required(WebhookPermission.administrate)
@templated
def update_form(webhook_id, erroneous_form=None):
    """Show form to update a webhook."""
    webhook = _get_webhook_or_404(webhook_id)

    event_names = WEBHOOK_EVENT_NAMES
    UpdateForm = assemble_update_form(event_names)

    # Pre-fill event type checkboxes.
    event_type_fields = {}
    for event_type_name in webhook.event_selectors:
        field_name = _create_event_field_name(event_type_name)
        event_type_fields[field_name] = True

    form = (
        erroneous_form
        if erroneous_form
        else UpdateForm(obj=webhook, **event_type_fields)
    )

    return {
        'webhook': webhook,
        'form': form,
        'event_names': event_names,
    }


@blueprint.post('/webhooks/<uuid:webhook_id>')
@permission_required(WebhookPermission.administrate)
def update(webhook_id):
    """Update the webhook."""
    webhook = _get_webhook_or_404(webhook_id)

    event_names = WEBHOOK_EVENT_NAMES
    UpdateForm = assemble_update_form(event_names)

    form = UpdateForm(request.form)

    if not form.validate():
        return update_form(webhook.id, form)

    event_selectors = {}
    for event_name in event_names:
        if form.get_field_for_event_name(event_name).data:
            event_selectors[event_name] = None

    format = form.format.data.strip()
    url = form.url.data.strip()
    text_prefix = form.text_prefix.data.lstrip()  # Allow trailing whitespace.
    description = form.description.data.strip()
    enabled = form.enabled.data

    webhook = webhook_service.update_outgoing_webhook(
        webhook.id,
        event_selectors,
        format,
        url,
        enabled,
        text_prefix=text_prefix,
        description=description,
    )

    flash_success(gettext('Webhook has been updated.'))

    return redirect_to('.index')


@blueprint.post('/webhooks/<uuid:webhook_id>/test')
@permission_required(WebhookPermission.administrate)
@respond_no_content
def test(webhook_id):
    """Call the webhook (synchronously)."""
    webhook = _get_webhook_or_404(webhook_id)

    text = 'Test, test … is this thing on?!'
    try:
        call_webhook(webhook, text)
        flash_success(
            gettext('Webhook call has been successful.'), icon='success'
        )
    except Exception as e:
        flash_error(
            gettext('Webhook call failed:')
            + f'<br><pre style="white-space: pre-wrap;">{e}</pre>',
            icon='warning',
            text_is_safe=True,
        )


# helpers


def _get_webhook_or_404(webhook_id: WebhookID) -> OutgoingWebhook:
    webhook = webhook_service.find_webhook(webhook_id)

    if webhook is None:
        abort(404)

    return webhook
