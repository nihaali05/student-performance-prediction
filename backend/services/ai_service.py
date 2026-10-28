import os
import logging


logger = logging.getLogger(__name__)


def _read_env(name, fallback=None):
    value = os.environ.get(name, fallback)
    if value is None:
        return fallback
    return value.strip()


class AIServiceError(RuntimeError):
    """Raised when a configured language model cannot answer a request."""


def _call_gemini(system_prompt, user_prompt, response_mime_type, conversation_history):
    api_key = _read_env('GEMINI_API_KEY') or _read_env('GOOGLE_API_KEY')
    if not api_key:
        raise AIServiceError("The assistant needs an AI API key. Set GEMINI_API_KEY and restart the backend.")

    configured_model = _read_env('GEMINI_MODEL') or 'gemini-3.5-flash'
    candidate_models = [configured_model, 'gemini-3.5-flash', 'gemini-3.8-flash', 'gemini-3.5-flash-lite', 'gemini-flash-latest']
    seen_models = set()
    models_to_try = []
    for m in candidate_models:
        if m and m not in seen_models:
            seen_models.add(m)
            models_to_try.append(m)

    # 1. Primary: Direct HTTPS REST (avoids Windows httpx SSL handshake timeout issues on cellular/broadband IPv6)
    try:
        import requests
        contents = []
        for msg in conversation_history:
            role = 'model' if msg.get('role') == 'assistant' else 'user'
            contents.append({'role': role, 'parts': [{'text': msg.get('content', '')}]})
        contents.append({'role': 'user', 'parts': [{'text': user_prompt}]})

        payload = {'contents': contents}
        if system_prompt:
            payload['systemInstruction'] = {'parts': [{'text': system_prompt}]}

        generation_config = {}
        if response_mime_type == 'application/json':
            generation_config['responseMimeType'] = 'application/json'
        if generation_config:
            payload['generationConfig'] = generation_config

        for model_name in models_to_try:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
                resp = requests.post(
                    url,
                    json=payload,
                    headers={'Content-Type': 'application/json'},
                    timeout=20
                )
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get('candidates', [])
                    if candidates:
                        parts = candidates[0].get('content', {}).get('parts', [])
                        if parts and 'text' in parts[0]:
                            return parts[0]['text'].strip()
                else:
                    logger.warning(f"Gemini REST call for '{model_name}' returned status {resp.status_code}: {resp.text[:150]}")
            except Exception as req_exc:
                logger.warning(f"Gemini REST attempt for '{model_name}' failed: {req_exc}")
                continue
    except Exception as exc:
        logger.warning(f"Gemini REST client error: {exc}")

    # 2. Secondary: google.genai SDK fallback
    try:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=api_key, http_options={'timeout': 20})
        sdk_contents = [
            types.Content(
                role='model' if message.get('role') == 'assistant' else 'user',
                parts=[types.Part.from_text(text=message.get('content', ''))]
            )
            for message in conversation_history
        ]
        sdk_contents.append(types.Content(role='user', parts=[types.Part.from_text(text=user_prompt)]))

        config = {'system_instruction': system_prompt}
        if response_mime_type == 'application/json':
            config['response_mime_type'] = response_mime_type

        for model_name in models_to_try:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=sdk_contents,
                    config=types.GenerateContentConfig(**config)
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as exc:
                logger.warning(f"Gemini SDK call with model '{model_name}' failed: {exc}")
                continue
    except Exception as exc:
        logger.warning(f"Gemini SDK fallback failed: {exc}")

    raise AIServiceError("Gemini could not complete the request. Check your internet connection or try again.")


def _call_openai(system_prompt, user_prompt, response_mime_type, conversation_history):
    from openai import OpenAI

    client = OpenAI(api_key=_read_env('OPENAI_API_KEY'), timeout=15.0)
    messages = [{'role': 'system', 'content': system_prompt}]
    messages.extend(conversation_history)
    messages.append({'role': 'user', 'content': user_prompt})
    kwargs = {'model': 'gpt-4o-mini', 'messages': messages}
    if response_mime_type == 'application/json':
        kwargs['response_format'] = {'type': 'json_object'}
    response = client.chat.completions.create(**kwargs)
    text = response.choices[0].message.content
    return text.strip() if text else None


