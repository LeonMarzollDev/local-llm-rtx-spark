from . import pricing


def receipt(cart):
    lines = [f"{item['qty']} x {item['name']}: {item['price'] * item['qty']:.2f} EUR" for item in cart.items]
    lines.append(f"total: {pricing.calc_total(cart.items, cart.code):.2f} EUR")
    return "\n".join(lines)
