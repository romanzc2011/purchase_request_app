ROUTING_RULES = {
    "511": "IT_group",
    "092": "FINANCE_group",
    "ABOVE_250": "TED",
    "BELOW_250": "EDMUND",
}

def get_routing_group(fund, price):
    if fund.startswith("511"):
        return ROUTING_RULES["511"]
    else:
        return ROUTING_RULES["0900"]

def get_routing_group_by_price(price):
    if price > 250:
        return ROUTING_RULES["ABOVE_250"]
    else:
        return ROUTING_RULES["BELOW_250"]