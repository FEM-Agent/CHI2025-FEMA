import json
from collections import deque

import numpy as np
from sentence_transformers import SentenceTransformer

from tweet import Tweet
from config import get_depth
from virtual_time import VirtualTime


class Memory:
    def __init__(self, content, importance, event_time, emotion_type=None, emotion_intensity=1, depth=None):
        self.content = content
        self.importance = importance
        self.event_time = event_time
        self.emotion_type = emotion_type
        self.emotion_intensity = emotion_intensity
        self.depth = get_depth()

        self.update_embedding(SentenceTransformer('./Models/all-MiniLM-L6-v2'))

    def update_embedding(self, model):
        self.embedding = model.encode(self.content)

    def to_dict(self):
        return {
            'content': self.content,
            'importance': self.importance,
            'event_time': self.event_time,
            'emotion_type': self.emotion_type,
            'emotion_intensity': self.emotion_intensity,
            'embedding': self.embedding.tolist() if self.embedding is not None else None,
            'depth': self.depth
        }

    @classmethod
    def from_dict(cls, data):
        global global_depth_flag
        memory = cls(
            content=data['content'],
            importance=data['importance'],
            event_time=data['event_time'],
            emotion_type=data['emotion_type'],
            emotion_intensity=data['emotion_intensity'],
            depth=data.get('depth', get_depth())
        )
        if data['embedding'] is not None:
            memory.embedding = np.array(data['embedding'])

        return memory


class GlobalContext:
    def __init__(self, event):
        self.global_queue = deque()
        self.tweet_log = []
        self.event = event
        self.agents = []
        self.current_event_index = 0
        self.virtual_time = VirtualTime()

    def save_global_queue(self, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(list(self.global_queue), f, ensure_ascii=False, indent=4)

    def load_global_queue(self, filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.global_queue = deque(data)

    def load_property(self, events=None, tweets=None):
        if events:
            self.events = events
        if tweets:
            self.tweet_log = tweets

    def load_tweets_from_file(self, tweet_log_file):
        with open(tweet_log_file, 'r', encoding='utf-8') as f:
            tweet_log_data = json.load(f)
            self.tweet_log = [Tweet.from_dict(tweet) for tweet in tweet_log_data]
