"""Unit tests for FileAttachmentMixin."""

import pytest

from akd._base import RunContext

from akd_ext.agents._mixins import FileAttachmentMixin
from akd_ext.files import (
    FileAttachment,
    OpenAIFileAttachment,
    OpenAIFileResolver,
    URLFileAttachment,
)


class DummyResolver:
    """Test resolver that returns a fixed content part."""

    def __init__(self, parts: list[dict]):
        self.parts = parts

    async def resolve(self, attachment: FileAttachment) -> list[dict]:
        return self.parts


class MixinHost(FileAttachmentMixin):
    """Minimal host class to test the mixin."""

    pass


@pytest.fixture
def mixin():
    host = MixinHost()
    host.file_resolvers = {
        OpenAIFileAttachment: OpenAIFileResolver(),
        URLFileAttachment: DummyResolver([{"type": "text", "text": "[File: test.csv]\ncol1,col2"}]),
    }
    return host


class TestFileAttachmentMixin:
    @pytest.mark.asyncio
    async def test_no_attachments_is_noop(self, mixin):
        """Messages unchanged when no file_attachments on RunContext."""
        messages = [{"role": "user", "content": "hello"}]
        run_context = RunContext(messages=messages)

        await mixin._resolve_and_inject_files(run_context)

        assert len(run_context.messages) == 1
        assert run_context.messages[0]["content"] == "hello"

    @pytest.mark.asyncio
    async def test_inject_openai_file(self, mixin):
        """OpenAI file attachment is appended as a new user message."""
        messages = [{"role": "user", "content": "Analyze this file"}]
        att = OpenAIFileAttachment(file_id="f1", filename="report.pdf", openai_file_id="file-abc")
        run_context = RunContext(messages=messages, file_attachments=[att])

        await mixin._resolve_and_inject_files(run_context)

        assert len(run_context.messages) == 2
        assert run_context.messages[0]["content"] == "Analyze this file"
        assert run_context.messages[1]["role"] == "user"
        assert run_context.messages[1]["content"] == [{"type": "input_file", "file_id": "file-abc"}]

    @pytest.mark.asyncio
    async def test_inject_url_file(self, mixin):
        """URL file attachment is appended as a new user message."""
        messages = [{"role": "user", "content": "Check this data"}]
        att = URLFileAttachment(
            file_id="f2", filename="test.csv", mime_type="text/csv", url="https://example.com/test.csv"
        )
        run_context = RunContext(messages=messages, file_attachments=[att])

        await mixin._resolve_and_inject_files(run_context)

        assert len(run_context.messages) == 2
        assert run_context.messages[0]["content"] == "Check this data"
        assert run_context.messages[1]["role"] == "user"
        assert run_context.messages[1]["content"][0]["type"] == "text"
        assert "[File: test.csv]" in run_context.messages[1]["content"][0]["text"]

    @pytest.mark.asyncio
    async def test_inject_multiple_attachments(self, mixin):
        """Multiple attachments are all added to the new message."""
        messages = [{"role": "user", "content": "Compare these"}]
        att1 = OpenAIFileAttachment(file_id="f1", filename="a.pdf", openai_file_id="file-a")
        att2 = OpenAIFileAttachment(file_id="f2", filename="b.pdf", openai_file_id="file-b")
        run_context = RunContext(messages=messages, file_attachments=[att1, att2])

        await mixin._resolve_and_inject_files(run_context)

        assert len(run_context.messages) == 2
        assert run_context.messages[0]["content"] == "Compare these"
        assert len(run_context.messages[1]["content"]) == 2

    @pytest.mark.asyncio
    async def test_files_appended_as_new_message(self, mixin):
        """Files are appended as a new message, existing messages are untouched."""
        messages = [
            {"role": "user", "content": "first message"},
            {"role": "assistant", "content": "response"},
            {"role": "user", "content": "second message"},
        ]
        att = OpenAIFileAttachment(file_id="f1", filename="report.pdf", openai_file_id="file-abc")
        run_context = RunContext(messages=messages, file_attachments=[att])

        await mixin._resolve_and_inject_files(run_context)

        assert len(run_context.messages) == 4
        assert run_context.messages[0]["content"] == "first message"
        assert run_context.messages[2]["content"] == "second message"
        assert run_context.messages[3]["role"] == "user"
        assert run_context.messages[3]["content"] == [{"type": "input_file", "file_id": "file-abc"}]

    @pytest.mark.asyncio
    async def test_existing_multipart_untouched(self, mixin):
        """Existing multipart content is not modified."""
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "existing text"},
                    {"type": "image_url", "image_url": {"url": "data:image/png;base64,abc"}},
                ],
            }
        ]
        att = OpenAIFileAttachment(file_id="f1", filename="report.pdf", openai_file_id="file-abc")
        run_context = RunContext(messages=messages, file_attachments=[att])

        await mixin._resolve_and_inject_files(run_context)

        assert len(run_context.messages) == 2
        assert len(run_context.messages[0]["content"]) == 2  # original untouched
        assert run_context.messages[1]["role"] == "user"
        assert run_context.messages[1]["content"] == [{"type": "input_file", "file_id": "file-abc"}]

    @pytest.mark.asyncio
    async def test_unregistered_attachment_type_raises(self, mixin):
        """TypeError raised for attachment types without a registered resolver."""

        class CustomAttachment(FileAttachment):
            custom_field: str = "x"

        messages = [{"role": "user", "content": "test"}]
        att = CustomAttachment(file_id="f1", filename="test.txt", custom_field="x")
        run_context = RunContext(messages=messages, file_attachments=[att])

        with pytest.raises(TypeError, match="No resolver registered"):
            await mixin._resolve_and_inject_files(run_context)

    @pytest.mark.asyncio
    async def test_none_messages_initialized(self, mixin):
        """When run_context.messages is None, it gets initialized."""
        att = OpenAIFileAttachment(file_id="f1", filename="report.pdf", openai_file_id="file-abc")
        run_context = RunContext(messages=None, file_attachments=[att])

        await mixin._resolve_and_inject_files(run_context)

        assert run_context.messages is not None
        assert len(run_context.messages) == 1
        assert run_context.messages[0]["role"] == "user"
        assert run_context.messages[0]["content"] == [{"type": "input_file", "file_id": "file-abc"}]

    @pytest.mark.asyncio
    async def test_attachments_cleared_after_injection(self, mixin):
        """Attachments are cleared from run_context after injection to prevent re-injection."""
        messages = [{"role": "user", "content": "Analyze this"}]
        att = OpenAIFileAttachment(file_id="f1", filename="report.pdf", openai_file_id="file-abc")
        run_context = RunContext(messages=messages, file_attachments=[att])

        await mixin._resolve_and_inject_files(run_context)

        assert run_context.file_attachments == []

        # Second call should be a no-op
        msg_count = len(run_context.messages)
        await mixin._resolve_and_inject_files(run_context)
        assert len(run_context.messages) == msg_count
