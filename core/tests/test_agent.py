import asyncio
import os
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

import agent


class RecycleIntentTests(unittest.TestCase):
    def test_explicit_created_file_delete_only(self):
        for prompt in ("delete my recent presentation", "recycle the PDF report",
                       "ye deck hatao", "presentation delete karo"):
            with self.subTest(prompt=prompt):
                self.assertTrue(agent.explicit_recycle_request(prompt))
        for prompt in ("don't delete the presentation", "report delete mat karo",
                       "list my presentations", "delete an arbitrary file"):
            with self.subTest(prompt=prompt):
                self.assertFalse(agent.explicit_recycle_request(prompt))

    def test_presentation_action_is_distinct_from_a_how_to_question(self):
        self.assertTrue(agent.explicit_presentation_creation(
            "Types of AI pe presentation banani hai"))
        self.assertTrue(agent.explicit_presentation_creation(
            "Create a professional PowerPoint about AI"))
        self.assertFalse(agent.explicit_presentation_creation(
            "How to create a presentation?"))
        self.assertFalse(agent.explicit_presentation_creation(
            "Don't make a presentation"))


class ProviderConfigTests(unittest.TestCase):
    def test_gemini_is_inferred_from_its_key(self):
        env = {
            "GEMINI_API_KEY": "test-key",
            "OPENAI_API_KEY": "",
            "AI_API_KEY": "",
            "AI_PROVIDER": "",
        }
        with patch.dict(os.environ, env, clear=False):
            config = agent.ProviderConfig.from_env()
        self.assertEqual(config.provider, "gemini")
        self.assertEqual(config.base_url, agent.GEMINI_BASE_URL)
        self.assertTrue(config.model.startswith("gemini-"))

    def test_custom_provider_requires_base_url(self):
        with patch.dict(os.environ, {"AI_API_KEY": "test", "AI_BASE_URL": ""}, clear=True):
            with self.assertRaisesRegex(ValueError, "AI_BASE_URL"):
                agent.ProviderConfig.from_env("compatible", "model")

    def test_openai_automatically_gets_gemini_fallback(self):
        env = {
            "OPENAI_API_KEY": "openai-test-key",
            "GEMINI_API_KEY": "gemini-test-key",
            "AI_FALLBACK_PROVIDER": "",
            "AI_MODEL": "",
            "GEMINI_MODEL": "gemini-test-model",
        }
        with patch.dict(os.environ, env, clear=True):
            primary = agent.ProviderConfig.from_env("openai", "openai-test-model")
            fallback = agent.fallback_config_from_env(primary)
        self.assertIsNotNone(fallback)
        self.assertEqual(fallback.provider, "gemini")
        self.assertEqual(fallback.model, "gemini-test-model")


class FakeAgent(agent.LocalAgent):
    def __init__(self, *args, replies, **kwargs):
        super().__init__(*args, **kwargs)
        self.replies = iter(replies)

    async def _request(self):
        return next(self.replies)


