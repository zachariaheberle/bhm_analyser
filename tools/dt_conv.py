

from datetime import datetime,timezone
import datetime as dt
import pytz
def tz_from_utc_ms_ts(utc_ms_ts, tz_info):
    """Given millisecond utc timestamp and a timezone return dateime

    :param utc_ms_ts: Unix UTC timestamp in milliseconds
    :param tz_info: timezone info
    :return: timezone aware datetime
    """
    # convert from time stamp to datetime
    utc_datetime = dt.datetime.utcfromtimestamp(utc_ms_ts / 1000.)

    # set the timezone to UTC, and then convert to desired timezone
    t = utc_datetime.replace(tzinfo=pytz.timezone('UTC')).astimezone(tz_info)
    return t


def get_date_time(utc_code):
    tz_gva = "Europe/Paris"
    tz_UTC = "UTC"
    t = tz_from_utc_ms_ts(utc_code,pytz.timezone(tz_UTC))
    return t

def utc_to_string(utc_code):
    """
    Converts UTC time into string of format day month, year
    """
    t = get_date_time(utc_code)
    return t.strftime("%d %B, %Y")

def tz_to_utc_ms(year, month, day, hour, minute, second):
    """
    Converts year, month, day, etc... to unix timestamp (ms)
    """
    return int(dt.datetime.timestamp(dt.datetime(year, month, day, hour, minute, second, tzinfo=pytz.timezone("UTC"))) * 1000)

def utc_ms_to_orbit(utc_ms, start_time, reference_orbit):
    """
    Converts a utc ms timestamp to an orbit number (given a reference start time (utc ms) and orbit)
    """
    return int((utc_ms - start_time)/(26_659/299_792_458*1000) + reference_orbit)