def _call_grok(system_prompt, user_prompt, response_mime_type, conversation_history):
    from openai import OpenAI

    client = OpenAI(
        api_key=_read_env('GROK_API_KEY') or _read_env('XAI_API_KEY'),
        base_url='https://api.x.ai/v1',
        timeout=15.0
    )
    messages = [{'role': 'system', 'content': system_prompt}]
    messages.extend(conversation_history)
    messages.append({'role': 'user', 'content': user_prompt})
    kwargs = {'model': _read_env('GROK_MODEL') or 'grok-2-latest', 'messages': messages}
    if response_mime_type == 'application/json':
        kwargs['response_format'] = {'type': 'json_object'}
    response = client.chat.completions.create(**kwargs)
    text = response.choices[0].message.content
    return text.strip() if text else None


def call_ai_llm(
    system_prompt,
    user_prompt,
    response_mime_type=None,
    conversation_history=None,
    strict=False
):
    """
    Call the configured language model, optionally preserving a chat conversation.
    Non-strict callers retain the existing rule-based fallback behavior.
    """
    conversation_history = conversation_history or []
    provider = _read_env('AI_PROVIDER', 'auto').lower()
    if provider not in ('auto', 'gemini', 'openai', 'grok'):
        message = "AI_PROVIDER must be set to 'gemini', 'openai', 'grok', or 'auto'."
        if strict:
            raise AIServiceError(message)
        logger.error(message)
        return None

    gemini_key = _read_env('GEMINI_API_KEY') or _read_env('GOOGLE_API_KEY')
    openai_key = _read_env('OPENAI_API_KEY')
    grok_key = _read_env('GROK_API_KEY') or _read_env('XAI_API_KEY')

    last_error = None

    if provider in ('auto', 'gemini') and gemini_key:
        try:
            response = _call_gemini(
                system_prompt, user_prompt, response_mime_type, conversation_history
            )
            if response:
                return response
            raise AIServiceError("Gemini returned an empty response.")
        except Exception as exc:
            logger.exception("Gemini request failed.")
            last_error = exc
            if provider == 'gemini' and strict:
                if isinstance(exc, AIServiceError):
                    raise
                raise AIServiceError(
                    "Gemini could not complete the request. Check the API key and try again."
                ) from exc

    if provider in ('auto', 'grok') and grok_key:
        try:
            response = _call_grok(
                system_prompt, user_prompt, response_mime_type, conversation_history
            )
            if response:
                return response
            raise AIServiceError("Grok returned an empty response.")
        except Exception as exc:
            logger.exception("Grok request failed.")
            last_error = exc
            if provider == 'grok' and strict:
                if isinstance(exc, AIServiceError):
                    raise
                raise AIServiceError(
                    "Grok could not complete the request. Check the API key and try again."
                ) from exc

    if provider in ('auto', 'openai') and openai_key:
        try:
            response = _call_openai(
                system_prompt, user_prompt, response_mime_type, conversation_history
            )
            if response:
                return response
            raise AIServiceError("OpenAI returned an empty response.")
        except Exception as exc:
            logger.exception("OpenAI request failed.")
            last_error = exc
            if provider == 'openai' and strict:
                if isinstance(exc, AIServiceError):
                    raise
                raise AIServiceError(
                    "OpenAI could not complete the request. Check the API key and try again."
                ) from exc

    if strict:
        if provider == 'openai':
            raise AIServiceError(
                "The assistant needs an OpenAI API key. Set OPENAI_API_KEY and restart the backend."
            )
        if provider == 'grok':
            raise AIServiceError(
                "The assistant needs a Grok API key. Set GROK_API_KEY or XAI_API_KEY and restart the backend."
            )
        if gemini_key:
            if isinstance(last_error, AIServiceError):
                raise last_error
            raise AIServiceError(
                "Gemini is currently unavailable. Try again later or set OPENAI_API_KEY or GROK_API_KEY for fallback."
            )
        if grok_key:
            if isinstance(last_error, AIServiceError):
                raise last_error
            raise AIServiceError(
                "Grok is currently unavailable. Try again later or set GEMINI_API_KEY for fallback."
            )
        raise AIServiceError(
            "The assistant needs an AI API key. Set GEMINI_API_KEY/GROK_API_KEY or OPENAI_API_KEY and restart the backend."
        )

    return None
