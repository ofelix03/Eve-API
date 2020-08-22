from slugify import slugify


class TicketDiscountOperator(object):
    EQUAL_TO = '='
    GREATER_THAN = '>'
    GREATER_THAN_OR_EQUAL_TO = '>='
    BETWEEN = '<->'
    operators = [EQUAL_TO, GREATER_THAN, GREATER_THAN_OR_EQUAL_TO, BETWEEN]

    @classmethod
    def has_operator(cls, op):
        return op in cls.operators


class TicketDiscountType:
    EARLY_PURCHASE = "1f8ed81a-f652-44c3-8d16-3b75be10fe2a"
    NUMBER_OF_PURCHASES = "d4925ff6-6779-4204-be9d-63613c652c77"
