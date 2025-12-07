# AI Code Explainer

A Django web application that uses AI to explain code snippets, detect potential errors, and provide improved versions. Supports Python and C++ code.

## Features

- **Code Explanation**: Get plain-language explanations of code snippets
- **Error Detection**: Identify potential bugs, runtime errors, and edge cases
- **Code Improvement**: Receive cleaned and optimized versions of your code
- **Rate Limiting**: Built-in protection against abuse (30 requests per hour per IP)
- **Input Validation**: Size limits and sanitization for security
- **Modern UI**: Clean, responsive interface with CodeMirror editor

## Project Overview

This is a production-ready Django MVP that integrates with external LLM APIs to provide code explanations. The application is designed to be secure, scalable, and easy to deploy.

## Tech Stack

- **Backend**: Django 4.x (Python 3.11+)
- **Frontend**: HTML/CSS/vanilla JavaScript with CodeMirror
- **LLM Integration**: Generic REST API client (configurable for any provider)
- **Database**: SQLite (for development, easily switchable to PostgreSQL)
- **Containerization**: Docker and Docker Compose

## Setup Instructions

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Docker and Docker Compose (optional, for containerized deployment)

### Local Setup (Without Docker)

1. **Clone or navigate to the project directory:**
   ```bash
   cd ai-code-explainer
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and set your configuration:
   ```env
   SECRET_KEY=your-secret-key-here
   DEBUG=True
   LLM_API_URL=https://api.example.com/v1/chat
   LLM_API_KEY=your-api-key-here
   LLM_TEMPERATURE=0.7
   ```

5. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

6. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

7. **Open your browser:**
   Navigate to `http://localhost:8000`

### Docker Setup

1. **Set environment variables:**
   Create a `.env` file (see above) or export them:
   ```bash
   export LLM_API_URL=https://api.example.com/v1/chat
   export LLM_API_KEY=your-api-key-here
   ```

2. **Build and run with Docker Compose:**
   ```bash
   docker-compose up --build
   ```

   The app will be available at `http://localhost:8000`

3. **Stop the containers:**
   ```bash
   docker-compose down
   ```

## Using Makefile Commands

For convenience, a Makefile is provided:

```bash
make install      # Install dependencies
make migrate      # Run database migrations
make runserver    # Start development server
make test         # Run tests
make clean        # Clean Python cache files
make docker-build # Build Docker image
make docker-up    # Start Docker containers
make docker-down  # Stop Docker containers
```

## API Usage

### Endpoint: `POST /api/explain/`

**Request:**
```json
{
  "language": "python",
  "code": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)"
}
```

**Response:**
```json
{
  "explanation": "This code calculates the factorial of a number using recursion...",
  "errors": "- No input validation for negative numbers\n- Stack overflow risk for large numbers",
  "improved_code": "def factorial(n):\n    if n < 0:\n        raise ValueError(\"n must be non-negative\")\n    return 1 if n <= 1 else n * factorial(n - 1)"
}
```

### Example cURL Request

```bash
curl -X POST http://localhost:8000/api/explain/ \
  -H "Content-Type: application/json" \
  -H "X-CSRFToken: your-csrf-token" \
  -d '{
    "language": "python",
    "code": "def sum(n): return sum(range(1, n+1))"
  }'
```

**Note:** For cURL, you'll need to get a CSRF token first. In a browser, the token is automatically handled.

## LLM API Integration

### Configuring Your LLM Provider

The application uses a generic REST API client that can be adapted to any LLM provider. The configuration is done via environment variables:

- `LLM_API_URL`: The endpoint URL for your LLM API
- `LLM_API_KEY`: Your API key (sent as `Authorization: Bearer <key>`)
- `LLM_TEMPERATURE`: Temperature setting (default: 0.7)

### Adapting for Specific Providers

The LLM client (`explainers/llm_client.py`) is designed to work with generic REST APIs. To adapt it for a specific provider:

#### OpenAI Example

Modify the `call_llm_api` function in `explainers/llm_client.py`:

```python
data = {
    "model": "gpt-4",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": settings.LLM_TEMPERATURE
}
headers = {
    "Authorization": f"Bearer {settings.LLM_API_KEY}",
    "Content-Type": "application/json"
}
```

Set environment variables:
```env
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_API_KEY=sk-your-openai-key
```

#### Anthropic Example

```python
data = {
    "model": "claude-3-opus-20240229",
    "max_tokens": 2000,
    "messages": [{"role": "user", "content": prompt}]
}
headers = {
    "x-api-key": settings.LLM_API_KEY,
    "anthropic-version": "2023-06-01",
    "Content-Type": "application/json"
}
```

#### Using a Mock Server for Testing

For testing without a real LLM API, you can use a mock server:

