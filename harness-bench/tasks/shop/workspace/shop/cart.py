from .pricing import calc_total


class Cart:
    def __init__(self):
        self.items = []
        self.code = None

    def add(self, name, price, qty=1):
        self.items.append({"name": name, "price": price, "qty": qty})

    def apply_code(self, code):
        self.code = code

    def total(self):
        return calc_total(self.items, self.code)