class ToolLoopTests(unittest.IsolatedAsyncioTestCase):
    async def test_presentation_nudge_uses_output_shelf_and_reports_real_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = agent.ProviderConfig("openai", "test", agent.OPENAI_BASE_URL, "test-model")
            replies = [
                {"content": "I need permission to create a folder."},
                {"content": None, "tool_calls": [{"id": "deck-1", "type": "function",
                    "function": {"name": "professional_topic_presentation", "arguments":
                                 '{"topic":"Types of AI","output_path":"JARVIS/output/ai.pptx"}'}}]},
                {"content": "I need permission to create a folder."},
            ]
            runner = FakeAgent(config, Path(tmp), "instructions", auto_approve=True, replies=replies)
            with patch.object(runner.mark2, "execute",
                              return_value="error: fewer than two independent public pages were readable") as execute:
                answer = await runner.ask("Types of AI pe presentation banani hai")
            execute.assert_called_once_with("professional_topic_presentation", {"topic": "Types of AI"})
            self.assertIn("fewer than two independent public pages", answer)
            self.assertNotIn("permission", answer.casefold())

    async def test_presentation_keeps_a_user_named_output_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = agent.ProviderConfig("openai", "test", agent.OPENAI_BASE_URL, "test-model")
            runner = agent.LocalAgent(config, Path(tmp), "instructions", auto_approve=True)
            path = str(Path(tmp) / "deck.pptx")
            runner._current_request = f"Create a presentation at {path}"
            args = {"topic": "Types of AI", "output_path": path}
            with patch.object(runner.mark2, "execute", return_value="error: fixture") as execute:
                await runner._run_tool("professional_topic_presentation", args)
            execute.assert_called_once_with("professional_topic_presentation", args)

    async def test_voice_recycle_tool_requires_explicit_current_turn_request(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = agent.ProviderConfig("openai", "test", agent.OPENAI_BASE_URL, "test-model")
            runner = agent.LocalAgent(config, Path(tmp), "instructions", auto_approve=True)
            args = {"id": "reports/demo.pdf", "version": "1:2"}
            with patch.object(runner.mark2, "execute", return_value="recycled and verified: reports/demo.pdf") as execute:
                denied = await runner._run_tool("recycle_created_file", args)
                self.assertIn("explicit user request", denied)
                execute.assert_not_called()
                runner._recycle_created_file_requested = True
                allowed = await runner._run_tool("recycle_created_file", args)
                self.assertIn("recycled and verified", allowed)
                execute.assert_called_once_with("recycle_created_file", args)

    async def test_tool_call_writes_and_returns_final_answer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = agent.ProviderConfig("openai", "test", agent.OPENAI_BASE_URL, "test-model")
            replies = [
                {
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call-1",
                            "type": "function",
                            "function": {
                                "name": "write_file",
                                "arguments": '{"path":"hello.txt","content":"hello"}',
                            },
                        }
                    ],
                },
                {"content": "Done."},
            ]
            runner = FakeAgent(config, root, "instructions", auto_approve=True, replies=replies)
            answer = await runner.ask("write it")
            self.assertEqual(answer, "Done.")
            self.assertEqual((root / "hello.txt").read_text(), "hello")
            self.assertEqual(runner.messages[-2]["role"], "tool")

    async def test_mutating_tool_is_denied_without_approval(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = agent.ProviderConfig("openai", "test", agent.OPENAI_BASE_URL, "test-model")
            runner = agent.LocalAgent(config, root, "instructions")
            result = await runner._run_tool("write_file", {"path": "no.txt", "content": "no"})
            self.assertEqual(result, "denied by user")
            self.assertFalse((root / "no.txt").exists())

    async def test_run_command_does_not_inherit_provider_keys(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = agent.ProviderConfig("openai", "test", agent.OPENAI_BASE_URL, "test-model")
            runner = agent.LocalAgent(config, Path(tmp), "instructions", auto_approve=True)
            completed = __import__("subprocess").CompletedProcess([], 0, "ok")
            secrets = {
                "OPENAI_API_KEY": "openai-secret",
                "GEMINI_API_KEY": "gemini-secret",
                "GOOGLE_API_KEY": "google-secret",
                "ELEVENLABS_API_KEY": "voice-secret",
                "FISH_API_KEY": "fish-secret",
                "FISH_AUDIO_API_KEY": "fish-audio-secret",
                "AI_API_KEY": "compatible-secret",
            }
            with patch.dict(os.environ, secrets, clear=False), patch(
                "agent.subprocess.run", return_value=completed
            ) as mocked:
                result = await runner._run_tool("run_command", {"command": "echo ok"})
            self.assertIn("exit code: 0", result)
            child_env = mocked.call_args.kwargs["env"]
            for name in secrets:
                self.assertNotIn(name, child_env)

    async def test_failed_turn_is_removed_from_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = agent.ProviderConfig("openai", "test", agent.OPENAI_BASE_URL, "test-model")
            runner = agent.LocalAgent(config, Path(tmp), "instructions")
            with patch.object(runner, "_request", side_effect=RuntimeError("offline")):
                with self.assertRaisesRegex(RuntimeError, "offline"):
                    await runner.ask("stale question")
            self.assertEqual([message["role"] for message in runner.messages], ["system"])

    async def test_compaction_preserves_complete_recent_turns(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = agent.ProviderConfig("openai", "test", agent.OPENAI_BASE_URL, "test-model")
            runner = agent.LocalAgent(config, Path(tmp), "instructions")
            for number in range(4):
                runner.messages.extend([
                    {"role": "user", "content": f"question {number}"},
                    {"role": "assistant", "content": f"answer {number}"},
                ])
            runner.compact(2)
            self.assertEqual(runner.messages[1]["content"], "question 2")
            self.assertEqual([m["role"] for m in runner.messages[1:]],
                             ["user", "assistant", "user", "assistant"])


class HttpRequestTests(unittest.IsolatedAsyncioTestCase):
    async def test_chat_completions_endpoint_and_bearer_auth(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"choices":[{"message":{"role":"assistant","content":"hello"}}]}'

        config = agent.ProviderConfig("gemini", "secret-test-key", "https://example.test/v1", "test-model")
        runner = agent.LocalAgent(config, Path.cwd(), "instructions")
        with patch("urllib.request.urlopen", return_value=Response()) as mocked:
            message = await runner._request()
        request = mocked.call_args.args[0]
        payload = __import__("json").loads(request.data)
        self.assertEqual(request.full_url, "https://example.test/v1/chat/completions")
        self.assertEqual(request.get_header("Authorization"), "Bearer secret-test-key")
        self.assertEqual(payload["model"], "test-model")
        self.assertEqual(message["content"], "hello")

    async def test_failed_openai_request_switches_to_gemini(self):
        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

            def read(self):
                return b'{"choices":[{"message":{"role":"assistant","content":"fallback"}}]}'

        primary = agent.ProviderConfig("openai", "openai-key", "https://openai.test/v1", "gpt-test")
        fallback = agent.ProviderConfig("gemini", "gemini-key", "https://gemini.test/v1", "gemini-test")
        runner = agent.LocalAgent(
            primary,
            Path.cwd(),
            "instructions",
            fallback_config=fallback,
        )
        failure = urllib.error.URLError("offline")
        with patch("urllib.request.urlopen", side_effect=[failure, Response()]) as mocked:
            message = await runner._request()
        self.assertEqual(mocked.call_count, 2)
        self.assertEqual(runner.config.provider, "gemini")
        self.assertEqual(message["content"], "fallback")

    async def test_transient_503_is_retried_without_switching_provider(self):
        config = agent.ProviderConfig("gemini", "key", "https://gemini.test/v1", "model")
        runner = agent.LocalAgent(config, Path.cwd(), "instructions", fallback_config=None)
        success = {"role": "assistant", "content": "ready"}
        with patch.object(
            runner,
            "_request_with",
            side_effect=[RuntimeError("API request failed (503): busy"), success],
        ) as request, patch("asyncio.sleep", return_value=None) as sleep:
            message = await runner._request()
        self.assertEqual(message, success)
        self.assertEqual(request.call_count, 2)
        sleep.assert_awaited_once_with(1.0)


if __name__ == "__main__":
    unittest.main()
