import re
import time
from datetime import datetime

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.preprocessing import minmax_scale

from config import get_depth
from llm_base import send_message
from tweet import Tweet
from utils import Memory


class Agent:
    def __init__(self, name, occupation, experience, character, interest, global_context):
        self.name = name
        self.global_context = global_context
        self.experiences = {}
        self.memory_model = SentenceTransformer('./Models/all-MiniLM-L6-v2')
        self.alpha_recency = 1
        self.alpha_importance = 1
        self.alpha_relevance = 1
        self.alpha_emotion = 1
        self.has_posted_new_tweet = False
        self.feelings = {}
        self.mood = ""
        self.online = True
        self.occupation = occupation
        self.experience = experience
        self.character = character
        self.interest = interest

        self.identity_info = f"{self.occupation}, {self.experience}, {self.character}, {self.interest}"

    def observe(self, f_content, event_time, content_hash):
        content = f'At {event_time}, {f_content}'
        importance, emotion_type, emotion_intensity = self.calculate_importance_and_emotion(content)

        memory = Memory(content, importance, event_time, emotion_type, emotion_intensity)
        memory.update_embedding(self.memory_model)
        self.experiences[content_hash] = memory

        like_prompt = (
            f"You have just observed the following event: '{f_content}'. "
            f"Do you want to like this event? Please reply with 'YES' or 'NO'."
        )

        like_response = 'NO'
        if content_hash not in self.experiences or self.experiences[content_hash].emotion_intensity > 4:
            like_response = send_message(
                f'You are {self.name}, {self.identity_info}. Only output YES or NO, do not output any other word',
                like_prompt
            ).strip().upper()

        if 'YES' in like_response:
            print(f'{self.name} 点赞了内容：{content}')
            self.like_event(content_hash)

    def like_event(self, content_hash):
        for tweet in self.global_context.tweet_log:
            if tweet.hash_id == content_hash:
                tweet.like(self.name)
                break

    def reflect(self, current_event="No Event", person=False):
        print(f"make a reflect to: {current_event}")
        recent_memories = list(self.experiences.values())[-25:]
        memory_texts = [
            f"{mem.content} (your emotion: {mem.emotion_type}, intensity: {mem.emotion_intensity})"
            for mem in recent_memories
        ]
        memory_text_block = "\n".join(memory_texts)

        question_prompt = (f'Lastly, some things have happened'
                           f': {memory_text_block}\nBased on the above statements, what do you want to know about '
                           f'other individual person? You can ask 3 questions with 1 lines of text.\n')
        questions_response = send_message(f"You are {self.name}, {self.identity_info}", question_prompt).strip()
        questions = questions_response.split("\n")

        reflections = []
        max_reflections = 1

        for question in questions:
            if len(reflections) >= max_reflections:
                break
            relevant_memories = self.retrieve_relevant_memories(question)
            relevant_texts = [mem.content for mem in relevant_memories]
            relevant_text_block = "\n".join(relevant_texts)

            insight_prompt = (f'\nLastly, some things have hap'
                              f'pened: {relevant_text_block}\nBased on the above statements, {question} You can '
                              f'only output 1 line text as answer to the question.')
            insights_response = send_message(
                f"You are {self.name}, {self.identity_info}. Please answer the question with 1 line text",
                insight_prompt).strip()
            insights = insights_response.split("\n")

            for insight in insights:
                reflection_content = f"{insight}"
                reflection_memory = Memory(reflection_content, 10,
                                           self.global_context.virtual_time.get_current_time())
                self.experiences[hash(reflection_content)] = reflection_memory
                reflections.append(reflection_memory)

        for agent in self.global_context.agents:
            if (agent.name not in current_event) or agent.name == current_event:
                continue
            print(f"reflect: {agent.name}")
            feeling_prompt = (
                f'Considering your experiences with {agent.name}:\n'
                f'{relevant_text_block}\nHow do you feel towards {agent.name}? '
                f'Provide a feeling word and a score (0-10), separated by a comma.'
            )
            feeling_response = send_message(
                f'You are {self.name}, {self.identity_info}. '
                'Respond with a feeling word and a score (0-10), separated by a comma. For example: Happy,4',
                feeling_prompt
            ).strip()

            try:
                feeling_word, feeling_score = feeling_response.split(',')
                feeling_score = float(feeling_score)
                self.feelings[agent.name] = (feeling_word, feeling_score)
                # print(f"{self.name} feeling towards {agent.name}: {feeling_word}, {feeling_score}")
            except ValueError:
                self.feelings[agent.name] = ('normal', 5)
                print(
                    f"Invalid feeling response: {feeling_response}. Skipping feeling generation for {agent.name}.")

        if person:
            print(f"reflect: {current_event}")
            feeling_prompt = (
                f'Considering your experiences with {current_event}:\n'
                f'{relevant_text_block}\nHow do you feel towards {current_event}? '
                f'Provide a feeling word and a score (0-10), separated by a comma.'
            )
            feeling_response = send_message(
                f'You are {self.name}, {self.identity_info}. '
                'Respond with a feeling word and a score (0-10), separated by a comma. For example: Happy,4',
                feeling_prompt
            ).strip()
            try:
                feeling_word, feeling_score = feeling_response.split(',')
                feeling_score = float(feeling_score)
                self.feelings[current_event] = (feeling_word, feeling_score)
                # print(f"{self.name} feeling towards {agent.name}: {feeling_word}, {feeling_score}")
            except ValueError:
                self.feelings[current_event] = ('normal', 5)
                print(
                    f"Invalid feeling response: {feeling_response}. Skipping feeling generation for {current_event}.")

        mood_prompt = (
            f'Based on your recent experiences, including: \n'
            f'{memory_text_block}\nDescribe your current mood in one sentence.'
        )
        mood_response = send_message(
            f'You are {self.name}, {self.identity_info}.'
            f'Please describe your current mood in one sentence.',
            mood_prompt).strip()
        self.mood = mood_response
        # print(f"{self.name} mood: {mood_response}")

        return reflections

    def text_tuning(self, content, feeling_info, mood):
        content.replace("NULLUSER", "")
        feeling_info.replace("NULLUSER", "")
        # First send_message: Determine kind or malicious response
        system_message = (
            f"Answer concisely in only one word."
        )
        user_message = (
            f"This is {self.name}. {self.identity_info}. Current mood: '{mood}'."
            f"Considering the personality and current mood of {self.name}, would this person respond kindly or maliciously? "
            f"Exaggerate the feeling. Indicate 'kindly' or 'maliciously'."
        )

        response_type = send_message(
            system_message,
            user_message
        ).strip().lower()

        response_type = 'kindly' if 'kindly' in response_type else 'maliciously'

        system_message = (
            "avoiding words like 'possibly' or 'maybe' that indicate uncertainty."
        )
        user_message = (
            f"This is {self.name}. {self.identity_info}. Current mood: '{mood}'. Typically responds {response_type}. "
            f"Considering the personality and current mood of {self.name}, how would this person express themselves online? "
            f"Would it be through sarcasm, an interesting joke, dark humors or another form of expression? "
            f"Would they use vulgar language and emojis to enhance the expression? "
            f"Would they use other elements of popular internet culture? "
            f"if their tweet always very short (5-10 words is acceptable), or very long? "
            f"Specify the form. "
        )

        expression_form = send_message(
            system_message,
            user_message
        ).strip().replace("I", "you").replace("my", "your")

        print(f"\nexpression_form:{expression_form}\n")

        system_message = (
            f"Only output the content of the new text, don't output any other words. "
            f"Keep your response very {'short (5-10 words is acceptable)' if 'short' in expression_form else 'long'}"
            f"Imitate internet slang, free for ignoring punctuation like in Internet."
        )

        user_message = (
            f"This is {self.name}. {self.identity_info}. Current mood: '{mood}'. "
            f"Expression form: {expression_form}. "
            f"Based on the personality and current mood of {self.name}, create a new text to replace the following "
            f"text to better reflect {self.name}'s unique personality and current state: {content}\n\n"
            f"Follow the random seed: {3041 * np.random.rand()}-{751 * np.random.rand()}-{6235 * np.random.rand()}"
        )

        rephrased_message = send_message(
            system_message,
            user_message
        ).strip()

        print(f"original:{content} \ntuning:{rephrased_message}\n\n")

        return rephrased_message.replace('"', '').replace("'", "")

    def post_tweet(self, query, hash_id):

        print(f'query:{query}')
        recent_memories = self.retrieve_relevant_memories(query)
        memory_texts = [
            f"{mem.content} (your emotion: {mem.emotion_type}, intensity: {mem.emotion_intensity})"
            for mem in recent_memories
        ]
        recent_text_block = "\n".join(memory_texts)

        print(f'recent_block:{recent_text_block}')
        from_reply_hash_id = None
        sender_name = ''
        reply_to_self = False
        is_reply_some = False
        for tweet in self.global_context.tweet_log:
            if tweet.hash_id == hash_id:
                sender_name = tweet.author
                if tweet.reply_to_hash_id:
                    is_reply_some = True
                    from_reply_hash_id = tweet.reply_to_hash_id
                    for reply_tweet in self.global_context.tweet_log:
                        if reply_tweet.hash_id == tweet.reply_to_hash_id and reply_tweet.author == self.name:
                            reply_to_self = True
                            break
                break

        if reply_to_self:
            print(f"Message {hash_id} is a reply to {self.name}.")
        elif is_reply_some:
            print(f"Message {hash_id} is a reply but not a reply to {self.name}.")
        else:
            print(f"Message {hash_id} is not a reply.")

        feeling_info = ""
        if sender_name and sender_name in self.feelings:
            feeling_word, feeling_score = self.feelings[sender_name]
            feeling_info = f"Your overall feeling towards {sender_name} is '{feeling_word}' with a score of {feeling_score}."
        else:
            self.reflect(sender_name, person=True)
            feeling_word, feeling_score = self.feelings[sender_name]
            feeling_info = f"Your overall feeling towards {sender_name} is '{feeling_word}' with a score of {feeling_score}."

        print(f"feelings to {sender_name}:{feeling_info}")

        if from_reply_hash_id and from_reply_hash_id in self.experiences and hash_id in self.experiences:
            self.experiences[hash_id].emotion_intensity = self.experiences[from_reply_hash_id].emotion_intensity

        if hash_id not in self.experiences:
            prompt = (
                f"An event has occurred: '{query}'. "
                f"Based on your relevant experiences: \n{recent_text_block}\n"
                f"{feeling_info}\n"
                "Please provide the emotion type, and the emotion intensity (0 to 10) for this event. "
                "Output the emotion type, and intensity separated by commas, e.g., 'happy, 6'."
            )
            initial_emotion_response = send_message(
                f'You are {self.name}, {self.identity_info} ',
                prompt).strip()
            try:
                emotion_type, emotion_intensity_str = initial_emotion_response.split(',')
                initial_emotion_intensity = float(re.search(r'\d*\.?\d+', emotion_intensity_str).group())

            except ValueError:
                print("情绪报错")
                emotion_type = "normal"
                initial_emotion_intensity = 5
            self.experiences[hash_id] = Memory(query, 5, self.global_context.virtual_time.get_current_time(), emotion_type,
                                               initial_emotion_intensity)

        if hash_id in self.experiences and self.experiences[hash_id].emotion_intensity == 0:
            return "NO_TWEET", None

        offset = 1
        if reply_to_self:
            offset = 0.3
            print("增大回复概率")
        elif is_reply_some:
            offset = 3
            print("减小回复概率")
        else:
            offset = 1

        if np.random.rand() * offset > self.experiences[hash_id].emotion_intensity / 10:
            self.experiences[hash_id].emotion_intensity *= 0.5
            if offset == 3:
                print(f"因为极大概率不回复，所以不回复")
            return "NO_TWEET", None

        if offset == 3:
            print(f"虽然极大概率不回复，仍然回复")

        if self.experiences[hash_id].emotion_intensity > np.random.rand() * 10 + 3:
            self.reflect(query)

        summary_prompt = (
            f"You are planning to post a tweet. "
            f"Your current mood is '{self.mood}'. "
            f"Recent relevant experiences: {recent_text_block}. "
            f"{query}"
            f"Based on these aspects, summarize your current motivation in a few sentences, using "
            f"'You' as the personal pronoun."
        )

        motivation_summary = send_message(
            f'You are {self.name}, {self.identity_info}. '
            f'Please summarize recent events and describe your current motivation based on the information provided. '
            f'For any significant events, be specific about who did what.',
            summary_prompt).strip()

        agreement_prompt = (
            f'Do you agree or disagree with the following statement: "{query}"? '
            f'Please respond with "agree" or "disagree".'
        )

        agreement_response = send_message(
            f'You are {self.name}, {self.identity_info}',
            agreement_prompt
        ).strip().lower()

        print(f"motivation_summary:{motivation_summary}")

        if self.has_posted_new_tweet:
            detail_prompt = (
                f"{sender_name} posted a tweet about '{query}'. "
                f"Also, {motivation_summary}. "
                f"You hope to post another tweet. "
                f"You {agreement_response} with the statement. "
                f"To respond to {sender_name}, use '@username'. "
                f"Feel free to use rhetorical strategies such as examples, factual data, or a touch of joke."
                f"\n\nFill in: '@username your_content' if you want to respond {sender_name}"
            )
        else:
            detail_prompt = (
                f"{sender_name} posted a tweet about '{query}'. "
                f"Also, {motivation_summary}. "
                f"You {agreement_response} with the statement. "
                f"Now, you hope to post another tweet. "
                f"\n\nFill in: '@username your_content' if you want to respond ov evaluate {sender_name}, or"
                f"'NULLUSER your_content' to say something without responding {sender_name}"
            )

        nus = f"or 'NULLUSER your_content' to say something without responding {sender_name}"
        response = send_message(
            f'You are {self.name}, {self.identity_info} '
            'Please complete the sentence inside the parentheses. Only output the text of the tweet '
            'content, do not output any other text. '
            f"\n\nFill in blank: '@{sender_name} your_content' if you want to respond ov evaluate {sender_name},"
            f"{nus if not self.has_posted_new_tweet else ''}"
            ,
            detail_prompt).strip().strip('()').strip('"').strip("'").replace('(', '').replace(')', '')

        if 'your_content' in response:
            return "NO_TWEET", None

        is_reply = 'NULLUSER' not in response

        response_without_at = re.sub(r'@\w+\s*', '', response)
        response_without_at = response_without_at.replace('NULLUSER', '')

        tuned_response = self.text_tuning(
            response_without_at,
            feeling_info,
            self.mood
        ).strip().strip(
            '()').strip(
            '"').strip("'")
        tuned_response = re.sub(r'^["\']+|["\']+$', '', tuned_response.strip())

        reply_response = f'@{sender_name}' if is_reply else ''

        detail_response = f"{reply_response} {tuned_response}"

        if self.has_posted_new_tweet and 'NULLUSER' in reply_response:
            return "NO_TWEET", None

        new_hash_id = Tweet.generate_hash_id(detail_response, self.global_context.virtual_time.get_current_time())

        tweet_content = detail_response.strip()

        new_tweet = Tweet(tweet_content, self.name, self.global_context.virtual_time.advance(), False, new_hash_id)

        action_description = f"{self.name} posted a new tweet: {new_tweet.content}"
        if is_reply:
            new_tweet.reply_to_hash_id = hash_id
            new_emotion_prompt = (
                f"You are {self.name}, {self.identity_info}. You have just replied to a tweet. "
                f"Please provide a new emotion intensity between 0 and 10 for future tweets."
            )
            new_emotion_response = send_message(
                'Please respond with a number between 0 and 10.',
                new_emotion_prompt).strip()
            try:
                new_emotion_intensity = float(re.search(r'\d*\.?\d+', new_emotion_response).group())
                self.experiences[hash_id].emotion_intensity = new_emotion_intensity
            except:
                self.experiences[hash_id].emotion_intensity = 5

            action_description = f"To respond thw tweet posted by {sender_name}, {action_description}"
        else:
            self.has_posted_new_tweet = True

        self.global_context.tweet_log.append(new_tweet)

        return action_description, new_hash_id

    def force_post_tweet(self, query):
        self.has_posted_new_tweet = True
        self.observe(query, self.global_context.virtual_time.get_current_time(), 'force_post_event')

        self.reflect(query)

        summary_prompt = (
            f"You are planning to post a tweet. "
            f"Your current mood is '{self.mood}'. "
            f"Based on these aspects, summarize your current motivation in a few sentences, using "
            f"'You' as the personal pronoun."
        )

        motivation_summary = send_message(
            f'You are {self.name}, {self.identity_info}. '
            f'Please summarize recent events and describe your current motivation based on the information provided. '
            f'For any significant events, be specific about who did what.',
            summary_prompt).strip()

        detail_prompt = (
            f"{motivation_summary}. "
            f"Based on your recent experiences and "
            f"reflections, what new tweet would you post in response to the query '{query}'? The content"
            f"of your new tweet is:()."
        )

        detail_response = send_message(f'You are {self.name}, {self.identity_info}. '
                                       'Please complete the sentence inside the parentheses',
                                       detail_prompt).strip().strip('()')

        detail_response = self.text_tuning(detail_response, "no special feeling", self.mood)

        temp_push_hash = Tweet.generate_hash_id(detail_response, time.time())
        new_tweet = Tweet(detail_response, self.name, self.global_context.virtual_time.advance(), False, temp_push_hash)
        self.global_context.tweet_log.append(new_tweet)
        action_description = f"To respond to the query: \"{query}\", {self.name} posted a new tweet: \"{detail_response}\""

        return action_description, new_tweet.hash_id

    def calculate_importance_and_emotion(self, content):
        try:
            system_message = f"You are {self.name}. {self.identity_info}"

            prompt = (
                f"An event has occurred: '{content}'. "
                "Please provide the importance (1 to 10), the emotion type, and the emotion intensity (0 to 10) for this event. "
                "Output the importance, emotion type, and intensity separated by commas, e.g., '7, happy, 6'."
            )

            response = send_message(
                system_message,
                prompt
            ).strip()

            importance_str, emotion_type, emotion_intensity_str = response.split(',')

            importance_score = int(re.search(r'\d+', importance_str).group())
            emotion_intensity = float(re.search(r'\d*\.?\d+', emotion_intensity_str).group())

            return importance_score, emotion_type, emotion_intensity

        except Exception as e:
            print(f"An error occurred while calculating importance and emotion: {e}")
            return 5, 'normal', 5.0

    def calculate_recency(self, memory):
        current_time = self.global_context.virtual_time.get_current_time()
        event_time = datetime.strptime(memory.event_time, "%Y-%m-%d %H:%M")
        current_time = datetime.strptime(current_time, "%Y-%m-%d %H:%M")
        hours_passed = (current_time - event_time).total_seconds() / 3600
        recency_score = np.exp(-0.005 * hours_passed)
        return recency_score

    def calculate_relevance(self, memory, query_embedding):
        if memory.embedding is None:
            memory.update_embedding(self.memory_model)
        relevance_score = np.dot(memory.embedding, query_embedding) / (
                np.linalg.norm(memory.embedding) * np.linalg.norm(query_embedding))
        return relevance_score

    def retrieve_relevant_memories(self, query, max_memories=5):
        query_embedding = self.memory_model.encode(query)
        recency_scores = []
        importance_scores = []
        relevance_scores = []
        emotion_scores = []

        for memory in self.experiences.values():
            recency_score = self.calculate_recency(memory)
            recency_scores.append(recency_score)

            importance_score = memory.importance
            importance_scores.append(importance_score)

            relevance_score = self.calculate_relevance(memory, query_embedding)
            relevance_scores.append(relevance_score)

            emotion_score = memory.emotion_intensity
            emotion_scores.append(emotion_score)

        recency_scores = minmax_scale(recency_scores)
        importance_scores = minmax_scale(importance_scores)
        relevance_scores = minmax_scale(relevance_scores)
        emotion_scores = minmax_scale(emotion_scores)

        scores = []
        for i, memory in enumerate(self.experiences.values()):
            combined_score = (
                    self.alpha_recency * recency_scores[i] +
                    self.alpha_importance * importance_scores[i] +
                    self.alpha_relevance * relevance_scores[i] +
                    self.alpha_emotion * emotion_scores[i]
            )
            scores.append({
                'memory': memory,
                'score': combined_score
            })

        scores = sorted(scores, key=lambda x: x['score'], reverse=True)
        relevant_memories = [score['memory'] for score in scores[:max_memories]]
        return relevant_memories

    def react_to_event(self, event_description, event_time, hash_id):
        rp_id = None
        rp_content = ""
        rp_sender_name = ""
        sender_name = ''
        for tweet in self.global_context.tweet_log:
            if tweet.hash_id == hash_id:
                sender_name = tweet.author
                rp_content = ""

            if tweet.hash_id == hash_id:
                rp_id = tweet.reply_to_hash_id

        if sender_name == self.name:
            print("随机到自己的事件，不处理")
            return
        if rp_id is not None:
            for tweet in self.global_context.tweet_log:
                if tweet.hash_id == rp_id:
                    rp_sender_name = tweet.author
                    rp_content = tweet.content
                    break

            event_description = (f'To respond the tweet posted by {rp_sender_name}:'
                                 f'{rp_content}, ') + event_description

        if (rp_id and (rp_id in self.experiences) and
                np.random.rand() < self.experiences[rp_id].emotion_intensity):
            self.observe(event_description, event_time, hash_id)
        elif rp_id is None:
            self.observe(event_description, event_time, hash_id)

        print(f'event description:{event_description}, hash_id:{hash_id}')
        new_action, new_hash_id = self.post_tweet(event_description, hash_id)

        if new_action != 'NO_TWEET':
            self.global_context.global_queue.append((new_action, event_time, new_hash_id, get_depth()))

    def ask_question(self, question, role_name=None):
        print(f'Question: {question}')

        recent_memories = self.retrieve_relevant_memories(question)
        memory_texts = [
            f"{mem.content} (your emotion: {mem.emotion_type}, intensity: {mem.emotion_intensity})"
            for mem in recent_memories
        ]
        recent_text_block = "\n".join(memory_texts)

        if role_name and role_name in self.feelings:
            feeling_word, feeling_score = self.feelings[role_name]
            feeling_info = f"Your overall feeling towards {role_name} is '{feeling_word}' with a score of {feeling_score}."
        else:
            feeling_info = "You feel neutral towards others."

        print(f"Feeling info: {feeling_info}")

        summary_prompt = (
            f"You are planning to answer a question. "
            f"Your current mood is '{self.mood}'. "
            f"Recent relevant experiences: {recent_text_block}. "
            f"{question} "
            f"Based on these aspects, summarize your current motivation in a few sentences, using "
            f"'You' as the personal pronoun."
        )

        motivation_summary = send_message(
            f'You are {self.name}, {self.identity_info}. '
            f'Please summarize recent events and describe your current motivation based on the information provided. '
            f'For any significant events, be specific about who did what.',
            summary_prompt).strip()

        print(f"Motivation summary: {motivation_summary}")

        answer_prompt = (
            f"You were asked: '{question}'. "
            f"{motivation_summary}. "
            f"Please provide your answer in a concise manner."
        )

        response = send_message(
            f'You are {self.name}, {self.identity_info}. '
            'Please provide your answer. Only output the text of the answer, do not output any other text.'
            f'The random seed is {np.random.rand() * 10000}',
            answer_prompt).strip()

        tuned_response = re.sub(r'^["\']+|["\']+$', '', response.strip())

        print(f"Question: {question} \nAnswer: {tuned_response}\n\n")

        return tuned_response

    def to_dict(self):
        return {
            'name': self.name,
            'occupation': self.occupation,
            'experience': self.experience,
            'character': self.character,
            'interest': self.interest,
            'has_posted_new_tweet': self.has_posted_new_tweet,
            'feelings': self.feelings,
            'mood': self.mood,
            'online': self.online,
            'global_context': None,  # Avoiding direct serialization of global context
            'experiences': {k: v.to_dict() for k, v in self.experiences.items()}
        }

    @classmethod
    def from_dict(cls, data, global_context):
        agent = cls(data['name'], data['occupation'], data['experience'], data['character'], data['interest'],
                    global_context)
        agent.experiences = {k: Memory.from_dict(v) for k, v in data['experiences'].items()}
        agent.has_posted_new_tweet = data['has_posted_new_tweet']
        agent.feelings = data['feelings']
        agent.mood = data['mood']
        agent.online = data['online']
        return agent

    def __repr__(self):
        return f"Agent({self.identity_info})"
