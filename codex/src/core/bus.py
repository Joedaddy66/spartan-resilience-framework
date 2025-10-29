"""Simple in-memory event bus."""
from typing import Callable, Dict, List, Any

Subscriber = Callable[[Any], None]


class CodexBus:
    """In-memory event bus for scroll events."""
    
    def __init__(self):
        self.subs: Dict[str, List[Subscriber]] = {}

    def subscribe(self, topic: str, fn: Subscriber):
        """Subscribe to a topic."""
        self.subs.setdefault(topic, []).append(fn)

    def publish(self, topic: str, msg: Any):
        """Publish message to all subscribers."""
        for fn in self.subs.get(topic, []):
            fn(msg)
