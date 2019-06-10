
class PaymentTypes(object):
    MOBILE_MONEY = "mobile_money"
    CARD = "card"

    @classmethod
    def accepts_payment_of_type(cls, type):
        return type in [cls.MOBILE_MONEY, cls.CARD]


class MobileNetworks(object):
    MTN = "mtn"
    VODAFONE = "vodafone"
    AIRTEL_TIGO = "airtel-tigo"
    GLO = "glo"


class PaymentCards(object):
    VISA = 'visa-card'
    MASTERCARD = 'master-card'
    DEBIT = 'debit-card'


class MobilePaymentInfo(object):

    def __init__(self, mobile_network, mobile_number):
        self.mobile_network = mobile_network
        self.mobile_number = mobile_number


class CardPaymentInfo(object):

    def __init__(self, card_name, card_type, card_number, card_expiration_date, card_cv):
        self.card_name = card_name
        self.card_type = card_type
        self.card_number = card_number
        self.card_expiration_date = card_expiration_date
        self.card_cv = card_cv


class DiscountTypes(object):

    EARLY_PURCHASE = "early-purchase"
    NUMBER_OF_PURCHASED_TICKETS = "number-of-tickets"

    @classmethod
    def has_type(cls, type):
        return type in [cls.EARLY_PURCHASE, cls.NUMBER_OF_PURCHASED_TICKETS]