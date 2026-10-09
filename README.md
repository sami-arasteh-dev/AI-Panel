# AI Panel

A secure, Flask-based web application providing a unified interface for interacting with OpenAI-compatible Large Language Models. Features user authentication, persistent SQLite storage, multi-model routing, conversation history management, and customizable AI parameters.

## 📋 Table of Contents
- [Features](#-features)
- [Architecture & Structure](#-architecture--structure)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Endpoints](#-api-endpoints)
- [Security & Technical Notes](#-security--technical-notes)
- [Development](#-development)
- [License](#-license)

## ✨ Features
- **User Authentication**: Secure registration and login with `werkzeug` password hashing and server-side session management.
- **Multi-Model Support**: Route requests to OpenAI, Anthropic, Google, Deepseek, or custom OpenAI-compatible endpoints.
- **Conversation Persistence**: Automatic conversation creation, SQLite-backed message storage, and full history retrieval.
- **Context Management**: Configurable memory depth (1–5 message pairs), temperature (0–2), system instructions, and base context.
- **File Attachments**: Support for text-based file uploads (`.txt`, `.csv`, `.md`, `.json`, `.py`, `.js`, `.html`, `.css`) with a 5KB read limit.
- **Secure UI Rendering**: Strict HTML escaping for all user and assistant messages to prevent XSS.
- **Responsive RTL Interface**: Dark-themed dashboard built with Bootstrap 5.3 and Vazirmatn font.

## 🏗 Architecture & Structure
The application follows a lightweight client-server architecture:
- **Frontend**: Server-rendered Jinja2 template (`index.html`) with client-side JavaScript/jQuery for API communication, DOM manipulation, and message formatting.
- **Backend**: Flask REST API handling authentication, chat routing, settings management, and SQLite persistence.
- **Database**: SQLite (`ai_panel.db`) with four tables: `users`, `settings`, `conversations`, `messages`.
- **LLM Integration**: Uses the `openai` Python SDK as an HTTP client proxying to a custom base URL (`https://api.gapgpt.app/v1`).

```
├── app.py                  # Flask backend, routes, DB initialization, LLM proxy
├── index.html              # Frontend UI, auth forms, chat interface, settings, JS logic
├── ai_panel.db             # SQLite database (auto-generated on first run)
└── requirements.txt        # Not provided in source files
```

## 📦 Prerequisites
- Python 3.8+
- `pip` package manager
- (Recommended) Virtual environment

## 🛠 Installation
1. Clone or extract the project files.
2. Install dependencies:
   ```bash
   pip install flask openai werkzeug
   ```
3. Run the application:
   ```bash
   python app.py
   ```
4. Access the interface at `http://localhost:8282`.

## ⚙️ Configuration
- **API Key**: Set via the Settings tab. A default key is hardcoded during registration (`sk-gJI1851Li5z70HphGjIjkxjNGjNGMIGdZ1y3Y4NtI11SvUWa`). Replace this in production.
- **Model Selection**: Choose from predefined options in the dropdown or use custom OpenAI-compatible endpoints.
- **Memory & Temperature**: Adjust via the Settings tab. Memory controls how many recent message pairs are sent to the LLM.
- **System Prompts**: Inject custom instructions or base context for consistent behavior.

## 🚀 Usage
1. **Authentication**: Register on first visit or log in with existing credentials.
2. **Chat**: Enter a message in the input field. Optionally attach a supported text file. Submit via button or `Enter` key.
3. **History**: Navigate to the History tab to view, search, or resume past conversations.
4. **Settings**: Configure API key, model, memory depth, temperature, and system prompts. Changes persist per user.
5. **Logout**: Click the exit button to clear the session.

## 🔌 API Endpoints
| Method | Endpoint                  | Description                                  |
|--------|---------------------------|----------------------------------------------|
| GET    | `/`                       | Renders main interface (auth or dashboard)   |
| POST   | `/auth`                   | Handles login/register with JSON payload     |
| GET    | `/logout`                 | Clears session and redirects to `/`          |
| GET    | `/settings`               | Returns user settings as JSON                |
| POST   | `/settings`               | Updates user settings (JSON payload)         |
| POST   | `/chat`                   | Processes chat message/file, returns AI response |
| GET    | `/history`                | Returns user conversations list              |
| GET    | `/conversation/<id>`      | Returns messages for a specific conversation |

## 🔒 Security & Technical Notes
- **Password Security**: Uses `werkzeug.security.generate_password_hash` and `check_password_hash`.
- **XSS Prevention**: All message content is escaped via `escapeHtml()` before DOM injection. Code blocks are wrapped in `<pre><code>` after escaping.
- **Session Management**: Server-side sessions with `app.secret_key`. Unauthorized routes return `401 Unauthorized`.
- **SQLite Threading**: `check_same_thread=False` is used to allow concurrent Flask request handling.
- **File Handling**: Uploaded files are read as UTF-8 text, truncated to 5000 characters, and appended to the user message.
- **Debug Mode**: Enabled by default in `__main__`. Disable in production (`debug=False`).
- **Hardcoded Default Key**: A placeholder API key is inserted during registration. Update this in `app.py` or enforce user-provided keys only.

## 🧑‍💻 Development
- The frontend uses jQuery 3.6.0 and Bootstrap 5.3.0 via CDN. PrismJS CSS is linked but not utilized in the current JS logic.
- To extend model support, add new options to the `<select>` in `index.html` and ensure the target API follows the OpenAI chat completions format.
- Database schema is auto-initialized on startup. Modify `init_db()` in `app.py` to alter table structures.
- No rate limiting or input validation beyond basic empty checks. Consider adding middleware for production hardening.

## 📄 License
No license file or declaration was provided in the source files. Users should verify usage rights before deployment or modification.

---
*Documentation generated based on provided source files. All claims are strictly derived from observable code and configuration.*
