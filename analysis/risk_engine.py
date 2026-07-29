def calculate_risk(record):

    score = 0
    reasons = []

    # Phone number
    if record.phones:
        score += 20
        reasons.append("Phone number detected")

    # UPI ID
    if record.upi_ids:
        score += 30
        reasons.append("UPI ID detected")

    # Email
    if record.emails:
        score += 10
        reasons.append("Email detected")

    # URL
    if record.urls:
        score += 10
        reasons.append("URL detected")

    # Decide level
    if score >= 50:
        level = "HIGH"

    elif score >= 20:
        level = "MEDIUM"

    else:
        level = "LOW"

    return {
        "score": score,
        "level": level,
        "reasons": reasons
    }