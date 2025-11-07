import json

class ContextBuilder:
    def compose(self, initial: str, memory: list, short_term: str, sensors: dict):
        mem_text = "\n".join(memory) if memory else "(no prior memories)"
        sensor_text = json.dumps(sensors, indent=2)
        return (
            "=== INITIAL PROMPT ===\n"
            # "[Provide an initial prompt showing what your task is.]\n"
            f"{initial}\n\n"
            "=== MEMORY ===\n"
            # "[Provide your memories, what do you remember?]\n"
            f"{mem_text}\n\n"
            "=== SHORT TERM CONTEXT ===\n"
            # "[Provide a summary of your recent knowledge of your environment]\n"
            f"{short_term}\n\n"
            "=== SENSORS ===\n"
            # "[Provide a readout of what you are sensing in a readable format]\n"
            f"{sensor_text}\n\n"
            f"=== REASONING ===\n"
            "[Provide reasoning regarding your current task in the form of a summary. Use the data available to you. "
            "Keep your summary short, you don't have much time. Don't include grammer and use small words, use as little characters as possible. "
            "Don't provide explanations. Don't extrapolate, use only the information you have given to come to a conclusion. End when completed, don't follow up with another section.]\n"
            # "Example reasoning: I am in a room and am trying to leave. Based on the distance of 15cm, I am close to the door. I must move forward to leave.\n"
        )