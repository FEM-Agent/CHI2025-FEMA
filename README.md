# FEMA: Emotion-Driven Personification in Generative Agents

## Overview
This repository contains the implementation of the FEMA framework, which enables generative agents to exhibit human-like emotional perception and expression. The goal of FEMA is to enhance the realism of agents by incorporating emotional variability and personality-driven responses, making interactions more engaging and contextually relevant.

This project is part of the **CHI 2025** paper submission titled *"FEMA: Emotion-Driven Personification in Generative Agents."*

## Features
- **Emotion Perception and Expression**: Agents perceive and express a range of emotions, ensuring human-like interactions.
- **Personality Customization**: Each agent can be tailored to a specific personality, influencing their behavior and responses.
- **Contextual Awareness**: The framework leverages conversation history and virtual time, ensuring agents' responses are coherent and emotionally consistent.

## Installation

Follow these steps to install and run the project:

1. **Clone the repository**:
    ```bash
    git clone https://github.com/FEM-Agent/CHI2025-FEMA.git
    cd CHI2025-FEMA
    ```

2. **Install dependencies**:
    Install all necessary Python packages from the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure GPT API**:
   - Open the `config.py` file.
   - Add your GPT API credentials (API key) in the following section:
     ```python
     gpt_api_key = "your_openai_api_key"
     ```

4. **Run the server**:
    ```bash
    python server.py
    ```

## Usage
After running the server, you can interact with the agents via provided API endpoints or the web interface. The system allows for agent configuration and personalization, enabling you to observe how they respond to various scenarios with emotional and logical coherence.

## Configuration
- **Agents**: Define and modify agents' emotional states, personalities, and behavior in the configuration files.
- **Global Context**: The system tracks virtual time and conversation history, which influences how agents generate responses based on their mood and experiences.

## Contributions
We encourage contributions from the community. Feel free to submit issues, feature requests, or pull requests to help improve the framework.

## License
This project is licensed under the MIT License. See the `LICENSE` file for more details.

## Acknowledgements
This project uses OpenAI's GPT models and other open-source libraries. Special thanks to the open-source community for their continuous contributions.
