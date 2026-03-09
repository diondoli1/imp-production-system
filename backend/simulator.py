"""Phase 1 machine simulator placeholder.

The simulator is non-autonomous and must only respond to explicit operator actions.
"""

from backend.schemas import MACHINE_ID


class Simulator:
    """Simple placeholder for operator-triggered simulator actions."""

    def trigger(self, action: str) -> dict:
        return {
            "message": "Simulator is registered and awaits explicit operator triggers.",
            "action": action,
            "machine_id": MACHINE_ID,
            "autonomous_mode": False,
        }
