# FEMA: Emotion-Driven Personification in Generative Agents

## Overview
This repository provides a framework for creating generative agents with enhanced emotional expression and personality traits. The system utilizes GPT models to simulate human-like emotional responses in conversational agents, supporting rich, engaging, and contextually appropriate interactions.

## Features
- **Emotional Perception and Expression**: Agents are capable of perceiving and expressing emotions, enabling more realistic and engaging conversations.
- **Personality Customization**: Each agent can be configured with distinct personality traits, which are reflected in their responses.
- **Contextual Awareness**: Agents respond based on conversation history, ensuring coherent and contextually relevant interactions.

## Requirements
Before running the project, make sure you have Python installed. The required dependencies can be installed from the `requirements.txt` file.

### Installation
1. **Clone the repository**:
    ```bash
    git clone https://github.com/your-repository.git
    cd your-repository
    ```

2. **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure GPT API**:
   - Open the `llm_base.py` file.
   - Add your GPT API credentials (API key) in the designated section:
     ```python
     gpt_api_key = "your_openai_api_key"
     ```

4. **Run the server**:
    ```bash
    python server.py
    ```

## Usage
Once the server is up and running, you can interact with the agents by accessing the provided endpoints or through a web interface. Each agent can be configured with a unique personality, and you can observe how the agent engages in conversations with a mixture of emotional and logical responses.

## Configuration
- **Agents**: Modify or create new agents by adjusting the personality and emotional parameters in the configuration files.
- **Global Context**: The system tracks conversation context and virtual time, which can be used to influence agent responses.

## Contributing
We welcome contributions to this project. Please submit issues, feature requests, or pull requests to help improve the framework.

## License
This project is licensed under the MIT License.

## Acknowledgements
This project leverages OpenAI's GPT models and various other open-source tools. We thank the open-source community for their valuable contributions.

