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

        await mixin._resolve_and_inject_files(messages, run_context)

        assert messages[0]["content"] == "hello"

    @pytest.mark.asyncio
    async def test_inject_openai_file(self, mixin):
        """OpenAI file attachment is injected into last user message."""
        messages = [{"role": "user", "content": "Analyze this file"}]
        att = OpenAIFileAttachment(file_id="f1", filename="report.pdf", openai_file_id="file-abc")
        run_context = RunContext(messages=messages, file_attachments=[att])

        await mixin._resolve_and_inject_files(messages, run_context)

        content = messages[0]["content"]
        assert isinstance(content, list)
        assert content[0] == {"type": "text", "text": "Analyze this file"}
        assert content[1] == {"type": "file", "file": {"file_id": "file-abc"}}

    @pytest.mark.asyncio
    async def test_inject_url_file(self, mixin):
        """URL file attachment is injected into last user message."""
        messages = [{"role": "user", "content": "Check this data"}]
        att = URLFileAttachment(
            file_id="f2", filename="test.csv", mime_type="text/csv", url="https://example.com/test.csv"
        )
        run_context = RunContext(messages=messages, file_attachments=[att])

        await mixin._resolve_and_inject_files(messages, run_context)

        content = messages[0]["content"]
        assert isinstance(content, list)
        assert content[0] == {"type": "text", "text": "Check this data"}
        assert content[1]["type"] == "text"
        assert "[File: test.csv]" in content[1]["text"]

    @pytest.mark.asyncio
    async def test_inject_multiple_attachments(self, mixin):
        """Multiple attachments are all injected."""
        messages = [{"role": "user", "content": "Compare these"}]
        att1 = OpenAIFileAttachment(file_id="f1", filename="a.pdf", openai_file_id="file-a")
        att2 = OpenAIFileAttachment(file_id="f2", filename="b.pdf", openai_file_id="file-b")
        run_context = RunContext(messages=messages, file_attachments=[att1, att2])

        await mixin._resolve_and_inject_files(messages, run_context)

        content = messages[0]["content"]
        assert len(content) == 3  # original text + 2 file parts

    @pytest.mark.asyncio
    async def test_inject_targets_last_user_message(self, mixin):
        """Files are injected into the last user message, not earlier ones."""
        messages = [
            {"role": "user", "content": "first message"},
            {"role": "assistant", "content": "response"},
            {"role": "user", "content": "second message"},
        ]
        att = OpenAIFileAttachment(file_id="f1", filename="report.pdf", openai_file_id="file-abc")
        run_context = RunContext(messages=messages, file_attachments=[att])

        await mixin._resolve_and_inject_files(messages, run_context)

        # First user message unchanged
        assert messages[0]["content"] == "first message"
        # Last user message converted to multipart
        assert isinstance(messages[2]["content"], list)

    @pytest.mark.asyncio
    async def test_existing_multipart_content_preserved(self, mixin):
        """If content is already multipart, existing parts are preserved."""
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

        await mixin._resolve_and_inject_files(messages, run_context)

        content = messages[0]["content"]
        assert len(content) == 3  # 2 existing + 1 new

    @pytest.mark.asyncio
    async def test_unregistered_attachment_type_raises(self, mixin):
        """TypeError raised for attachment types without a registered resolver."""

        class CustomAttachment(FileAttachment):
            custom_field: str = "x"

        messages = [{"role": "user", "content": "test"}]
        att = CustomAttachment(file_id="f1", filename="test.txt", custom_field="x")
        run_context = RunContext(messages=messages, file_attachments=[att])

        with pytest.raises(TypeError, match="No resolver registered"):
            await mixin._resolve_and_inject_files(messages, run_context)
