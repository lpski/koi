
class Portfolio:
    has_stock: bool
    purchase_date: str
    purchase_price: float
    quantity: float
    hold_duration: int
    confidence: float
    
    profit: bool
    gross_profit: float
    stop_loss_pct: float
    stop_loss_price: float
    purchases: int
    hold_start_price: float
    hold_start_shares: float
    symbol: str

    def __init__(self, hold_start_price: float, has_stock: bool = False, purchase_date: str = '', purchase_price: float = None, quantity: float = 0, profit: float = 0, gross_profit: float = 0, stop_loss_pct: float = 0.03, purchases: int = 0, symbol: str = ''):
        self.hold_start_price = hold_start_price
        self.has_stock = has_stock
        self.purchase_date = purchase_date
        self.purchase_price = purchase_price
        self.profit = profit
        self.quantity = quantity
        self.gross_profit = gross_profit
        self.stop_loss_pct = stop_loss_pct
        self.purchases = purchases
        self.symbol = symbol
        self.hold_duration = 0
        self.confidence = 0

    def purchased(self, price: float, quantity: float, date: str, confidence: float):
        self.has_stock = True
        self.purchase_price = price
        self.purchase_date = date
        self.quantity = quantity
        self.purchases += 1
        self.confidence = confidence
        try: self.stop_loss_price = price - (price * self.stop_loss_pct)
        except: self.stop_loss_price = price * .95

    def sold(self, price: float, quantity: float):
        self.quantity -= quantity
        self.has_stock = False
        self.profit += (price - self.purchase_price)
        self.gross_profit += (price - self.purchase_price) * quantity
        self.hold_duration = 0

    def set_hold_start(self, price: float, initial_capital: float):
        self.hold_start_price = price
        self.hold_start_shares = initial_capital /  price

    def current_equity(self, current_price: float):
        return (current_price - self.purchase_price) * self.quantity


    def hold_profit(self, current_price: float, initial_capital: float):
        hold_shares_purchased = initial_capital / self.hold_start_price
        current_shares_value = hold_shares_purchased * current_price
        return current_shares_value - initial_capital


    def safe_dict(self):
        data = self.__dict__.copy()
        del data['purchase_date']
        del data['purchase_price']
        return data

    
    @classmethod
    def from_json(cls, data: dict):
        return cls(**data)

