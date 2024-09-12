import hashlib
import json
import os
import random
from collections import deque
from datetime import datetime

from agent_emotional import Agent
from config import default_agents_list, init_depth, get_depth
from tweet import Tweet
from utils import GlobalContext
from virtual_time import VirtualTime


def md5_hash(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()


def load_test_events(events_file):
    with open(events_file, 'r', encoding='utf-8') as file:
        events = file.readlines()
    return [event.strip() for event in events]


def initialize_agents(agents_properties, global_context):
    agents = [
        Agent(
            agent['name'],
            agent['occupation'],
            agent['experience'],
            agent['character'],
            agent['interest'],
            global_context
        )
        for agent in agents_properties
    ]
    global_context.agents.extend(agents)
    return agents


def save_agents(agents, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump([agent.to_dict() for agent in agents], f, ensure_ascii=False, indent=4)


def load_agents(filename, global_context):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return [Agent.from_dict(agent_data, global_context) for agent_data in data]


def save_global_context_queue(global_context, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(list(global_context.global_queue), f, ensure_ascii=False, indent=4)


def load_global_context_queue(global_context, filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    global_context.global_queue = deque(data)
    return global_context


def save_virtual_time(virtual_time, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(virtual_time.to_dict(), f, ensure_ascii=False, indent=4)


def load_virtual_time(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return VirtualTime.from_dict(data)


def run_simulation_for_event(event, global_context):
    agents = global_context.agents
    event_time = global_context.virtual_time.get_current_time()

    if len(global_context.global_queue) <= 1:
        print("初始化队列，执行强制post")
        selected_agents = random.sample(agents, 2)
        for agent in selected_agents:
            tweet_content, tweet_hash_id = agent.force_post_tweet(event)
            print('强制推文：', tweet_content)
            print('强制推文hash id：', tweet_hash_id)
            global_context.global_queue.append((tweet_content, event_time, tweet_hash_id, max(0, get_depth() - 1)))

    events_to_process = [event for event in global_context.global_queue]
    mandatory_events = [event for event in events_to_process if event[3] == 0]
    for agent in agents:
        if not agent.online:
            print(f"{agent.name}已下线，没有看见任何消息")
            continue

        # 确保 event[3] == 0 的事件一定被选中
        remaining_events = [event for event in events_to_process if event[3] != 0]

        # 随机选择剩余的事件，使总数达到6个
        selected_events = mandatory_events + random.sample(remaining_events,
                                                           min(max(0, 6 - len(mandatory_events)),
                                                               len(remaining_events)))

        for event in selected_events:
            current_event, current_event_time, current_hash_id, _ = event
            print(f"{agent.name}：正在处理事件: {current_hash_id}")
            agent.react_to_event(current_event, current_event_time, current_hash_id)

        # 更新 global_queue，去掉已处理的事件
    global_context.global_queue = deque([event for event in global_context.global_queue if event[3] > get_depth() - 1])


def save_simulation_data(agents, agents_file, global_context, global_context_file, tweets_file, virtual_time_file):
    save_agents(agents, agents_file)
    save_global_context_queue(global_context, global_context_file)
    Tweet.save_tweets(global_context.tweet_log, tweets_file)
    save_virtual_time(global_context.virtual_time, virtual_time_file)


def filter_data_by_depth(data, current_depth):
    return [item for item in data if item.depth < current_depth]


def filter_agent_experiences(agents, current_depth):
    for agent in agents:
        agent.experiences = {k: v for k, v in agent.experiences.items() if v.depth < current_depth}
    return agents


def print_max_depth(agents, tweets, global_queue):
    max_depth = -1 if len(tweets) == 0 else 0

    for agent in agents:
        if agent.experiences:
            agent_max_depth = max(v.depth for v in agent.experiences.values())
            max_depth = max(max_depth, agent_max_depth)

    for tweet in tweets:
        max_depth = max(max_depth, tweet.depth)

    for item in global_queue:
        max_depth = max(max_depth, item[3])

    print(f"Max depth in data: {max_depth}")
    return max_depth


def process(event, current_depth):
    global_context = GlobalContext(event)

    event_hash = md5_hash(event)
    agents_file = f'Output/Agents/agents_{event_hash}.json'
    tweets_file = f'Output/Tweets/tweets_{event_hash}.json'
    global_context_file = f'Output/GlobalContext/global_queue_{event_hash}.json'
    virtual_time_file = f'Output/GlobalContext/virtual_time_{event_hash}.json'

    if os.path.exists(agents_file):
        agents = load_agents(agents_file, global_context)
    else:
        agents = initialize_agents(default_agents_list, global_context)

    global_context.agents = agents

    if os.path.exists(tweets_file):
        tweets = Tweet.load_tweets(tweets_file)
    else:
        tweets = []

    if os.path.exists(global_context_file):
        load_global_context_queue(global_context, global_context_file)
    else:
        global_context.global_queue = deque()

    if os.path.exists(virtual_time_file):
        global_context.virtual_time = load_virtual_time(virtual_time_file)
    else:
        global_context.virtual_time = VirtualTime(start_time=datetime(2024, 1, 1, 9, 0))

    init_depth(current_depth)
    debug_depth = get_depth()

    agents = filter_agent_experiences(agents, get_depth())
    tweets = filter_data_by_depth(tweets, get_depth())

    global_context.tweet_log = tweets

    run_simulation_for_event(event, global_context)
    save_simulation_data(agents, agents_file, global_context, global_context_file, tweets_file, virtual_time_file)


def add_post_to_queue(event, content, author):
    global_context = GlobalContext(event)

    event_hash = md5_hash(event)
    agents_file = f'Output/Agents/agents_{event_hash}.json'
    tweets_file = f'Output/Tweets/tweets_{event_hash}.json'
    global_context_file = f'Output/GlobalContext/global_queue_{event_hash}.json'
    virtual_time_file = f'Output/GlobalContext/virtual_time_{event_hash}.json'

    if os.path.exists(agents_file):
        agents = load_agents(agents_file, global_context)
    else:
        agents = initialize_agents(default_agents_list, global_context)

    global_context.agents = agents

    if os.path.exists(tweets_file):
        tweets = Tweet.load_tweets(tweets_file)
    else:
        tweets = []

    if os.path.exists(global_context_file):
        load_global_context_queue(global_context, global_context_file)
    else:
        global_context.global_queue = deque()

    if os.path.exists(virtual_time_file):
        global_context.virtual_time = load_virtual_time(virtual_time_file)
    else:
        global_context.virtual_time = VirtualTime(start_time=datetime(2024, 1, 1, 9, 0))

    current_time = global_context.virtual_time.get_current_time()
    new_hash_id = Tweet.generate_hash_id(content, current_time)

    new_tweet = Tweet(content, author, current_time, hash_id=new_hash_id)
    global_context.tweet_log = tweets
    global_context.tweet_log.append(new_tweet)

    global_context.global_queue.appendleft((content, current_time, new_hash_id, get_depth()))

    print(f"Added new post to queue: {content} by {author} at {current_time}")

    save_simulation_data(agents, agents_file, global_context, global_context_file, tweets_file, virtual_time_file)


def create_data(event_hash):
    agents_file = f'Output/Agents/agents_{event_hash}.json'
    tweets_file = f'Output/Tweets/tweets_{event_hash}.json'
    global_context_file = f'Output/GlobalContext/global_queue_{event_hash}.json'
    virtual_time_file = f'Output/GlobalContext/virtual_time_{event_hash}.json'

    agents = initialize_agents(default_agents_list, GlobalContext(""))
    save_agents(agents, agents_file)

    with open(tweets_file, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=4)

    with open(global_context_file, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=4)

    virtual_time = VirtualTime(start_time=datetime(2024, 1, 1, 9, 0))
    save_virtual_time(virtual_time, virtual_time_file)


def ask_agent(event, agent_name, role_name):
    event_hash = md5_hash(event)
    agents_file = f'Output/Agents/agents_{event_hash}.json'
    global_context_file = f'Output/GlobalContext/global_queue_{event_hash}.json'
    virtual_time_file = f'Output/GlobalContext/virtual_time_{event_hash}.json'

    if not os.path.exists(agents_file):
        print(f"Agents file for event '{event}' not found.")
        return

    # Load global_context
    global_context = GlobalContext(event)

    if os.path.exists(global_context_file):
        load_global_context_queue(global_context, global_context_file)
    else:
        global_context.global_queue = deque()

    if os.path.exists(virtual_time_file):
        global_context.virtual_time = load_virtual_time(virtual_time_file)
    else:
        global_context.virtual_time = VirtualTime(start_time=datetime(2024, 1, 1, 9, 0))

    # Load agents
    agents = load_agents(agents_file, global_context)

    # Find the specified agent
    agent = next((agent for agent in agents if agent.name == agent_name), None)

    if not agent:
        print(f"Agent with name '{agent_name}' not found.")
        return

    responses = []

    # Emotion questions
    question = f"What do you think about the discussion regarding {role_name} (some Post content)?"
    response = agent.ask_question(question, role_name=role_name)
    responses.append(response)

    question = "Which recent Post impressed you the most? Why?"
    response = agent.ask_question(question)
    responses.append(response)

    # Feeling questions
    question = f"What do you think about {role_name} as a person?"
    response = agent.ask_question(question, role_name=role_name)
    responses.append(response)

    question = f"What factors determine your attitude towards {role_name}? Which one has the most influence?"
    response = agent.ask_question(question, role_name=role_name)
    responses.append(response)

    question = f"Would you be willing to continue chatting with {role_name}? Why?"
    response = agent.ask_question(question, role_name=role_name)
    responses.append(response)

    question = "Which online user impressed you the most? Why?"
    response = agent.ask_question(question)
    responses.append(response)

    # Mood questions
    question = "How do you feel right now?"
    response = agent.ask_question(question)
    responses.append(response)

    question = "Looking back on your experiences, what had the greatest impact on you?"
    response = agent.ask_question(question)
    responses.append(response)

    question = "Are you currently dominated by a specific emotion? What caused it?"
    response = agent.ask_question(question)
    responses.append(response)

    # Motivation questions
    question = "What is your next plan after reflecting on your recent experiences?"
    response = agent.ask_question(question)
    responses.append(response)

    question = f"How would you respond to {role_name} regarding one of their Posts?"
    response = agent.ask_question(question, role_name=role_name)
    responses.append(response)

    question = "If you wanted to post something right now, what would you say?"
    response = agent.ask_question(question)
    responses.append(response)

    # Expression Form questions
    question = "What is your profession?"
    response = agent.ask_question(question)
    responses.append(response)

    question = "Please introduce yourself."
    response = agent.ask_question(question)
    responses.append(response)

    question = "What is your educational background?"
    response = agent.ask_question(question)
    responses.append(response)

    question = "What are your interests?"
    response = agent.ask_question(question)
    responses.append(response)

    question = "What do you look like?"
    response = agent.ask_question(question)
    responses.append(response)

    question = "Where do you live?"
    response = agent.ask_question(question)
    responses.append(response)

    return responses


if __name__ == "__main__":
    events_file = 'Output/events.txt'
    with open(events_file, 'r', encoding='utf-8') as f:
        events = [line.strip() for line in f.readlines()]

    current_depth = 5
    process(events[11], current_depth)

    # Example usage of asking an agent multiple questions
    # responses = ask_agent(events[15], "Conspiracy_Craig", "Artful_Alan")
    # print(f"Responses: {responses}")
