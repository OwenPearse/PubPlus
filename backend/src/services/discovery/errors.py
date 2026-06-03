from __future__ import annotations


class DiscoveryError(Exception):
    """Base for shared discovery / filter validation failures."""


class DiscoveryFilterError(DiscoveryError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


class DiscoveryQueryError(DiscoveryError):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")
