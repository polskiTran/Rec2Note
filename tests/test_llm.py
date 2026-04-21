from unittest.mock import MagicMock, patch

import pytest

from rec2note_cli.core.llm import call_llm
from rec2note_cli.core.llm_models import LLMResponse


def _make_mock_response(content: str | None = '"hello"') -> MagicMock:
    mock_usage = MagicMock()
    mock_usage.prompt_tokens = 10
    mock_usage.completion_tokens = 5
    mock_usage.total_tokens = 15
    mock_usage.prompt_tokens_details = None
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content=content))]
    mock_response.model = "gpt-4.1-mini"
    mock_response.usage = mock_usage
    return mock_response


class TestCallLlm:
    def test_raises_when_user_prompt_empty(self):
        with pytest.raises(ValueError, match="user_prompt is required"):
            call_llm(user_prompt="")

    @patch("rec2note_cli.core.llm._get_client")
    def test_builds_system_and_user_messages(self, mock_get_client: MagicMock):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(
            '"hello"'
        )
        mock_get_client.return_value = mock_client

        call_llm(
            system_prompt="You are a helpful assistant.",
            user_prompt="Say hello.",
            json_mode=False,
        )

        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4.1-mini"
        assert call_kwargs["messages"] == [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hello."},
        ]
        assert call_kwargs["temperature"] == 0.3
        assert call_kwargs["response_format"] == {"type": "text"}

    @patch("rec2note_cli.core.llm._get_client")
    def test_json_mode_adds_response_format(self, mock_get_client: MagicMock):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(
            '{"key": "value"}'
        )
        mock_get_client.return_value = mock_client

        call_llm(user_prompt="Return JSON.", json_mode=True)

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["response_format"] == {"type": "json_object"}

    @patch("rec2note_cli.core.llm._get_client")
    def test_model_id_override_used(self, mock_get_client: MagicMock):
        mock_client = MagicMock()
        mock_response = _make_mock_response('"hello"')
        mock_response.model = "gpt-4o"
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        call_llm(user_prompt="Hi.", model_id="gpt-4o", json_mode=False)

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o"

    @patch("rec2note_cli.core.llm._get_client")
    def test_returns_llm_response_object(self, mock_get_client: MagicMock):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(
            "The answer is 42"
        )
        mock_get_client.return_value = mock_client

        result = call_llm(user_prompt="What is 40 + 2?", json_mode=False)

        assert isinstance(result, LLMResponse)
        assert result.content == "The answer is 42"
        assert result.model == "gpt-4.1-mini"

    @patch("rec2note_cli.core.llm._get_client")
    def test_returns_empty_string_when_content_none(self, mock_get_client: MagicMock):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(None)
        mock_get_client.return_value = mock_client

        result = call_llm(user_prompt="Hello?", json_mode=False)

        assert isinstance(result, LLMResponse)
        assert result.content == ""

    @patch("rec2note_cli.core.llm._get_client")
    def test_token_usage_populated(self, mock_get_client: MagicMock):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response('"ok"')
        mock_get_client.return_value = mock_client

        result = call_llm(user_prompt="Token test.", json_mode=False)

        assert result.usage.prompt_tokens == 10
        assert result.usage.completion_tokens == 5
        assert result.usage.total_tokens == 15
        assert result.usage.cached_tokens == 0

    @patch("rec2note_cli.core.llm._get_client")
    def test_cached_tokens_extracted(self, mock_get_client: MagicMock):
        mock_client = MagicMock()
        mock_response = _make_mock_response('"ok"')
        mock_response.usage.prompt_tokens_details = MagicMock(cached_tokens=8)
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = call_llm(user_prompt="Cache test.", json_mode=False)

        assert result.usage.cached_tokens == 8


class TestCallLlmTaskPrompt:
    @patch("rec2note_cli.core.llm._get_client")
    def test_task_prompt_appends_second_user_message(self, mock_get_client: MagicMock):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(
            '{"result": "ok"}'
        )
        mock_get_client.return_value = mock_client

        call_llm(
            system_prompt="You are an assistant.",
            user_prompt="Full transcript text here.",
            task_prompt="Extract deadlines from the transcript.",
            json_mode=True,
        )

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["messages"] == [
            {"role": "system", "content": "You are an assistant."},
            {"role": "user", "content": "Full transcript text here."},
            {"role": "user", "content": "Extract deadlines from the transcript."},
        ]

    @patch("rec2note_cli.core.llm._get_client")
    def test_task_prompt_without_system_prompt(self, mock_get_client: MagicMock):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(
            '{"result": "ok"}'
        )
        mock_get_client.return_value = mock_client

        call_llm(
            user_prompt="Transcript content.",
            task_prompt="Summarize the above.",
            json_mode=True,
        )

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["messages"] == [
            {"role": "user", "content": "Transcript content."},
            {"role": "user", "content": "Summarize the above."},
        ]

    @patch("rec2note_cli.core.llm._get_client")
    def test_no_task_prompt_backward_compatible(self, mock_get_client: MagicMock):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(
            '{"result": "ok"}'
        )
        mock_get_client.return_value = mock_client

        call_llm(
            system_prompt="You are an assistant.",
            user_prompt="Hello.",
            json_mode=False,
        )

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["messages"] == [
            {"role": "system", "content": "You are an assistant."},
            {"role": "user", "content": "Hello."},
        ]

    @patch("rec2note_cli.core.llm._get_client")
    def test_task_prompt_none_equivalent_to_omitted(self, mock_get_client: MagicMock):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = _make_mock_response(
            '{"result": "ok"}'
        )
        mock_get_client.return_value = mock_client

        call_llm(
            system_prompt="System.",
            user_prompt="User.",
            task_prompt=None,
            json_mode=False,
        )

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert len(call_kwargs["messages"]) == 2
        assert call_kwargs["messages"] == [
            {"role": "system", "content": "System."},
            {"role": "user", "content": "User."},
        ]
