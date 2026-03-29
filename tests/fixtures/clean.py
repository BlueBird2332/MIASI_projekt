"""A perfectly clean module."""


def greet(name: str) -> str:
    """Return a greeting."""
    return f"Hello, {name}!"


class Greeter:
    """Greets people."""

    def __init__(self, prefix: str = "Hello") -> None:
        """Set the greeting prefix."""
        self.prefix = prefix

    def greet(self, name: str) -> str:
        """Return a greeting with the configured prefix."""
        return f"{self.prefix}, {name}!"
