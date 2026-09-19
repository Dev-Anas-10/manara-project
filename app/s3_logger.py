import os
import io
import json
import time
import logging
import threading
from datetime import datetime, timezone

import boto3

BUCKET = os.environ.get("LOG_BUCKET")
PREFIX = os.environ.get("LOG_PREFIX", "app-logs")
FLUSH_INTERVAL = int(os.environ.get("LOG_FLUSH_INTERVAL", "60"))
FLUSH_SIZE = int(os.environ.get("LOG_FLUSH_SIZE", "100"))


class S3LogHandler(logging.Handler):
    """Buffers log records and uploads them to S3 as JSON-lines files."""

    def __init__(self):
        super().__init__()
        self.s3 = boto3.client("s3")
        self.buffer = []
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._periodic_flush, daemon=True)
        self.thread.start()

    def emit(self, record):
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        with self.lock:
            self.buffer.append(json.dumps(entry, ensure_ascii=False))
            should_flush = len(self.buffer) >= FLUSH_SIZE
        if should_flush:
            self.flush()

    def flush(self):
        with self.lock:
            if not self.buffer:
                return
            lines, self.buffer = self.buffer, []
        now = datetime.now(timezone.utc)
        key = f"{PREFIX}/{now:%Y/%m/%d}/{now:%H%M%S}-{os.getpid()}-{int(time.time()*1000)}.jsonl"
        try:
            self.s3.put_object(
                Bucket=BUCKET,
                Key=key,
                Body="\n".join(lines).encode("utf-8"),
                ContentType="application/x-ndjson",
            )
        except Exception as e:
            # Don't lose logs on transient failure: put them back
            with self.lock:
                self.buffer = lines + self.buffer
            logging.getLogger("s3_logger").error("S3 upload failed: %s", e)

    def _periodic_flush(self):
        while not self.stop_event.wait(FLUSH_INTERVAL):
            self.flush()

    def close(self):
        self.stop_event.set()
        self.flush()
        super().close()


def setup_logging():
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))
    root.addHandler(console)  # also goes to CloudWatch via awslogs
    handler = None
    if BUCKET:
        handler = S3LogHandler()
        root.addHandler(handler)
    return handler
