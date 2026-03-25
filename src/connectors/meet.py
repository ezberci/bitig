import re
from datetime import datetime
from pathlib import Path

import structlog

from src.connectors.base import BaseConnector
from src.models.connector import ConnectorType
from src.models.document import RawDocument

logger = structlog.get_logger()


class MeetConnector(BaseConnector):
    """Connector for parsing Google Meet transcript files.

    Expects transcript files in a directory, one per meeting.
    Supported formats: .txt, .vtt, .srt
    """

    def __init__(self, transcripts_dir: Path | None = None) -> None:
        self._transcripts_dir = transcripts_dir

    @property
    def connector_type(self) -> ConnectorType:
        return ConnectorType.MEET

    def is_configured(self) -> bool:
        return self._transcripts_dir is not None and self._transcripts_dir.is_dir()

    async def fetch(self, since: datetime | None = None) -> list[RawDocument]:
        if not self.is_configured():
            logger.warning("meet_not_configured")
            return []

        documents: list[RawDocument] = []
        extensions = {".txt", ".vtt", ".srt"}

        for path in sorted(self._transcripts_dir.iterdir()):
            if path.suffix.lower() not in extensions:
                continue

            mtime = datetime.fromtimestamp(path.stat().st_mtime)
            if since and mtime < since:
                continue

            content = self._parse_transcript(path)
            if not content.strip():
                continue

            documents.append(
                RawDocument(
                    source_type="meet",
                    source_id=path.stem,
                    title=self._title_from_filename(path.stem),
                    content=content,
                    metadata={"file": path.name, "format": path.suffix.lstrip(".")},
                    timestamp=mtime,
                )
            )

        logger.info("meet_fetched", count=len(documents))
        return documents

    def _parse_transcript(self, path: Path) -> str:
        text = path.read_text(encoding="utf-8", errors="replace")
        suffix = path.suffix.lower()

        if suffix == ".txt":
            return text
        if suffix in {".vtt", ".srt"}:
            return self._strip_subtitle_metadata(text)
        return text

    def _strip_subtitle_metadata(self, text: str) -> str:
        """Remove timestamps and sequence numbers from VTT/SRT content."""
        lines: list[str] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line == "WEBVTT":
                continue
            if re.match(r"^\d+$", line):
                continue
            if re.match(r"[\d:.,]+\s*-->", line):
                continue
            lines.append(line)
        return "\n".join(lines)

    def _title_from_filename(self, stem: str) -> str:
        """Generate a readable title from filename."""
        title = stem.replace("_", " ").replace("-", " ")
        return title.title()
