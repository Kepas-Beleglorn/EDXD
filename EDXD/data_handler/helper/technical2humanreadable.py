def get_clean_body_type(raw_body_type: str) -> str:
    if raw_body_type == "A_BlueWhiteSuperGiant":
        return "A (Blue-White Super Giant)"
    if raw_body_type == "B_BlueWhiteSuperGiant":
        return "B (Blue-White Super Giant)"
    if raw_body_type == "K_OrangeGiant":
        return "K (Orange Giant)"
    if raw_body_type == "M_RedGiant":
        return "M (Red Giant)"
    if raw_body_type == "M_RedSuperGiant":
        return "M (Red Super Giant)"
    if raw_body_type == "SupermassiveBlackHole":
        return "Supermassive Black Hole"

    return raw_body_type
