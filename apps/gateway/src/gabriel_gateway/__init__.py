"""Gabriel Gateway (BFF).

The single edge the browser talks to. It holds no business logic — agent-spec
construction, validation, and persistence are delegated to gabriel-core over
HTTP (the Gateway never imports gabriel-core).
"""

__version__ = "0.2.0"
