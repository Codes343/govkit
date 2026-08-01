"""One module per upstream federal data source.

Each module exposes a ``fetch(client, options)`` async generator that yields
pages of already-normalized records. Keeping fetch and normalization together
means an actor's ``main.py`` is only wiring: read input, stream pages, bill.
"""
