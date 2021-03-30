from datetime import datetime


def time_to_date(timestamp: int) -> (int, int, int):
    date = datetime.fromtimestamp(timestamp)
    return date.year, date.month, date.day


def clear_html_url(url: str) -> str:
    return url.replace("&amp;", "&")
