class BaseException(Exception):

    def __init__(self, message=None):
        self.message = message


class NotAuthUser(Exception):
    pass

class EventNotFound(BaseException):
    pass


class EventCategoryNotFound(BaseException):
    pass


class EventSpeakerNotFound(BaseException):
    pass


class BookmarkNotFound(BaseException):
    pass


class BookmarkAlreadyExist(Exception):
    pass


class CountryNotFound(Exception):
    pass


class TicketDiscountNotFound(Exception):
    pass


class TicketTypeDiscountTypeNotFound(Exception):
    pass


class EventReviewNotFound(Exception):
    pass


class EventReviewStreamNotFound(Exception):
    pass


class EventReviewNotFound(Exception):
    pass


class AlreadyDownvoted(Exception):
    pass


class AlreadyUpvoted(Exception):
    pass


class ReviewCommentNotFound(Exception):
    pass


class EventReviewCommentResponseNotFound(Exception):
    pass


class EventSponsorNotFound(Exception):
    pass


class BrandNotFound(Exception):
    pass


class BrandCategoryNotFound(Exception):
    pass


class BrandValidationNotFound(Exception):
    pass


class BrandAlreadyValidated(Exception):
    pass


class TicketNotFound(Exception):
    pass


class TicketAlreadyAssigned(Exception):
    pass


class TicketNotAssigned(Exception):
    pass


class TicketNotAssignedToUser(Exception):
    pass


class TicketTypeNotFound(Exception):
    pass


# User
class UserNotFound(Exception):
    pass


class UserAlreadyExists(Exception):
    pass


class UserIsGhost(Exception):
    pass


# PaymentDetails
class NoPaymentDetailsFound(Exception):
    pass


class PaymentAccountDoesNotExist(Exception):
    pass


class InvalidCardExpirationDateFmt(Exception):
    pass

# UserFollower
class NoFollowersFound(Exception):
    pass


class AlreadyFollowingUser(Exception):
    pass


class NotFollowingUser(Exception):
    pass


class UnvailableTickets(Exception):
    pass


class TicketReservationNotFound(Exception):
    pass


class AlreadyHasTicketsForEvent(Exception):
    pass


class SocialAccountNotFound(Exception):
    pass


class JobNotFound(Exception):
    pass


class AlreadyHasTicketReservation(BaseException):

    def __init__(self, reservation=None, message=None):
        super(AlreadyHasTicketReservation, self).__init__(message)
        self.reservation = reservation


class InsufficientTicketsAvailable(BaseException):

    def __init__(self, ticket_type=None, available_ticket_qty=None, message=None):
        super(InsufficientTicketsAvailable, self).__init__(message)
        self.available_ticket_qty = available_ticket_qty
        self.ticket_type = ticket_type


class MediaNotFound(Exception):
    pass


class PasswordMismatch(Exception):
    pass


class PasswordConfirmationMismatch(Exception):
    pass


class UserNotFound(Exception):
    pass

class UserHasAlreadyUsedPassword(Exception):
    pass