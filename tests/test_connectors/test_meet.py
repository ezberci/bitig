from datetime import datetime

import pytest

from src.connectors.meet import MeetConnector


@pytest.fixture
def meet_connector(tmp_path):
    return MeetConnector(transcripts_dir=tmp_path)


class TestMeetConnector:
    def test_connector_type(self, meet_connector):
        assert meet_connector.connector_type == "meet"

    def test_is_configured_with_valid_dir(self, meet_connector):
        assert meet_connector.is_configured() is True

    def test_is_configured_without_dir(self):
        connector = MeetConnector(transcripts_dir=None)
        assert connector.is_configured() is False

    async def test_fetch_empty_dir(self, meet_connector):
        docs = await meet_connector.fetch()
        assert docs == []

    async def test_fetch_txt_file(self, meet_connector, tmp_path):
        transcript = tmp_path / "standup_2024_01_15.txt"
        transcript.write_text("Alice: Let's discuss the sprint goals\nBob: Sounds good")

        docs = await meet_connector.fetch()
        assert len(docs) == 1
        assert docs[0].source_type == "meet"
        assert docs[0].source_id == "standup_2024_01_15"
        assert "Alice" in docs[0].content
        assert docs[0].title == "Standup 2024 01 15"

    async def test_fetch_vtt_file(self, meet_connector, tmp_path):
        vtt = tmp_path / "meeting.vtt"
        vtt.write_text(
            "WEBVTT\n\n1\n00:00:01.000 --> 00:00:05.000\n"
            "Hello everyone\n\n2\n00:00:06.000 --> 00:00:10.000\nLet's begin"
        )

        docs = await meet_connector.fetch()
        assert len(docs) == 1
        assert "Hello everyone" in docs[0].content
        assert "WEBVTT" not in docs[0].content
        assert "-->" not in docs[0].content

    async def test_fetch_srt_file(self, meet_connector, tmp_path):
        srt = tmp_path / "meeting.srt"
        srt.write_text(
            "1\n00:00:01,000 --> 00:00:05,000\nFirst line\n\n"
            "2\n00:00:06,000 --> 00:00:10,000\nSecond line"
        )

        docs = await meet_connector.fetch()
        assert len(docs) == 1
        assert "First line" in docs[0].content
        assert "-->" not in docs[0].content

    async def test_fetch_ignores_non_transcript_files(self, meet_connector, tmp_path):
        (tmp_path / "notes.md").write_text("some notes")
        (tmp_path / "meeting.txt").write_text("actual transcript")

        docs = await meet_connector.fetch()
        assert len(docs) == 1
        assert docs[0].source_id == "meeting"

    async def test_fetch_since_filter(self, meet_connector, tmp_path):
        old = tmp_path / "old_meeting.txt"
        old.write_text("old content")

        new = tmp_path / "new_meeting.txt"
        new.write_text("new content")

        # Fetch with since=now should return nothing (files are just created)
        future = datetime(2099, 1, 1)
        docs = await meet_connector.fetch(since=future)
        assert docs == []


class TestStripSubtitleMetadata:
    def test_strips_vtt(self):
        connector = MeetConnector()
        text = (
            "WEBVTT\n\n1\n00:00:01.000 --> 00:00:05.000\n"
            "Hello\n\n2\n00:00:06.000 --> 00:00:10.000\nWorld"
        )
        result = connector._strip_subtitle_metadata(text)
        assert result == "Hello\nWorld"

    def test_strips_srt(self):
        connector = MeetConnector()
        text = "1\n00:00:01,000 --> 00:00:05,000\nHello\n\n2\n00:00:06,000 --> 00:00:10,000\nWorld"
        result = connector._strip_subtitle_metadata(text)
        assert result == "Hello\nWorld"
