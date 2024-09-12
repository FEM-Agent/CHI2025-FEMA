import json
import os

from flask import Flask, request, render_template, jsonify

from main import create_data, md5_hash, process, add_post_to_queue

app = Flask(__name__)


def load_tweets(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return preprocess_tweets(json.load(f))
    return []


def load_tweets_with_comments(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return preprocess_tweets(json.load(f), True)
    return []


def load_events(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f]
    return []


def save_events(filename, events):
    with open(filename, 'w', encoding='utf-8') as f:
        for event in events:
            f.write(event + '\n')


def load_agents(filename):
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def save_agents(filename, agents):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(agents, f, ensure_ascii=False, indent=4)


def preprocess_tweets(tweets, individual_comment=False):
    tweet_dict = {}
    root_tweets = []
    max_depth = 0

    for tweet in tweets:
        tweet['comments'] = []
        tweet_dict[tweet['hash_id']] = tweet
        if tweet['depth'] > max_depth:
            max_depth = tweet['depth']

    for tweet in tweets:
        if not individual_comment:
            if tweet['reply_to_hash_id'] is None:
                root_tweets.append(tweet)
            else:
                parent_tweet = tweet_dict.get(tweet['reply_to_hash_id'])
                if parent_tweet:
                    parent_tweet['comments'].append(tweet)
                else:
                    print(f"Warning: Parent tweet with hash_id {tweet['reply_to_hash_id']} not found.")
        else:
            root_tweets.append(tweet)
            if tweet['reply_to_hash_id'] is not None:
                parent_tweet = tweet_dict.get(tweet['reply_to_hash_id'])
                if parent_tweet:
                    parent_tweet['comments'].append(tweet)
                else:
                    print(f"Warning: Parent tweet with hash_id {tweet['reply_to_hash_id']} not found.")

    for tweet in root_tweets:
        tweet['total_comments'] = count_comments(tweet)

    return root_tweets, max_depth


def count_comments(tweet):
    total = len(tweet['comments'])
    for comment in tweet['comments']:
        total += count_comments(comment)
    return total


project_tweets_file = 'Output/Tweets/tweets_4dd1419ab4d3b7ffa58d346f2967fdad.json'
project_events_file = 'Output/events.txt'
project_agents_file = 'Output/Agents/agents_4dd1419ab4d3b7ffa58d346f2967fdad.json'


@app.route('/')
def show_default_tweets():
    tweets, max_depth = load_tweets(project_tweets_file)
    events = load_events(project_events_file)
    agents = load_agents(project_agents_file)
    return render_template('index.html', tweets=tweets, events=events, agents=agents, max_depth=max_depth)


@app.route('/project/<project_name>')
def show_project_tweets(project_name):
    tweets, max_depth = load_tweets(f'Output/Tweets/tweets_{project_name}.json')
    events = load_events(project_events_file)
    agents = load_agents(f'Output/Agents/agents_{project_name}.json')
    return render_template('index.html', tweets=tweets, events=events, agents=agents, max_depth=max_depth)


@app.route('/tweets', methods=['POST'])
def show_tweets():
    tweets_json = request.json
    tweets, max_depth = preprocess_tweets(tweets_json)
    events = load_events(project_events_file)
    agents = load_agents(project_agents_file)
    return render_template('index.html', tweets=tweets, events=events, agents=agents, max_depth=max_depth)


@app.route('/api/tweets', methods=['GET'])
def get_tweets():
    tweets, max_depth = load_tweets(project_tweets_file)
    return jsonify(tweets)


@app.route('/api/events', methods=['POST'])
def save_events_api():
    events = request.json.get('events', [])
    save_events(project_events_file, events)
    return jsonify({"message": "Events saved successfully!"})


@app.route('/api/event_data', methods=['POST'])
def get_event_data():
    event = request.json.get('event', '')
    if isinstance(event, int):
        event = get_line_from_file('Output/events.txt', event)
    event_hash = md5_hash(event)
    print(f'hash:{event_hash}')
    tweets_file = f'Output/Tweets/tweets_{event_hash}.json'
    agents_file = f'Output/Agents/agents_{event_hash}.json'

    if not os.path.exists(tweets_file) or not os.path.exists(agents_file):
        create_data(event_hash)

    tweets, max_depth = load_tweets(tweets_file)
    agents = load_agents(agents_file)

    return jsonify({"tweets": tweets, "agents": agents, "max_depth": max_depth})


def get_line_from_file(file_path, line_number):
    with open(file_path, 'r', encoding='utf-8') as file:
        for current_line_number, line in enumerate(file, start=1):
            if current_line_number == line_number:
                return line.strip()
    raise ValueError("Line number is out of range")


@app.route('/api/update_agent', methods=['POST'])
def update_agent():
    data = request.json
    project_name = request.args.get('project_name')

    content = md5_hash(get_line_from_file('Output/events.txt', int(project_name)))

    agents_file = f'Output/Agents/agents_{content}.json'

    agents = load_agents(agents_file)
    for agent in agents:
        if (
                agent['occupation'] == data.get('occupation') or
                agent['experience'] == data.get('experience') or
                agent['character'] == data.get('character') or
                agent['interest'] == data.get('interest')
        ):
            agent['occupation'] = data.get('occupation')
            agent['experience'] = data.get('experience')
            agent['character'] = data.get('character')
            agent['interest'] = data.get('interest')
            agent['online'] = data.get('online')
            break

    save_agents(agents_file, agents)
    return jsonify({"message": "Agent updated successfully!"})


@app.route('/api/delete_agent', methods=['POST'])
def delete_agent():
    data = request.json
    project_name = request.args.get('project_name')

    content = md5_hash(get_line_from_file('Output/events.txt', int(project_name)))

    agents_file = f'Output/Agents/agents_{content}.json'

    agents = load_agents(agents_file)
    agent_name = data.get('name')

    agents = [agent for agent in agents if agent['name'] != agent_name]

    save_agents(agents_file, agents)
    return jsonify({"message": "Agent deleted successfully!"})


@app.route('/api/add_agent', methods=['POST'])
def add_agent():
    data = request.json
    project_name = request.args.get('project_name')

    content = md5_hash(get_line_from_file('Output/events.txt', int(project_name)))

    agents_file = f'Output/Agents/agents_{content}.json'

    agents = load_agents(agents_file)
    new_agent = {
        "name": data.get('name'),
        "occupation": data.get('occupation'),
        "experience": data.get('experience'),
        "character": data.get('character'),
        "interest": data.get('interest'),
        "experiences": {},
        "has_posted_new_tweet": False,
        "feelings": {},
        "mood": '',
        "online": False
    }
    agents.append(new_agent)

    save_agents(agents_file, agents)
    return jsonify({"message": "Agent added successfully!"})


@app.route('/api/toggle_online_agent', methods=['POST'])
def toggle_online_agent():
    data = request.json
    project_name = request.args.get('project_name')

    content = md5_hash(get_line_from_file('Output/events.txt', int(project_name)))
    agents_file = f'Output/Agents/agents_{content}.json'

    agents = load_agents(agents_file)
    agent_name = data.get('name')
    online_status = data.get('online')

    for agent in agents:
        if agent['name'] == agent_name:
            agent['online'] = online_status
            break

    save_agents(agents_file, agents)
    return jsonify({"message": "Agent online status updated successfully!"})


@app.route('/api/simulate', methods=['POST'])
def simulate():
    data = request.json
    current_depth = data.get('depth')

    project_name = request.args.get('project_name')
    event_content = get_line_from_file('Output/events.txt', int(project_name))

    result = process(event_content, int(current_depth))

    print(f'Simulation completed for event: {event_content} at depth: {current_depth}')

    return jsonify({"message": "Simulation completed!", "result": result})


@app.route('/api/add_post_to_queue', methods=['POST'])
def add_post():
    data = request.json
    project_name = request.args.get('project_name')
    author = data.get('author')
    content = data.get('content')

    event_name = get_line_from_file('Output/events.txt', int(project_name))

    # Call the method from main.py to add the post to the queue
    add_post_to_queue(event_name, content, author)

    return jsonify({"message": "Post added successfully!"})


@app.route('/api/delete_post', methods=['POST'])
def delete_post():
    data = request.json
    project_name = md5_hash(get_line_from_file('Output/events.txt', int(request.args.get('project_name'))))
    hash_id = data.get('hash_id')

    tweets_file = f'Output/Tweets/tweets_{project_name}.json'
    tweets, max_depth = load_tweets_with_comments(tweets_file)

    # Filter out the tweet with the matching hash_id
    updated_tweets = [tweet for tweet in tweets if tweet['hash_id'] != hash_id]

    # Save the updated tweets back to the JSON file
    with open(tweets_file, 'w', encoding='utf-8') as f:
        json.dump(updated_tweets, f, ensure_ascii=False, indent=4)

    return jsonify({"message": "Post deleted successfully!"})


@app.route('/simulation')
def simulation():
    return render_template('simulation.html')


if __name__ == '__main__':
    app.run(debug=False, port=7382)
