"""GovKit — shared core for US federal open-data Apify Actors.

Every GovKit actor talks to a keyless, public, US federal government JSON API
over plain HTTP. No browsers, no proxies, no credentials. That keeps platform
compute cost near zero, which is what makes the pay-per-event margin work.
"""

from govkit.billing import Billing
from govkit.http import GovKitClient, UpstreamError

__all__ = ["Billing", "GovKitClient", "UpstreamError"]

__version__ = "0.1.0"


def _user_agent() -> str:
    """Identify GovKit honestly, and keep the HTTP client's own token.

    The trailing `python-httpx/<version>` is not decoration. ClinicalTrials.gov
    sits behind an edge filter that allow-lists recognised client tokens and
    returns HTTP 403 to everything else - including a polite, contactable,
    crawler-style User-Agent. Dropping the library token breaks that source
    outright; keeping it is also simply true, since httpx is what we use.
    """
    try:
        import httpx

        client = f"python-httpx/{httpx.__version__}"
    except (ImportError, AttributeError):  # pragma: no cover - httpx is required
        client = "python-httpx"
    return (
        "GovKit/0.1 (+https://apify.com/govkit; public-data extraction; "
        f"contact via Apify Store issues) {client}"
    )


# Sent on every upstream request so agency ops teams can identify and contact us
# instead of silently blocking the IP range.
USER_AGENT = _user_agent()
