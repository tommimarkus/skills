"""Original bounded consumer fixture; RELAY is intentionally unsupported."""


def execute(records, actions):
    rules = {row["id"]: row for row in records}
    energy = 0
    trace = []
    for action in actions:
        if action in ("pulse", "damp-pulse"):
            rule = rules["PULSE"]
            if action != "damp-pulse" or not rule["damp_skip"]:
                energy = min(rule["cap"], energy + rule["gain"])
        elif action == "drain":
            energy = max(0, energy - rules["DRAIN"]["loss"])
        else:
            raise ValueError(f"unsupported action: {action}")
        trace.append(energy)
    return trace
