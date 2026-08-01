"""Fedstack — shared core for US federal open-data Apify Actors.

Every Fedstack actor talks to a keyless, public, US federal government JSON API
over plain HTTP. No browsers, no proxies, no credentials. That keeps platform
compute cost near zero, which is what makes the pay-per-event margin work.
"""

from fedstack.billing import Billing
from fedstack.http import FedstackClient, UpstreamError

__all__ = ["Billing", "FedstackClient", "UpstreamError"]

__version__ = "0.1.0"

# Sent on every upstream request so agency ops teams can identify and contact us
# instead of silently blocking the IP range.
USER_AGENT = (
    "Fedstack/0.1 (+https://apify.com/fedstack; public-data extraction; "
    "contact via Apify Store issues)"
)
