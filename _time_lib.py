import pytz


def sydney_to_utc(sydney_time):
    local_tz = pytz.timezone("Australia/Sydney")
    sydney_time = local_tz.localize(sydney_time)
    target_tz = pytz.timezone("UTC")
    utc_time = target_tz.normalize(sydney_time)
    utc_time = utc_time.strftime("%Y-%m-%d %H:%M")
    return utc_time
