# FEMA: Emotion-Driven Personification in Generative Agents

## Overview
This repository contains the code for the FEMA (Feeling-Emotional-Moody Agent) framework, which was developed as part of our research on emotional personification in generative agents. The framework integrates emotional perception, personality traits, and contextual awareness into agents, enabling them to engage in more human-like and emotionally resonant interactions.

This project was submitted to CHI 2025 as part of the paper "FEMA: Emotion-Driven Personification in Generative Agents."

## Features
- **Emotional Perception and Expression**: Agents simulate emotions dynamically, allowing for more realistic interactions.
- **Personality Customization**: The framework supports the customization of agents' emotional states and personality traits.
- **Contextual Awareness**: Agents take conversation history into account to provide coherent and relevant responses.

## Installation

To set up the project, follow these steps:

1. **Clone the repository**:
    ```bash
    git clone https://github.com/FEM-Agent/CHI2025.git
    cd CHI2025
    ```

2. **Install dependencies**:
    The project requires several Python packages that are listed in the `requirements.txt` file. Install them using the following command:
    ```bash
    pip install -r requirements.txt
    ```

3. **Configure GPT API**:
    - Open the `config.py` file in a text editor.
    - Add your GPT API key in the following section:
      ```python
      gpt_api_key = "your_openai_api_key"
      ```

4. **Start the server**:
    Once you've installed the dependencies and configured the API, you can run the server with:
    ```bash
    python server.py
    ```

## Usage
After running the server, agents powered by the FEMA framework will be available for interaction. You can access them via the web interface or API endpoints. Each agent can be configured with specific emotional and personality traits, making their interactions varied and emotionally dynamic.

## Configuration
- **Agent Setup**: You can customize agent profiles by modifying their emotional attributes and behaviors in the respective configuration files.
- **Contextual Data**: The system maintains global context and virtual time, which are factored into the agents' responses, ensuring a contextually relevant dialogue flow.

## Contributions
We welcome contributions! Feel free to submit pull requests, report issues, or suggest features to help improve this framework. Please adhere to the contribution guidelines and ensure that any contributions align with the overall project goals.

## License
This project is licensed under the MIT License. See the [LICENSE](https://github.com/FEM-Agent/CHI2025/blob/main/LICENSE) file for details.

## Acknowledgements
This project was built using OpenAI's GPT models and other open-source tools. We extend our gratitude to the open-source community for their invaluable contributions.

---

For any questions or issues, please feel free to open a discussion or contact us via the repository.
