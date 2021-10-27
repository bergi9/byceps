"""
byceps.signals.guest_server
~~~~~~~~~~~~~~~~~~~~~~~~~~~

:Copyright: 2006-2021 Jochen Kupperschmidt
:License: Revised BSD (see `LICENSE` file for details)
"""

from blinker import Namespace


guest_server_signals = Namespace()


guest_server_registered = guest_server_signals.signal('guest-server-registered')