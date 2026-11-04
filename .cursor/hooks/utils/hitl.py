#!/usr/bin/env python3
"""Human-in-the-loop (HITL) request helper for Cursor hook scripts.

Adapted from disler/claude-code-hooks-multi-agent-observability.
Provides WebSocket-based request/response for human approvals and questions.
"""

import asyncio
import json
import socket
import time
from threading import Thread
from typing import Any, Literal

OBSERVABILITY_URL = "http://localhost:3001"


class HITLRequest:
    """Helper class for human-in-the-loop requests via the observability server."""

    def __init__(
        self,
        question: str,
        hitl_type: Literal["question", "permission", "choice"] = "question",
        choices: list[str] | None = None,
        timeout: int = 300,
        observability_url: str = OBSERVABILITY_URL,
    ):
        self.question = question
        self.hitl_type = hitl_type
        self.choices = choices
        self.timeout = timeout
        self.observability_url = observability_url
        self.response_port = self._find_free_port()
        self.response_data: dict[str, Any] | None = None
        self.server_thread: Thread | None = None

    def _find_free_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            s.listen(1)
            return s.getsockname()[1]

    def _start_response_server(self) -> None:
        try:
            from websockets.server import serve
        except ImportError:
            return

        async def handle_connection(websocket: Any) -> None:
            try:
                message = await websocket.recv()
                self.response_data = json.loads(message)
                await websocket.close()
            except Exception:
                pass

        async def start_server() -> None:
            try:
                async with serve(handle_connection, "localhost", self.response_port):
                    start_time = time.time()
                    while self.response_data is None:
                        await asyncio.sleep(0.1)
                        if time.time() - start_time > self.timeout:
                            break
            except Exception:
                pass

        try:
            asyncio.run(start_server())
        except Exception:
            pass

    def get_hitl_data(self) -> dict[str, Any]:
        return {
            "question": self.question,
            "responseWebSocketUrl": f"ws://localhost:{self.response_port}",
            "type": self.hitl_type,
            "choices": self.choices,
            "timeout": self.timeout,
            "requiresResponse": True,
        }

    def send_and_wait(
        self,
        hook_event_data: dict[str, Any],
        session_data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Send HITL request to the observability server and wait for a response."""
        event_payload = {
            **session_data,
            "hook_event_type": hook_event_data.get("hook_event_type", "HumanInTheLoop"),
            "payload": hook_event_data.get("payload", {}),
            "humanInTheLoop": self.get_hitl_data(),
            "timestamp": int(time.time() * 1000),
        }

        self.server_thread = Thread(target=self._start_response_server, daemon=True)
        self.server_thread.start()

        time.sleep(0.1)

        try:
            import requests

            response = requests.post(
                f"{self.observability_url}/events",
                json=event_payload,
                timeout=10,
            )
            response.raise_for_status()
        except ImportError:
            return None
        except Exception:
            return None

        self.server_thread.join(timeout=self.timeout)
        return self.response_data


def ask_question(
    question: str,
    session_data: dict[str, Any],
    timeout: int = 300,
) -> str | None:
    """Ask a question and wait for text response."""
    hitl = HITLRequest(question, hitl_type="question", timeout=timeout)
    response = hitl.send_and_wait(
        {"hook_event_type": "HumanInTheLoop", "payload": {}},
        session_data,
    )
    return response.get("response") if response else None


def ask_permission(
    question: str,
    session_data: dict[str, Any],
    timeout: int = 300,
) -> bool:
    """Ask for permission and wait for yes/no response."""
    hitl = HITLRequest(question, hitl_type="permission", timeout=timeout)
    response = hitl.send_and_wait(
        {"hook_event_type": "HumanInTheLoop", "payload": {}},
        session_data,
    )
    return response.get("permission", False) if response else False


def ask_choice(
    question: str,
    choices: list[str],
    session_data: dict[str, Any],
    timeout: int = 300,
) -> str | None:
    """Ask user to choose from options."""
    hitl = HITLRequest(
        question,
        hitl_type="choice",
        choices=choices,
        timeout=timeout,
    )
    response = hitl.send_and_wait(
        {"hook_event_type": "HumanInTheLoop", "payload": {}},
        session_data,
    )
    return response.get("choice") if response else None
