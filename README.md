# RepoChat - Multi-Agent Code Analysis

RepoChat is an AI-powered application that allows you to chat with GitHub repositories using different specialized agents. It provides intelligent code analysis, design assistance, and code generation capabilities.

## 🚀 Features

- **Multiple Agent Modes**:
  - **Codebase Q&A** (❓): Ask questions about the repository code
  - **Low-Level Design** (📐): Get design plans for new features
  - **Code Generation** (👨‍💻): Generate implementation code for features
  - **Code Changes** (🔄): Analyze changes between branches

- **Easy Repository Integration**: Simply paste a GitHub repository URL to start analyzing
- **Streamlit UI**: Clean, interactive interface for seamless interaction
- **Powered by Google Gemini**: Leverages advanced AI for code understanding

## 🛠️ Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/chat-with-repo.git
   cd chat-with-repo
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up your Google Gemini API keys in a `.streamlit/secrets.toml` file:
   ```toml
   GOOGLE_API_KEY_1 = "your-api-key-1"
   GOOGLE_API_KEY_2 = "your-api-key-2"
   GOOGLE_API_KEY_3 = "your-api-key-3"
   GOOGLE_API_KEY_4 = "your-api-key-4"
   GOOGLE_API_KEY_5 = "your-api-key-5"
   ```

## 🚀 Usage

1. Run the Streamlit app:
   ```bash
   streamlit run main.py
   ```

2. Open your browser at `http://localhost:8501`

3. Enter a GitHub repository URL in the sidebar

4. Select an agent mode based on your needs

5. Start chatting with the repository!

## 🐳 Docker Deployment

You can also run RepoChat using Docker:

```bash
docker build -t repochat-app .
docker run -p 8503:8503 repochat-app
```

## 📁 Project Structure

- `main.py`: Main Streamlit application
- `agents.py`: Implementation of different agent types
- `repo_utils.py`: Utilities for repository handling
- `search_utils.py`: Utilities for searching and formatting
- `chat_utils.py`: Utilities for chat functionality

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.