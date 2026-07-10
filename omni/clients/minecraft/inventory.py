import threading

from omni.config import SLOT_SWITCH_TIMEOUT_SECONDS


class InventoryMixin:
    def select_hotbar_slot(self, target_slot: int) -> tuple[bool, dict]:
        """
        Safely switches the bot's quickbar slot and waits for confirmation.
        Accepts slots from 0 to 8.
        """
        if type(target_slot) != int:
            return False, {"error": "target_slot must be an integer", "provided": type(target_slot)}

        # 1. Validation check
        if not (0 <= target_slot <= 8):
            return False, {"error": "invalid_slot_range", "provided": target_slot}

        # 2. Instant return if already on that slot
        current_slot = self.bot.quickBarSlot
        if current_slot == target_slot:
            return True, {
                "status": "already_selected",
                "slot": current_slot
            }

        # 3. Setup threading and state tracking
        done = threading.Event()
        state = {
            "success": False,
            "error": None,
        }

        # 4. Define precise callbacks and cleanup
        def cleanup():
            try:
                self.bot.removeListener("heldItemChanged", on_held_item_changed)
            except Exception:
                pass
            done.set()

        def on_held_item_changed(*args):
            actual_slot = self.bot.quickBarSlot

            if actual_slot == target_slot:
                state["success"] = True
                state["error"] = None
            else:
                state["success"] = False
                state["error"] = (
                    f"slot_mismatch: expected {target_slot}, got {actual_slot}"
                )

            cleanup()

        # 5. Attach the event listener
        self.bot.on("heldItemChanged", on_held_item_changed)

        # 6. Execute the synchronous JavaScript command
        try:
            self.bot.setQuickBarSlot(target_slot)
        except Exception as e:
            state["success"] = False
            state["error"] = f"js_execution_error: {str(e)}"
            cleanup()

        # 7. Block the Python thread until JS triggers the event or times out
        finished = done.wait(timeout=SLOT_SWITCH_TIMEOUT_SECONDS)

        # 8. Handle a timeout scenario safely
        if not finished:
            try:
                self.bot.removeListener("heldItemChanged", on_held_item_changed)
            except Exception:
                pass

            return False, {
                "error": "switch_timeout",
                "last_known_slot": self.bot.quickBarSlot,
                "intended_slot": target_slot,
            }

        # 9. Return the resulting state summary
        return state["success"], {
            "previous_slot": current_slot,
            "current_slot": self.bot.quickBarSlot,
            "intended_slot": target_slot,
            "error": state["error"],
        }