1. **Using httpbin:**
   ```bash
   docker run -p 8080:80 kennethreitz/httpbin
   ```
   Set `LLM_API_URL=http://localhost:8080/post` (note: this won't return proper format, but useful for testing connectivity)

2. **Simple Python mock server:**
   ```python
   from flask import Flask, request, jsonify
   app = Flask(__name__)
   
   @app.route('/api/chat', methods=['POST'])
   def mock_llm():
       return jsonify({
           'text': """### Explanation
   This is a test explanation.
   
   ### Errors
   None
   
   ### Improved Code
   # Improved code here
   """
       })
   
   if __name__ == '__main__':
       app.run(port=5000)
   ```
   Set `LLM_API_URL=http://localhost:5000/api/chat`

### Expected Request/Response Format

**Request Format:**
The client sends a POST request with:
- **Headers:**
  - `Authorization: Bearer <LLM_API_KEY>`
  - `Content-Type: application/json`
- **Body:**
  ```json
  {
    "prompt": "<formatted prompt with code>",
    "temperature": 0.7,
    "max_tokens": 2000
  }
  ```

**Response Format:**
The client expects one of these formats:
- Simple string response
- JSON with `text` or `content` field
- OpenAI-style: `{"choices": [{"message": {"content": "..."}}]}`
- Any JSON that can be converted to string

The response parser looks for markers (`### Explanation`, `### Errors`, `### Improved Code`) to extract structured output.

## Testing

### Running Tests

```bash
python manage.py test
```

Or using pytest (if installed):
```bash
pytest
```

### Test Coverage

The test suite includes:
- API endpoint validation tests
- Input size validation tests
- Prompt building and parsing tests
- Error handling tests

### Mocking LLM Responses

Tests use mocks to simulate LLM API responses. See `explainers/tests/test_api.py` for examples.

## Security Notes

⚠️ **Important Security Considerations:**

1. **Never commit API keys or secrets to version control**
   - Use `.env` file (already in `.gitignore`)
   - Use environment variables in production

2. **Change the default SECRET_KEY in production**
   - Generate a new key: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

3. **Disable DEBUG in production**
   - Set `DEBUG=False` in production
   - Configure `ALLOWED_HOSTS` properly

4. **Code Execution**
   - This app **never executes user code** on the server
   - All code is only sent to the LLM API for analysis

5. **Input Validation**
   - Code length is limited (20 KB default)
   - Line count is limited (500 lines default)
   - Binary/null characters are stripped

6. **Rate Limiting**
   - Default: 30 requests per hour per IP
   - Configure via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW`

## Project Structure

```
ai_code_explainer/
├── README.md
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
├── .env.example
├── .gitignore
├── Makefile
├── explainers/                # Django app
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── serializers.py
│   ├── llm_client.py          # LLM integration
│   ├── middleware.py           # Rate limiting
│   ├── admin.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_api.py
│   │   └── test_prompt.py
│   └── templates/explainers/
│       └── index.html
├── ai_code_explainer/         # Django project settings
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── static/
    ├── css/
    │   └── style.css
    └── js/
        └── main.js
```

## Acceptance Criteria Checklist

✅ `docker-compose up --build` starts the app and serves the homepage  
✅ `POST /api/explain/` with valid snippet returns 200 and JSON with `explanation`, `errors`, `improved_code`  
✅ Unit tests pass  
✅ README explains how to set `LLM_API_URL` for testing with mock server  
✅ All functional requirements implemented  
✅ Security measures in place  
✅ Rate limiting functional  
✅ Input validation working  

## Troubleshooting

### Issue: "LLM_API_URL not configured"
**Solution:** Set the `LLM_API_URL` environment variable in your `.env` file or export it.

### Issue: CSRF token errors
**Solution:** Make sure you're including the CSRF token in API requests. The frontend handles this automatically.

### Issue: Static files not loading
**Solution:** Run `python manage.py collectstatic` or ensure `STATIC_URL` is correctly configured.

### Issue: Rate limit errors (429 Too Many Requests)
**Solution:** 
- **App-level rate limiting:** Adjust `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_WINDOW` in settings or environment variables.
- **LLM API rate limiting (429 errors):** The app automatically retries with exponential backoff. If you're using Google Gemini:
  - Free tier has ~15 requests per minute limit
  - Wait a few minutes before trying again
  - Check your quota at: https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/quotas
  - Consider upgrading your API quota if needed

## License

This project is provided as-is for educational and development purposes.

## Contributing

This is an MVP project. For production use, consider:
- Adding Redis for distributed rate limiting
- Implementing proper logging
- Adding monitoring and analytics
- Setting up CI/CD pipelines
- Adding more comprehensive error handling
- Implementing caching for common requests

---

**Ready to use!** Start by setting up your `.env` file and running `docker-compose up --build` or following the local setup instructions.

