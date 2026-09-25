# Gemini and OpenAI compatibility

This checkout is patched by the sibling `fullstack-agent` repository. The brain uses an OpenAI-compatible Chat Completions API instead of the Claude Agent SDK.

Set `provider` and `model` in `backtalk.json`. Keep secrets out of that file: use `GEMINI_API_KEY`, `OPENAI_API_KEY`, `AI_API_KEY`, and `FISH_API_KEY` in the launcher's environment. Custom services also need `base_url` in the config. Re-run `fullstack-agent/provider_bridge/patch_backtalk.py` after manually updating Backtalk.

Speech recognition uses Gemini with local Whisper fallback. Speech output is an ordered cloud route: Fish Audio S2.1 Pro Free first, Gemini TTS second. `allow_local_tts_fallback` is an explicit policy switch; the JARVIS configuration keeps it disabled. Fish responses are streamed through an in-memory decoder, and logs report first-audio and total latency without logging credentials or reply text.
