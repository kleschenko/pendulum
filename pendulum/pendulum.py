# -*- coding: utf-8 -*-

from __future__ import division

import re
import time as _time
import math
import calendar
import pytz
import tzlocal
import datetime
import dateparser

from pytz.tzinfo import BaseTzInfo, tzinfo
from dateutil.relativedelta import relativedelta

from .exceptions import PendulumException
from .utils import hybrid_property
from ._compat import PY33


class Pendulum(object):

    # The day constants
    SUNDAY = 0
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6

    # Names of days of the week
    _days = {
        SUNDAY: 'Sunday',
        MONDAY: 'Monday',
        TUESDAY: 'Tuesday',
        WEDNESDAY: 'Wednesday',
        THURSDAY: 'Thursday',
        FRIDAY: 'Friday',
        SATURDAY: 'Saturday'
    }

    # Number of X in Y.
    YEARS_PER_CENTURY = 100
    YEARS_PER_DECADE = 10
    MONTHS_PER_YEAR = 12
    WEEKS_PER_YEAR = 52
    DAYS_PER_WEEK = 7
    HOURS_PER_DAY = 24
    MINUTES_PER_HOUR = 60
    SECONDS_PER_MINUTE = 60

    # Formats
    ATOM = '%Y-%m-%dT%H:%M:%S%P'
    COOKIE = '%A, %d-%b-%Y %H:%M:%S %Z'
    ISO8601 = '%Y-%m-%dT%H:%M:%S%P'
    ISO8601_EXTENDED = '%Y-%m-%dT%H:%M:%S.%f%P'
    RFC822 = '%a, %d %b %y %H:%M:%S %z'
    RFC850 = '%A, %d-%b-%y %H:%M:%S %Z'
    RFC1036 = '%a, %d %b %y %H:%M:%S %z'
    RFC1123 = '%a, %d %b %Y %H:%M:%S %z'
    RFC2822 = '%a, %d %b %Y %H:%M:%S %z'
    RFC3339 = '%Y-%m-%dT%H:%M:%S%P'
    RFC3339_EXTENDED = '%Y-%m-%dT%H:%M:%S.%f%P'
    RSS = '%a, %d %b %Y %H:%M:%S %z'
    W3C = '%Y-%m-%dT%H:%M:%S%P'

    # Default format to use for __str__ method when type juggling occurs.
    DEFAULT_TO_STRING_FORMAT = ISO8601_EXTENDED

    _to_string_format = DEFAULT_TO_STRING_FORMAT

    # First day of week
    _week_starts_at = MONDAY

    # Last day of week
    _week_ends_at = SUNDAY

    # Weekend days
    _weekend_days = [
        SATURDAY,
        SUNDAY
    ]

    _EPOCH = datetime.datetime(1970, 1, 1, tzinfo=pytz.UTC)

    @classmethod
    def _safe_create_datetime_zone(cls, obj):
        """
        Creates a timezone from a string, BaseTzInfo or integer offset.

        :param obj: str or tzinfo or int or None

        :rtype: BaseTzInfo
        """
        if obj is None or obj == 'local':
            return tzlocal.get_localzone()

        if isinstance(obj, tzinfo):
            return obj

        if isinstance(obj, (int, float)):
            timezone_offset = obj * 60

            return pytz.FixedOffset(timezone_offset)

        tz = pytz.timezone(obj)

        return tz

    def __init__(self, year=None, month=None, day=None,
                 hour=None, minute=None, second=None, microsecond=None,
                 tzinfo=pytz.UTC):
        """
        Constructor.

        :type time: str or None

        :type tz: BaseTzInfo or str or None
        """
        self._tz = self._safe_create_datetime_zone(tzinfo)

        now = (datetime.datetime.utcnow()
               .replace(tzinfo=pytz.UTC)
               .astimezone(self._tz))
        if year is None:
            year = now.year

        if month is None:
            month = now.month

        if day is None:
            day = now.day

        if hour is None:
            hour = now.hour
            minute = now.minute if minute is None else minute
            second = now.second if second is None else second
            microsecond = now.microsecond if microsecond is None else microsecond
        else:
            minute = 0 if minute is None else minute
            second = 0 if second is None else second
            microsecond = 0 if microsecond is None else microsecond

        self._year = year
        self._month = month
        self._day = day
        self._hour = hour
        self._minute = minute
        self._second = second
        self._microsecond = microsecond

        self._datetime = self._tz.localize(datetime.datetime(
            year, month, day,
            hour, minute, second, microsecond,
            tzinfo=None
        ))

    @classmethod
    def instance(cls, dt):
        """
        Create a Carbon instance from a datetime one.

        :param dt: A datetime instance
        :type dt: datetime.datetime

        :rtype: Pendulum
        """
        return cls(
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second, dt.microsecond,
            tzinfo=dt.tzinfo
        )

    @classmethod
    def parse(cls, time=None, tz=pytz.UTC):
        """
        Create a Pendulum instance from a string.

        :param time: The time string
        :type time: str

        :param tz: The timezone
        :type tz: BaseTzInfo or str or None

        :rtype: Pendulum
        """
        if time is None:
            return cls(tzinfo=tz)

        if time == 'now':
            return cls(tzinfo=None)

        dt = dateparser.parse(time, languages=['en'])

        if not dt:
            raise PendulumException('Invalid time string "%s"' % time)

        return cls(
            dt.year, dt.month, dt.day,
            dt.hour, dt.minute, dt.second, dt.microsecond,
            tzinfo=tz
        )

    @classmethod
    def now(cls, tz=None):
        """
        Get a Pendulum instance for the current date and time.

        :param tz: The timezone
        :type tz: BaseTzInfo or str or None

        :rtype: Pendulum
        """
        return cls(tzinfo=tz)

    @classmethod
    def utcnow(cls):
        """
        Get a Pendulum instance for the current date and time in UTC.

        :param tz: The timezone
        :type tz: BaseTzInfo or str or None

        :rtype: Pendulum
        """
        return cls.now(pytz.UTC)

    @classmethod
    def today(cls, tz=None):
        """
        Create a Pendulum instance for today.

        :param tz: The timezone
        :type tz: BaseTzInfo or str or None

        :rtype: Pendulum
        """
        return cls.now(tz).start_of_day()

    @classmethod
    def tomorrow(cls, tz=None):
        """
        Create a Pendulum instance for tomorrow.

        :param tz: The timezone
        :type tz: BaseTzInfo or str or None

        :rtype: Pendulum
        """
        return cls.today(tz).add_day()

    @classmethod
    def yesterday(cls, tz=None):
        """
        Create a Pendulum instance for yesterday.

        :param tz: The timezone
        :type tz: BaseTzInfo or str or None

        :rtype: Pendulum
        """
        return cls.today(tz).sub_day()

    # TODO: max_value

    # TODO: min_value

    @classmethod
    def create_from_date(cls, year=None, month=None, day=None, tz=pytz.UTC):
        """
        Create a Pendulum instance from just a date.
        The time portion is set to now.

        :type year: int
        :type month: int
        :type day: int
        :type tz: tzinfo or str or None

        :rtype: Pendulum
        """
        return cls(year, month, day, tzinfo=tz)

    @classmethod
    def create_from_time(cls, hour=None, minute=None, second=None,
                         microsecond=None, tz=pytz.UTC):
        """
        Create a Pendulum instance from just a time.
        The date portion is set to today.

        :type hour: int
        :type minute: int
        :type second: int
        :type microsecond: int
        :type tz: tzinfo or str or int or None

        :rtype: Pendulum
        """
        return cls(hour=hour, minute=minute, second=second,
                   microsecond=microsecond, tzinfo=tz)

    @classmethod
    def create_from_format(cls, time, fmt, tz=pytz.UTC):
        """
        Create a Pendulum instance from a specific format.

        :param fmt: The format
        :type fmt: str

        :param time: The time string
        :type time: str

        :param tz: The timezone
        :type tz: tzinfo or str or int or None

        :rtype: Pendulum
        """
        dt = (datetime.datetime.strptime(time, fmt)
              .replace(tzinfo=cls._safe_create_datetime_zone(tz)))

        return cls.instance(dt)

    @classmethod
    def create_from_timestamp(cls, timestamp, tz=pytz.UTC):
        """
        Create a Pendulum instance from a timestamp.

        :param timestamp: The timestamp
        :type timestamp: int or float

        :param tz: The timezone
        :type tz: tzinfo or str or int or None

        :rtype: Pendulum
        """
        return cls.now(tz).set_timestamp(timestamp)

    @classmethod
    def strptime(cls, time, fmt):
        return cls.create_from_format(time, fmt)

    def copy(self):
        """
        Get a copy of the instance.

        :rtype: Pendulum
        """
        return self.instance(self._datetime)

    ### Getters/Setters

    @hybrid_property
    def year(self):
        return self._datetime.year

    @hybrid_property
    def month(self):
        return self._datetime.month

    @hybrid_property
    def day(self):
        return self._datetime.day

    @hybrid_property
    def hour(self):
        return self._datetime.hour

    @hybrid_property
    def minute(self):
        return self._datetime.minute

    @hybrid_property
    def second(self):
        return self._datetime.second

    @property
    def day_of_week(self):
        return int(self.format('%w'))

    @property
    def day_of_year(self):
        return int(self.format('%-j'))

    @property
    def week_of_year(self):
        return int(self.format('%-W'))

    @property
    def days_in_month(self):
        return calendar.monthrange(self.year, self.month)[1]

    @property
    def timestamp(self):
        return int(self.float_timestamp - self._datetime.microsecond / 1e6)

    @property
    def float_timestamp(self):
        # If Python > 3.3 we use the native function
        # else we emulate it
        if PY33:
            return self._datetime.timestamp()

        if self._datetime.tzinfo is None:
            return _time.mktime((self.year, self.month, self.day,
                                 self.hour, self.minute, self.second,
                                 -1, -1, -1)) + self.microsecond / 1e6

        else:
            return (self._datetime - self._EPOCH).total_seconds()

    @property
    def week_of_month(self):
        return math.ceil(self.day / self.DAYS_PER_WEEK)

    @property
    def age(self):
        return self.diff_in_years()

    @property
    def quarter(self):
        return int(math.ceil(self.month / 3))

    @property
    def offset(self):
        return self.get_offset()

    @property
    def offset_hours(self):
        return int(self.get_offset()
                   / self.SECONDS_PER_MINUTE
                   / self.MINUTES_PER_HOUR)

    @property
    def local(self):
        return self.offset == self.copy().set_timezone(tzlocal.get_localzone()).offset

    @property
    def utc(self):
        return self.offset == 0

    @property
    def timezone(self):
        return self.get_timezone()

    @property
    def timezone_name(self):
        return self.timezone.zone

    def get_timezone(self):
        return self._tz

    def get_offset(self):
        return int(self._datetime.utcoffset().total_seconds())

    def set_date(self, year, month, day):
        """
        Sets the current date to a different date.

        :param year: The year
        :type year: int

        :param month: The month
        :type month: int

        :param day: The day
        :type day: int

        :rtype: Pendulum
        """
        self._datetime = self._datetime.replace(
            year=int(year), month=int(month), day=int(day)
        )

        return self

    def set_time(self, hour, minute, second):
        """
        Sets the current time to a different time.

        :param hour: The hour
        :type hour: int

        :param minute: The minute
        :type minute: int

        :param second: The second
        :type second: int

        :rtype: Pendulum
        """
        self._datetime = self._datetime.replace(
            hour=int(hour), minute=int(minute), second=int(second)
        )

        return self

    def set_date_time(self, year, month, day, hour, minute, second=0):
        """
        Set the date and time all together.

        :type year: int
        :type month: int
        :type day: int
        :type hour: int
        :type minute: int
        :type second: int

        :rtype: Pendulum
        """
        return self.set_date(year, month, day).set_time(hour, minute, second)

    def set_time_from_string(self, time):
        """
        Set the time by time string.

        :param time: The time string
        :type time: str

        :rtype: Pendulum
        """
        time = time.split(':')

        hour = time[0]
        minute = time[1] if len(time) > 1 else 0
        second = time[2] if len(time) > 2 else 0

        return self.set_time(hour, minute, second)

    def set_timezone(self, value):
        """
        Set the instance's timezone from a string or object.

        :param value: The timezone
        :type value: BaseTzInfo or str or None

        :rtype: Pendulum
        """
        self._tz = self._safe_create_datetime_zone(value)
        self._datetime = self._datetime.astimezone(self._tz)

        return self

    def to(self, tz):
        """
        Set the instance's timezone from a string or object.

        :param value: The timezone
        :type value: BaseTzInfo or str or None

        :rtype: Pendulum
        """
        return self.set_timezone(tz)

    def set_timestamp(self, timestamp):
        """
        Set the date and time based on a Unix timestamp.

        :param timestamp: The timestamp
        :type timestamp: int or float

        :rtype: Pendulum
        """
        self._datetime = datetime.datetime.fromtimestamp(timestamp, pytz.UTC).astimezone(self._tz)

        return self

    ### Special week days

    @classmethod
    def get_week_starts_at(cls):
        """
        Get the first day of the week.

        :rtype: int
        """
        return cls._week_starts_at

    @classmethod
    def set_week_starts_at(cls, value):
        """
        Set the first day of the week.

        :type value: int
        """
        cls._week_starts_at = value

    @classmethod
    def get_week_ends_at(cls):
        """
        Get the last day of the week.

        :rtype: int
        """
        return cls._week_ends_at

    @classmethod
    def set_week_ends_at(cls, value):
        """
        Set the last day of the week.

        :type value: int
        """
        cls._week_ends_at = value

    @classmethod
    def get_weekend_days(cls):
        """
        Get weekend days.

        :rtype: list
        """
        return cls._weekend_days

    @classmethod
    def set_weekend_days(cls, value):
        """
        Set weekend days.

        :type value: list
        """
        cls._weekend_days = value

    # TODO: Testing aids

    # TODO: Localization

    @classmethod
    def reset_to_string_format(cls):
        """
        Reset the format used to the default
        when type juggling a Pendulum instance to a string.
        """
        cls.set_to_string_format(cls.DEFAULT_TO_STRING_FORMAT)

    @classmethod
    def set_to_string_format(cls, fmt):
        """
        Set the default format used
        when type juggling a Pendulum instance to a string

        :type fmt: str
        """
        cls._to_string_format = fmt

    def format(self, fmt):
        """
        Formats the Pendulum instance using the given format.

        :param fmt: The format to use
        :type fmt: str

        :rtype: str
        """
        return self.strftime(fmt)

    def strftime(self, fmt):
        """
        Formats the Pendulum instance using the given format.

        :param fmt: The format to use
        :type fmt: str

        :rtype: str
        """
        if not fmt:
            return ''

        # Checking for custom formatters
        custom_formatters = ['P']
        formatters_regex = re.compile('(.*)(?:%%(%s))(.*)' % '|'.join(custom_formatters))

        m = re.match(formatters_regex, fmt)
        if m and m.group(2):
            return self.strftime(m.group(1)) + self._strftime(m.group(2)) + self.strftime(m.group(3))

        return self._datetime.strftime(fmt)

    def _strftime(self, fmt):
        """
        Handles custom formatters in format string.

        :return: str
        """
        if fmt == 'P':
            offset = self._datetime.utcoffset() or datetime.timedelta()
            minutes = offset.total_seconds() / 60

            if minutes > 0:
                sign = '+'
            else:
                sign = '-'

            hour, minute = divmod(abs(int(minutes)), 60)

            return '{0}{1:02d}:{2:02d}'.format(sign, hour, minute)

        raise PendulumException('Unknown formatter %%%s' % fmt)

    def __str__(self):
        return self.format(self._to_string_format)

    def to_date_string(self):
        """
        Format the instance as date.

        :rtype: str
        """
        return self.format('%Y-%m-%d')

    def to_formatted_date_string(self):
        """
        Format the instance as a readable date.

        :rtype: str
        """
        return self.format('%b %d, %Y')

    def to_time_string(self):
        """
        Format the instance as time.

        :rtype: str
        """
        return self.format('%H:%M:%S')

    def to_datetime_string(self):
        """
        Format the instance as date and time.

        :rtype: str
        """
        return self.format('%Y-%m-%d %H:%M:%S')

    def to_day_datetime_string(self):
        """
        Format the instance as day, date and time.

        :rtype: str
        """
        return self.format('%a, %b %d, %Y %-I:%M %p')

    def to_atom_string(self):
        """
        Format the instance as ATOM.

        :rtype: str
        """
        return self.format(self.ATOM)

    def to_cookie_string(self):
        """
        Format the instance as COOKIE.

        :rtype: str
        """
        return self.format(self.COOKIE)

    def to_iso8601_string(self, extended=False):
        """
        Format the instance as ISO8601.

        :rtype: str
        """
        fmt = self.ISO8601
        if extended:
            fmt = self.ISO8601_EXTENDED

        return self.format(fmt)

    def to_rfc822_string(self):
        """
        Format the instance as RFC822.

        :rtype: str
        """
        return self.format(self.RFC822)

    def to_rfc850_string(self):
        """
        Format the instance as RFC850.

        :rtype: str
        """
        return self.format(self.RFC850)

    def to_rfc1036_string(self):
        """
        Format the instance as RFC1036.

        :rtype: str
        """
        return self.format(self.RFC1036)

    def to_rfc1123_string(self):
        """
        Format the instance as RFC1123.

        :rtype: str
        """
        return self.format(self.RFC1123)

    def to_rfc2822_string(self):
        """
        Format the instance as RFC2822.

        :rtype: str
        """
        return self.format(self.RFC2822)

    def to_rfc3339_string(self, extended=False):
        """
        Format the instance as RFC3339.

        :rtype: str
        """
        fmt = self.RFC3339
        if extended:
            fmt = self.RFC3339_EXTENDED

        return self.format(fmt)

    def to_rss_string(self):
        """
        Format the instance as RSS.

        :rtype: str
        """
        return self.format(self.RSS)

    def to_w3c_string(self):
        """
        Format the instance as W3C.

        :rtype: str
        """
        return self.format(self.W3C)

    # TODO: Comparisons

    def add_years(self, value):
        """
        Add years to the instance. Positive $value travel forward while
        negative $value travel into the past.

        :param value: The number of years
        :type value: int

        :rtype: Pendulum
        """
        return self.add(years=value)

    def add_year(self, value=1):
        """
        Add a year to the instance.

        :param value: The number of years
        :type value: int

        :rtype: Pendulum
        """
        return self.add_years(value)

    def sub_years(self, value):
        """
        Remove years from the instance.

        :param value: The number of years
        :type value: int

        :rtype: Pendulum
        """
        return self.sub(years=value)

    def sub_year(self, value=1):
        """
        Remove a year from the instance.

        :param value: The number of years
        :type value: int

        :rtype: Pendulum
        """
        return self.sub_years(value)

    def add_months(self, value):
        """
        Add months to the instance. Positive $value travel forward while
        negative $value travel into the past.

        :param value: The number of months
        :type value: int

        :rtype: Pendulum
        """
        return self.add(months=value)

    def add_month(self, value=1):
        """
        Add a month to the instance.

        :param value: The number of month
        :type value: int

        :rtype: Pendulum
        """
        return self.add_months(value)

    def sub_months(self, value):
        """
        Remove months from the instance.

        :param value: The number of months
        :type value: int

        :rtype: Pendulum
        """
        return self.sub(months=value)

    def sub_month(self, value=1):
        """
        Remove a month from the instance.

        :param value: The number of months
        :type value: int

        :rtype: Pendulum
        """
        return self.sub_months(value)

    # TODO: No overflow

    def add_days(self, value):
        """
        Add days to the instance. Positive $value travel forward while
        negative $value travel into the past.

        :param value: The number of days
        :type value: int

        :rtype: Pendulum
        """
        return self.add(days=value)

    def add_day(self, value=1):
        """
        Add a day to the instance.

        :param value: The number of days
        :type value: int

        :rtype: Pendulum
        """
        return self.add_days(value)

    def sub_days(self, value):
        """
        Remove days from the instance.

        :param value: The number of days
        :type value: int

        :rtype: Pendulum
        """
        return self.sub(days=value)

    def sub_day(self, value=1):
        """
        Remove a day from the instance.

        :param value: The number of days
        :type value: int

        :rtype: Pendulum
        """
        return self.sub_days(value)

    def add_weekdays(self, value):
        """
        Add weekdays to the instance. Positive $value travel forward while
        negative $value travel into the past.

        :param value: The number of weekdays
        :type value: int

        :rtype: Pendulum
        """
        return self.add(weekdays=value)

    def add_weekday(self, value=1):
        """
        Add a weekday to the instance.

        :param value: The number of weekdays
        :type value: int

        :rtype: Pendulum
        """
        return self.add_days(value)

    def sub_weekdays(self, value):
        """
        Remove weekdays from the instance.

        :param value: The number of weekdays
        :type value: int

        :rtype: Pendulum
        """
        return self.sub(weekdays=value)

    def sub_weekday(self, value=1):
        """
        Remove a weekday from the instance.

        :param value: The number of weekdays
        :type value: int

        :rtype: Pendulum
        """
        return self.sub_weekdays(value)

    # TODO: Remaining durations

    def add(self, years=0, months=0, weeks=0, days=0,
            hours=0, minutes=0, seconds=0, microseconds=0,
            weekdays=None):
        """
        Add duration to the instance.

        :param years: The number of years
        :type years: int

        :param months: The number of months
        :type months: int

        :param weeks: The number of weeks
        :type weeks: int

        :param days: The number of days
        :type days: int

        :param hours: The number of hours
        :type hours: int

        :param minutes: The number of minutes
        :type minutes: int

        :param seconds: The number of seconds
        :type seconds: int

        :param microseconds: The number of microseconds
        :type microseconds: int

        :rtype: Pendulum
        """
        delta = relativedelta(
            years=years, months=months, weeks=weeks, days=days,
            hours=hours, minutes=minutes, seconds=seconds,
            microseconds=microseconds, weekday=weekdays
        )
        self._datetime = self._datetime + delta

        return self

    def sub(self, years=0, months=0, weeks=0, days=0,
            hours=0, minutes=0, seconds=0, microseconds=0,
            weekdays=None):
        """
        Remove duration from the instance.

        :param years: The number of years
        :type years: int

        :param months: The number of months
        :type months: int

        :param weeks: The number of weeks
        :type weeks: int

        :param days: The number of days
        :type days: int

        :param hours: The number of hours
        :type hours: int

        :param minutes: The number of minutes
        :type minutes: int

        :param seconds: The number of seconds
        :type seconds: int

        :param microseconds: The number of microseconds
        :type microseconds: int

        :rtype: Pendulum
        """
        delta = relativedelta(
            years=years, months=months, weeks=weeks, days=days,
            hours=hours, minutes=minutes, seconds=seconds,
            microseconds=microseconds, weekday=weekdays
        )
        self._datetime = self._datetime - delta

        return self

    ### Modifiers

    def start_of_day(self):
        """
        Reset the time to 00:00:00

        :rtype: Pendulum
        """
        return self.set_time(0, 0, 0)

    def end_of_day(self):
        """
        Reset the time to 23:59:59

        :rtype: Pendulum
        """
        return self.set_time(23, 59, 59)

    def start_of_month(self):
        """
        Reset the date to the first day of the month and the time to 00:00:00.

        :rtype: Pendulum
        """
        return self.set_date_time(self.year, self.month, 1, 0, 0, 0)

    def end_of_month(self):
        """
        Reset the date to the last day of the month and the time to 23:59:59.

        :rtype: Pendulum
        """
        return self.set_date_time(
            self.year, self.month, self.days_in_month, 23, 59, 59
        )

    def start_of_year(self):
        """
        Reset the date to the first day of the year and the time to 00:00:00.

        :rtype: Pendulum
        """
        return self.set_date_time(self.year, 1, 1, 0, 0, 0)

    def end_of_year(self):
        """
        Reset the date to the last day of the year and the time to 23:59:59.

        :rtype: Pendulum
        """
        return self.set_date_time(
            self.year, 12, 31, 23, 59, 59
        )

    def start_of_decade(self):
        """
        Reset the date to the first day of the decade
        and the time to 00:00:00.

        :rtype: Pendulum
        """
        year = self.year - self.year % self.YEARS_PER_DECADE
        return self.set_date_time(year, 1, 1, 0, 0, 0)

    def end_of_decade(self):
        """
        Reset the date to the last day of the decade
        and the time to 23:59:59.

        :rtype: Pendulum
        """
        year = self.year - self.year % self.YEARS_PER_DECADE + self.YEARS_PER_DECADE - 1

        return self.set_date_time(
            year, 12, 31, 23, 59, 59
        )

    def start_of_century(self):
        """
        Reset the date to the first day of the century
        and the time to 00:00:00.

        :rtype: Pendulum
        """
        year = self.year - 1 - (self.year - 1) % self.YEARS_PER_CENTURY + 1
        return self.set_date_time(year, 1, 1, 0, 0, 0)

    def end_of_century(self):
        """
        Reset the date to the last day of the century
        and the time to 23:59:59.

        :rtype: Pendulum
        """
        year = self.year - 1 - (self.year - 1) % self.YEARS_PER_CENTURY + self.YEARS_PER_CENTURY

        return self.set_date_time(
            year, 12, 31, 23, 59, 59
        )

    def start_of_week(self):
        """
        Reset the date to the first day of the week
        and the time to 00:00:00.

        :rtype: Pendulum
        """
        if self.day_of_week != self._week_starts_at:
            self.previous(self._week_starts_at)

        return self.start_of_day()

    def end_of_week(self):
        """
        Reset the date to the last day of the week
        and the time to 23:59:59.

        :rtype: Pendulum
        """
        if self.day_of_week != self._week_ends_at:
            self.next(self._week_ends_at)

        return self.end_of_day()

    def next(self, day_of_week=None):
        """
        Modify to the next occurrence of a given day of the week.
        If no day_of_week is provided, modify to the next occurrence
        of the current day of the week.  Use the supplied consts
        to indicate the desired day_of_week, ex. Pendulum.MONDAY.

        :param day_of_week: The next day of week to reset to.
        :type day_of_week: int or None

        :rtype: Pendulum
        """
        if day_of_week is None:
            day_of_week = self.day_of_week

        dt = self.start_of_day().add_day()
        while dt.day_of_week != day_of_week:
            dt.add_day()

        return dt

    def previous(self, day_of_week=None):
        """
        Modify to the previous occurrence of a given day of the week.
        If no day_of_week is provided, modify to the previous occurrence
        of the current day of the week.  Use the supplied consts
        to indicate the desired day_of_week, ex. Pendulum.MONDAY.

        :param day_of_week: The previous day of week to reset to.
        :type day_of_week: int or None

        :rtype: Pendulum
        """
        if day_of_week is None:
            day_of_week = self.day_of_week

        dt = self.start_of_day().sub_day()
        while dt.day_of_week != day_of_week:
            dt.sub_day()

        return dt

    def first_of_month(self, day_of_week=None):
        """
        Modify to the first occurrence of a given day of the week
        in the current month. If no day_of_week is provided,
        modify to the first day of the month. Use the supplied consts
        to indicate the desired day_of_week, ex. Pendulum.MONDAY.

        :type day_of_week: int or None

        :rtype: Pendulum
        """
        self.start_of_day()

        if day_of_week is None:
            return self.day(1)

        month = calendar.monthcalendar(self.year, self.month)

        calendar_day = (day_of_week - 1) % 7

        if month[0][calendar_day] > 0:
            day_of_month = month[0][calendar_day]
        else:
            day_of_month = month[1][calendar_day]

        return self.day(day_of_month)

    def last_of_month(self, day_of_week=None):
        """
        Modify to the last occurrence of a given day of the week
        in the current month. If no day_of_week is provided,
        modify to the last day of the month. Use the supplied consts
        to indicate the desired day_of_week, ex. Pendulum.MONDAY.

        :type day_of_week: int or None

        :rtype: Pendulum
        """
        self.start_of_day()

        if day_of_week is None:
            return self.day(self.days_in_month)

        month = calendar.monthcalendar(self.year, self.month)

        calendar_day = (day_of_week - 1) % 7

        if month[-1][calendar_day] > 0:
            day_of_month = month[-1][calendar_day]
        else:
            day_of_month = month[-2][calendar_day]

        return self.day(day_of_month)

    def nth_of_month(self, nth, day_of_week):
        """
        Modify to the given occurrence of a given day of the week
        in the current month. If the calculated occurrence is outside,
        the scope of the current month, then return False and no
        modifications are made. Use the supplied consts
        to indicate the desired day_of_week, ex. Pendulum.MONDAY.

        :type nth: int

        :type day_of_week: int or None

        :rtype: Pendulum
        """
        if nth == 1:
            return self.first_of_month(day_of_week)

        dt = self.copy().first_of_month()
        check = dt.format('%Y-%m')
        for i in range(nth - (1 if dt.day_of_week == day_of_week else 0)):
            dt.next(day_of_week)

        if dt.format('%Y-%m') == check:
            return self.day(dt.day).start_of_day()

        return False

    def first_of_quarter(self, day_of_week=None):
        """
        Modify to the first occurrence of a given day of the week
        in the current quarter. If no day_of_week is provided,
        modify to the first day of the quarter. Use the supplied consts
        to indicate the desired day_of_week, ex. Pendulum.MONDAY.

        :type day_of_week: int or None

        :rtype: Pendulum
        """
        return self.set_date(self.year, self.quarter * 3 - 2, 1).first_of_month(day_of_week)

    def last_of_quarter(self, day_of_week=None):
        """
        Modify to the last occurrence of a given day of the week
        in the current quarter. If no day_of_week is provided,
        modify to the last day of the quarter. Use the supplied consts
        to indicate the desired day_of_week, ex. Pendulum.MONDAY.

        :type day_of_week: int or None

        :rtype: Pendulum
        """
        return self.set_date(self.year, self.quarter * 3, 1).last_of_month(day_of_week)

    def nth_of_quarter(self, nth, day_of_week):
        """
        Modify to the given occurrence of a given day of the week
        in the current quarter. If the calculated occurrence is outside,
        the scope of the current quarter, then return False and no
        modifications are made. Use the supplied consts
        to indicate the desired day_of_week, ex. Pendulum.MONDAY.

        :type nth: int

        :type day_of_week: int or None

        :rtype: Pendulum
        """
        if nth == 1:
            return self.first_of_quarter(day_of_week)

        dt = self.copy().day(1).month(self.quarter * 3)
        last_month = dt.month
        year = dt.year
        dt.first_of_quarter()
        for i in range(nth - (1 if dt.day_of_week == day_of_week else 0)):
            dt.next(day_of_week)

        if last_month < dt.month or year != dt.year:
            return False

        return self.set_date(self.year, dt.month, dt.day).start_of_day()

    def first_of_year(self, day_of_week=None):
        """
        Modify to the first occurrence of a given day of the week
        in the current year. If no day_of_week is provided,
        modify to the first day of the year. Use the supplied consts
        to indicate the desired day_of_week, ex. Pendulum.MONDAY.

        :type day_of_week: int or None

        :rtype: Pendulum
        """
        return self.month(1).first_of_month(day_of_week)

    def last_of_year(self, day_of_week=None):
        """
        Modify to the last occurrence of a given day of the week
        in the current year. If no day_of_week is provided,
        modify to the last day of the year. Use the supplied consts
        to indicate the desired day_of_week, ex. Pendulum.MONDAY.

        :type day_of_week: int or None

        :rtype: Pendulum
        """
        return self.month(self.MONTHS_PER_YEAR).last_of_month(day_of_week)

    def nth_of_year(self, nth, day_of_week):
        """
        Modify to the given occurrence of a given day of the week
        in the current year. If the calculated occurrence is outside,
        the scope of the current year, then return False and no
        modifications are made. Use the supplied consts
        to indicate the desired day_of_week, ex. Pendulum.MONDAY.

        :type nth: int

        :type day_of_week: int or None

        :rtype: Pendulum
        """
        if nth == 1:
            return self.first_of_year(day_of_week)

        dt = self.copy().first_of_year()
        year = dt.year
        for i in range(nth - (1 if dt.day_of_week == day_of_week else 0)):
            dt.next(day_of_week)

        if year != dt.year:
            return False

        return self.set_date(self.year, dt.month, dt.day).start_of_day()

    def __getattr__(self, item):
        return getattr(self._datetime, item)