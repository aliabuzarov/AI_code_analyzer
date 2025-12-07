# LLM API Configuration Guide

## Quick Setup

1. **Edit the `.env` file** and add your API credentials:
   ```bash
   nano .env
   # or
   vim .env
   ```

2. **Set your API URL and key:**
   ```env
   LLM_API_URL=https://api.openai.com/v1/chat/completions
   LLM_API_KEY=sk-your-actual-key-here
   ```

## Provider-Specific Configuration

### Option 1: OpenAI

**In `.env` file:**
```env
LLM_API_URL=https://api.openai.com/v1/chat/completions
LLM_API_KEY=sk-your-openai-api-key-here
LLM_TEMPERATURE=0.7
```

**Then modify `explainers/llm_client.py`** around line 126-135 to use OpenAI format:

```python
# Replace the generic data structure with OpenAI format:
data = {
    "model": "gpt-4",  # or "gpt-3.5-turbo"
    "messages": [{"role": "user", "content": prompt}],
    "temperature": settings.LLM_TEMPERATURE,
    "max_tokens": 2000
}
```

The response parsing already handles OpenAI's format (it looks for `choices[0].message.content`).

### Option 2: Anthropic (Claude)

**In `.env` file:**
```env
LLM_API_URL=https://api.anthropic.com/v1/messages
LLM_API_KEY=sk-ant-your-anthropic-key-here
LLM_TEMPERATURE=0.7
```

**Then modify `explainers/llm_client.py`** around line 126-135:

```python
data = {
    "model": "claude-3-opus-20240229",  # or "claude-3-sonnet-20240229"
    "max_tokens": 2000,
    "messages": [{"role": "user", "content": prompt}]
}

headers = {
    "x-api-key": settings.LLM_API_KEY,
    "anthropic-version": "2023-06-01",
    "Content-Type": "application/json"
}
```

### Option 3: Generic/Custom API

If your API uses the generic format (sends `prompt` in body, returns `text` or `content`), just set:

```env
LLM_API_URL=https://your-api-endpoint.com/v1/chat
LLM_API_KEY=your-api-key-here
```

No code changes needed!

## Testing Your Configuration

1. **Start the server:**
   ```bash
   python manage.py runserver
   ```

2. **Visit** `http://localhost:8000` and try explaining a code snippet

3. **Check for errors** in the terminal - if you see "LLM_API_URL not configured" or "LLM_API_KEY not configured", make sure your `.env` file is correct

## Getting API Keys

- **OpenAI**: https://platform.openai.com/api-keys
- **Anthropic**: https://console.anthropic.com/
- **Other providers**: Check their documentation

## Security Reminder

⚠️ **Never commit your `.env` file to version control!** It's already in `.gitignore`, but double-check before pushing to GitHub.

