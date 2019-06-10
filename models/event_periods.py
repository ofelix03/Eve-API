from datetime import date, datetime, timedelta
import calendar


DAYS_IN_WEEK = 7
DAYS_IN_MONTHS = [None, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


class EventPeriods:
    TODAY = 'today'
    TOMORROW = 'tomorrow'
    THIS_WEEK = 'this_week'
    NEXT_WEEK = 'next_week'
    THIS_MONTH = 'this_month'
    NEXT_MONTH = 'next_month'
    THIS_YEAR = 'this_year'
    NEXT_YEAR = 'next_year'
    PERIODS = [TODAY, TOMORROW, THIS_WEEK, NEXT_WEEK, THIS_MONTH, NEXT_MONTH, THIS_YEAR, NEXT_YEAR]

    @staticmethod
    def parse(period):
        # replaces all white spaces to a single white space, and replace the white spaces with an underscore
        # 1. Strip left and right whitespace
        # 2. Replace the first white space occurance with an underscore(_)
        # 3. Remove any remaining white space
        return period.strip().replace(" ", "_", 1).replace(" ", "").lower()

    @classmethod
    def get_date(cls, period):
        period = cls.parse(period)
        if period in cls.PERIODS:
            method_name = "".join(['get_', period])
            return getattr(cls, method_name)()

    @classmethod
    def get_today(cls):
        return {
            'period': cls.TODAY,
            'value': date.today()
        }

    @classmethod
    def get_tomorrow(cls):
        return {
            'period': cls.TOMORROW,
            'value': date.today() + timedelta(days=1)
        }

    @classmethod
    def get_this_week(cls):
        today = date.today()
        week_end_date = cls.get_next_week()['value'] - timedelta(days=1)
        week_start_date = week_end_date - timedelta(days=6)
        return {
            'period': cls.THIS_WEEK,
            'value': (week_start_date, week_end_date)
        }

    @classmethod
    def get_next_week(cls):
        remaining_days_in_week = DAYS_IN_WEEK - date.today().weekday()
        return {
            'period': cls.NEXT_WEEK,
            'value': date.today() + timedelta(days=remaining_days_in_week)
        }

    @classmethod
    def get_this_month(cls):
        today = date.today()
        month = today.month
        year = today.year
        if month == 2 and calendar.isleap(year):
            days = 29
        else:
            days = DAYS_IN_MONTHS[month]

        return {
            'period': cls.THIS_MONTH,
            'value':  (today.replace(day=1), today.replace(day=days))
        }

    @classmethod
    def get_next_month(cls):
        today = date.today()
        if today.month == 12:
            month = 1
            year = today.year + 1
        else:
            month = today.month + 1
            year = today.year

        next_month_start_date = today.replace(year=year, month=month, day=1)
        next_month_end_date = today.replace(year, month, DAYS_IN_MONTHS[month])
        return {
            'period': cls.NEXT_MONTH,
            'value': (next_month_start_date, next_month_end_date)
        }

    @classmethod
    def get_this_year(cls):
        today = date.today()
        return {
            'period': cls.THIS_YEAR,
            'value': (today.replace(today.year, 1, 1), today.replace(today.year, 12, 31))
        }

    @classmethod
    def get_next_year(cls):
        today = date.today()
        return {
            'period': cls.THIS_YEAR,
            'value': (today.replace(today.year+1, 1, 1), today.replace(today.year+1, 12, 31))
        }