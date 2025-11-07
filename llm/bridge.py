class Bridge:
    def process_reasoning(self, reasoning_text: str):
        print("\n[Bridge] Received reasoning to act on.")
        # Example: extract actions and forward them to Arduino
        if "move" in reasoning_text.lower():
            print("[Bridge] Would send: MOTOR_ON")
        if "stop" in reasoning_text.lower():
            print("[Bridge] Would send: MOTOR_OFF")