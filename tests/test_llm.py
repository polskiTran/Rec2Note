from unittest.mock import MagicMock, patch

import pytest

from rec2note_cli.core.llm import call_llm


class TestCallLlm:
    def test_raises_when_user_prompt_empty(self):
        with pytest.raises(ValueError, match="user_prompt is required"):
            call_llm(user_prompt="")

    @patch("rec2note_cli.core.llm._get_client")
    def test_builds_system_and_user_messages(self, mock_get_client: MagicMock):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='"hello"'))]
        mock_client.chat.completions.create.return_value = mock_response
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
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content='{"key": "value"}'))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        call_llm(user_prompt="Return JSON.", json_mode=True)

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["response_format"] == {"type": "json_object"}

    @patch("rec2note_cli.core.llm._get_client")
    def test_model_id_override_used(self, mock_get_client: MagicMock):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='"hello"'))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        call_llm(user_prompt="Hi.", model_id="gpt-4o", json_mode=False)

        call_kwargs = mock_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o"

    @patch("rec2note_cli.core.llm._get_client")
    def test_returns_response_content(self, mock_get_client: MagicMock):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content="The answer is 42"))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = call_llm(user_prompt="What is 40 + 2?", json_mode=False)

        assert result == "The answer is 42"

    @patch("rec2note_cli.core.llm._get_client")
    def test_returns_empty_string_when_content_none(self, mock_get_client: MagicMock):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content=None))]
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        result = call_llm(user_prompt="Hello?", json_mode=False)

        assert result == ""
