def assess_risk(order):
    # very simple placeholder risk check
    if order.get("quantity", 0) > 1000000:
        return {"allowed": False, "reason": "size"}
    return {"allowed": True}
