import json
import random
from datetime import datetime, timedelta


class VirtualTime:
    def __init__(self, start_time=None):
        if start_time is None:
            self.current_time = datetime.now()
        else:
            self.current_time = start_time

    def advance(self, minutes=None):
        if minutes is None:
            minutes = random.randint(3, 5)
        self.current_time += timedelta(minutes=minutes)
        return self.current_time.strftime("%Y-%m-%d %H:%M")

    def get_current_time(self):
        return self.current_time.strftime("%Y-%m-%d %H:%M")

    def to_dict(self):
        return {
            'current_time': self.current_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    @classmethod
    def from_dict(cls, data):
        current_time = datetime.strptime(data['current_time'], "%Y-%m-%d %H:%M:%S")
        return cls(start_time=current_time)

    def save_to_file(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)

    @classmethod
    def load_from_file(cls, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)
