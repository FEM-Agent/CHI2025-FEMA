import json
import hashlib
import random
from config import get_depth


class Tweet:
    def __init__(self, content, author, tweet_time, is_retweet=False, hash_id='no hash id input', depth=None):
        self.content = content
        self.author = author
        self.tweet_time = tweet_time
        self.likes = []
        self.hash_id = hash_id
        self.reply_to_hash_id = None
        self.depth = depth if depth is not None else get_depth()

    def like(self, user_name):
        if user_name not in self.likes:
            self.likes.append(user_name)

    @staticmethod
    def generate_hash_id(content, tweet_time):
        random_number = random.randint(0, 1000000)
        hash_input = f"{content}{tweet_time}{random_number}".encode('utf-8')
        return hashlib.md5(hash_input).hexdigest()

    def to_dict(self):
        return {
            'content': self.content,
            'author': self.author,
            'tweet_time': self.tweet_time,
            'likes': self.likes,
            'hash_id': self.hash_id,
            'reply_to_hash_id': self.reply_to_hash_id,
            'depth': self.depth
        }

    @classmethod
    def from_dict(cls, data):
        global global_depth_flag
        tweet = cls(data['content'], data['author'], data['tweet_time'], data['hash_id'])
        tweet.likes = data['likes']
        tweet.hash_id = data.get('hash_id')
        tweet.reply_to_hash_id = data.get('reply_to_hash_id')
        tweet.depth = data.get('depth')

        return tweet

    @staticmethod
    def save_tweets(tweets, filename):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump([tweet.to_dict() for tweet in tweets], f, ensure_ascii=False, indent=4)

    @staticmethod
    def load_tweets(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [Tweet.from_dict(tweet) for tweet in data]
