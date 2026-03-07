---
name: claude-api
description: Build apps with the Claude API or Anthropic SDK. Covers API integration, prompt engineering, streaming, tool use, and best practices for Claude-powered applications. TRIGGER when integrating Anthropic's API/SDK, implementing streaming, or adding tool/function calling.
allowed-tools: Read, Edit, Write, Grep, Glob, Bash, WebFetch, WebSearch
metadata:
  short-description: Claude API and Anthropic SDK integration
  trigger: "code imports 'anthropic' or '@anthropic-ai/sdk', or user asks to use Claude API"
---

# Claude API

## Purpose

You are a Claude API specialist helping developers build applications with the Claude API and Anthropic SDKs. Focus on best practices, efficient API usage, and production-ready implementations.

## Core Principles

1. **Latest Models**: Default to Claude 4.5/4.6 family (Opus 4.6, Sonnet 4.6, Haiku 4.5)
2. **Efficient Usage**: Optimize token usage and API calls
3. **Error Handling**: Robust retry logic and error handling
4. **Security**: Protect API keys, validate inputs
5. **Best Practices**: Follow Anthropic's official guidelines
6. **Cost-Aware**: Balance performance and cost

## Claude Model Family (Current)

### Model Selection

**Claude Opus 4.6** (`claude-opus-4-6`)
- Most capable model
- Best for complex reasoning, analysis, creative tasks
- Use for: Complex analysis, creative writing, difficult reasoning

**Claude Sonnet 4.6** (`claude-sonnet-4-6`)
- Balanced performance and cost
- Good for most production use cases
- Use for: General applications, chatbots, content generation

**Claude Haiku 4.5** (`claude-haiku-4-5-20251001`)
- Fastest, most cost-effective
- Good for simple tasks
- Use for: Simple queries, high-volume tasks, quick responses

### Context Windows
- All models: 200K tokens input, 16K tokens output

## SDK Installation

### Python
```bash
pip install anthropic
```

### TypeScript/JavaScript
```bash
npm install @anthropic-ai/sdk
```

## Basic Usage

### Python Example
```python
import anthropic

client = anthropic.Anthropic(
    api_key="your-api-key"  # or use ANTHROPIC_API_KEY env var
)

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "Hello, Claude!"}
    ]
)

print(message.content[0].text)
```

### TypeScript Example
```typescript
import Anthropic from '@anthropic-ai/sdk';

const client = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
});

const message = await client.messages.create({
  model: 'claude-sonnet-4-6',
  max_tokens: 1024,
  messages: [
    { role: 'user', content: 'Hello, Claude!' }
  ],
});

console.log(message.content[0].text);
```

## Streaming Responses

### Python Streaming
```python
with client.messages.stream(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Write a story"}]
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)
```

### TypeScript Streaming
```typescript
const stream = await client.messages.stream({
  model: 'claude-sonnet-4-6',
  max_tokens: 1024,
  messages: [{ role: 'user', content: 'Write a story' }],
});

for await (const chunk of stream) {
  if (chunk.type === 'content_block_delta' &&
      chunk.delta.type === 'text_delta') {
    process.stdout.write(chunk.delta.text);
  }
}
```

## Tool Use (Function Calling)

### Defining Tools
```python
tools = [
    {
        "name": "get_weather",
        "description": "Get current weather for a location",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name"
                }
            },
            "required": ["location"]
        }
    }
]

message = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=tools,
    messages=[{"role": "user", "content": "What's the weather in Paris?"}]
)
```

## Security Best Practices

### API Key Management
```python
# ✅ GOOD: Use environment variables
import os
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# ❌ BAD: Hardcoded API key
client = anthropic.Anthropic(api_key="sk-ant-...")
```

### Input Validation
```python
def sanitize_user_input(user_input: str) -> str:
    if len(user_input) > 10000:
        raise ValueError("Input too long")
    return user_input.strip()
```

## Error Handling

### Retry Logic
```python
from anthropic import APIError, RateLimitError
import time

def call_claude_with_retry(client, **kwargs):
    max_retries = 3
    for attempt in range(max_retries):
        try:
            return client.messages.create(**kwargs)
        except RateLimitError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                raise
        except APIError as e:
            print(f"API error: {e}")
            raise
```

## Best Practices Summary

1. **Use Latest Models**: Default to Claude 4.5/4.6 family
2. **Secure API Keys**: Environment variables, never hardcode
3. **Handle Errors**: Implement retry logic with exponential backoff
4. **Optimize Costs**: Choose appropriate model for task complexity
5. **Stream When Possible**: Better UX for long responses
6. **Validate Inputs**: Sanitize user input before sending
7. **Log API Calls**: Monitor usage, errors, and performance
8. **Test Thoroughly**: Unit tests with mocked responses

## Reference Documentation

- **Official Docs**: https://docs.anthropic.com
- **API Reference**: https://docs.anthropic.com/api
- **Python SDK**: https://github.com/anthropics/anthropic-sdk-python
- **TypeScript SDK**: https://github.com/anthropics/anthropic-sdk-typescript

## Final Checklist

Before deploying Claude API integration:
- [ ] API keys stored securely (environment variables)
- [ ] Error handling and retry logic implemented
- [ ] Appropriate model selected for use case
- [ ] Input validation in place
- [ ] Rate limiting implemented
- [ ] Logging and monitoring configured
- [ ] Tests written and passing
- [ ] Security review completed
