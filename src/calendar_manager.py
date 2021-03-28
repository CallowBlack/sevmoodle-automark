from datetime import datetime
import pprint


class CalendarManager:

    def __init__(self):
        # Calendar format:
        # year:int -> {
        #   month:int -> {
        #       day:int -> {
        #           "link": (start_time, duration), ...
        #       }
        #   }
        # }
        self.__calendar = {}

    def show(self):
        pprint.pprint(self.__calendar)

    def clear(self):
        self.__calendar.clear()

    def add_event(self, start_timestamp: int, duration: int, link: str):
        year, month, day = self.__time_to_date(start_timestamp)
        if year not in self.__calendar:
            self.__calendar[year] = {}
        if month not in self.__calendar[year]:
            self.__calendar[year][month] = {}
        if day not in self.__calendar[year][month]:
            self.__calendar[year][month][day] = {}
        current_events = self.__calendar[year][month][day]
        current_events[link] = (start_timestamp, duration)

    def get_active_events(self, target_timestamp: int = None) -> list:
        events = []

        if target_timestamp is None:
            target_timestamp = int(datetime.now().timestamp())
        year, month, day = self.__time_to_date(target_timestamp)

        if not self.__has_calendar_date(year, month, day):
            return events

        current_events = self.__calendar[year][month][day]
        for link, event_data in current_events.items():
            start_timestamp, duration = event_data
            if start_timestamp < target_timestamp < start_timestamp + duration:
                events.append(link)
        return events

    def remove_event(self, event_timestamp: int, link: str = None):
        year, month, day = self.__time_to_date(event_timestamp)
        if not self.__has_calendar_date(year, month, day):
            return

        current_events: dict = self.__calendar[year][month][day]
        if link is not None:
            current_events.pop(link, None)
        else:
            for link, event_data in current_events.items():
                start_timestamp, duration = event_data
                if start_timestamp == event_timestamp:
                    del current_events[link]

    def __has_calendar_date(self, year, month, day) -> bool:
        return year in self.__calendar and \
                month in self.__calendar[year] and \
                day in self.__calendar[year][month]

    @staticmethod
    def __time_to_date(timestamp: int) -> (int, int, int):
        date = datetime.fromtimestamp(timestamp)
        return date.year, date.month, date.day
