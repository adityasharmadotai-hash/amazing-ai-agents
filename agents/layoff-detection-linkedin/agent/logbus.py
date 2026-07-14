"""In-memory log bus for streaming scan logs to the dashboard (SSE).

A logging.Handler fans every log record out to all subscribed queues and keeps
a small ring buffer so a newly-opened dashboard sees recent history. Thread-safe
— scan worker threads publish; the async SSE endpoint consumes.
"""
from __future__ import annotations

import collections
import logging
import queue
import threading

_lock = threading.Lock()
_subscribers: list[queue.Queue] = []
_history: collections.deque[str] = collections.deque(maxlen=300)
_installed = False


class _BusHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        try:
            line = self.format(record).replace("\n", " ")
        except Exception:  # noqa: BLE001
            return
        with _lock:
            _history.append(line)
            for q in _subscribers:
                try:
                    q.put_nowait(line)
                except queue.Full:
                    pass


def install(level: int = logging.INFO) -> None:
    global _installed
    if _installed:
        return
    h = _BusHandler()
    h.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s",
                                     datefmt="%H:%M:%S"))
    h.setLevel(level)
    logging.getLogger().addHandler(h)
    _installed = True


def subscribe() -> queue.Queue:
    q: queue.Queue = queue.Queue(maxsize=2000)
    with _lock:
        for line in list(_history)[-50:]:   # seed with recent history
            try:
                q.put_nowait(line)
            except queue.Full:
                break
        _subscribers.append(q)
    return q


def unsubscribe(q: queue.Queue) -> None:
    with _lock:
        if q in _subscribers:
            _subscribers.remove(q)
