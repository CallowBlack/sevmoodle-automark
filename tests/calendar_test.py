from src.calendar_manager import CalendarManager
from datetime import datetime
import random

manager = CalendarManager()
test_link_list = [chr(i) for i in range(ord('A'), ord('Z') + 1)]
duration = 90 * 60
for test_link in test_link_list:
    current_timestamp = int(datetime.now().timestamp())
    start_timestamp = random.randrange(current_timestamp - duration + 1, current_timestamp)
    manager.add_event(start_timestamp, duration, test_link)

assert manager.get_active_events() == test_link_list, "Test 1 failed"

print("All test passed")