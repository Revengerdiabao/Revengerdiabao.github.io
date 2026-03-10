#!/usr/bin/env python3
import json
import os
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

try:
    import pyautogui
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: pyautogui. Install with: pip install pyautogui"
    ) from exc


HOST = os.getenv("PYAUTOGUI_BRIDGE_HOST", "127.0.0.1")
PORT = int(os.getenv("PYAUTOGUI_BRIDGE_PORT", "8765"))
TOKEN = os.getenv("PYAUTOGUI_BRIDGE_TOKEN", "")
pyautogui.PAUSE = float(os.getenv("PYAUTOGUI_PAUSE", "0.1"))
pyautogui.FAILSAFE = os.getenv("PYAUTOGUI_FAILSAFE", "true").lower() in {
    "1",
    "true",
    "yes",
}


def _require(value, field):
    if value is None:
        raise ValueError(f"Missing required field: {field}")
    return value


def run_action(action):
    action_type = action.get("type")
    if not action_type:
        raise ValueError("Each action must contain 'type'")

    if action_type == "moveTo":
        x = _require(action.get("x"), "x")
        y = _require(action.get("y"), "y")
        duration = float(action.get("duration", 0))
        pyautogui.moveTo(x, y, duration=duration)
        return {"type": action_type, "x": x, "y": y}

    if action_type == "click":
        x = action.get("x")
        y = action.get("y")
        button = action.get("button", "left")
        clicks = int(action.get("clicks", 1))
        interval = float(action.get("interval", 0))
        pyautogui.click(x=x, y=y, clicks=clicks, interval=interval, button=button)
        return {"type": action_type, "x": x, "y": y, "button": button, "clicks": clicks}

    if action_type == "doubleClick":
        x = action.get("x")
        y = action.get("y")
        button = action.get("button", "left")
        pyautogui.doubleClick(x=x, y=y, button=button)
        return {"type": action_type, "x": x, "y": y, "button": button}

    if action_type == "type":
        text = _require(action.get("text"), "text")
        interval = float(action.get("interval", 0))
        pyautogui.write(str(text), interval=interval)
        return {"type": action_type, "chars": len(str(text))}

    if action_type == "press":
        key = _require(action.get("key"), "key")
        presses = int(action.get("presses", 1))
        interval = float(action.get("interval", 0))
        pyautogui.press(key, presses=presses, interval=interval)
        return {"type": action_type, "key": key, "presses": presses}

    if action_type == "hotkey":
        keys = _require(action.get("keys"), "keys")
        if not isinstance(keys, list) or not keys:
            raise ValueError("'keys' must be a non-empty list")
        pyautogui.hotkey(*keys)
        return {"type": action_type, "keys": keys}

    if action_type == "scroll":
        amount = int(_require(action.get("amount"), "amount"))
        pyautogui.scroll(amount)
        return {"type": action_type, "amount": amount}

    if action_type == "sleep":
        seconds = float(_require(action.get("seconds"), "seconds"))
        time.sleep(seconds)
        return {"type": action_type, "seconds": seconds}

    raise ValueError(f"Unsupported action type: {action_type}")


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "PyAutoGUIBridge/1.0"

    def _json_response(self, status_code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth_ok(self):
        if not TOKEN:
            return True
        return self.headers.get("X-Automation-Token", "") == TOKEN

    def do_GET(self):
        if self.path != "/health":
            self._json_response(404, {"status": "error", "message": "Not found"})
            return
        self._json_response(
            200,
            {
                "status": "ok",
                "failsafe": pyautogui.FAILSAFE,
                "pause": pyautogui.PAUSE,
            },
        )

    def do_POST(self):
        if self.path != "/action":
            self._json_response(404, {"status": "error", "message": "Not found"})
            return

        if not self._auth_ok():
            self._json_response(401, {"status": "error", "message": "Unauthorized"})
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length).decode("utf-8")
            payload = json.loads(raw_body or "{}")
        except Exception as exc:
            self._json_response(400, {"status": "error", "message": f"Invalid JSON: {exc}"})
            return

        action = payload.get("action")
        actions = payload.get("actions")

        if action and actions:
            self._json_response(400, {"status": "error", "message": "Use 'action' or 'actions', not both"})
            return

        if action:
            actions = [action]

        if not isinstance(actions, list) or not actions:
            self._json_response(
                400,
                {
                    "status": "error",
                    "message": "Request must include 'action' object or non-empty 'actions' list",
                },
            )
            return

        try:
            results = [run_action(item) for item in actions]
            self._json_response(200, {"status": "success", "results": results})
        except Exception as exc:
            self._json_response(500, {"status": "error", "message": str(exc)})

    def log_message(self, fmt, *args):
        return


def main():
    print(f"Starting PyAutoGUI bridge on http://{HOST}:{PORT}")
    with HTTPServer((HOST, PORT), RequestHandler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
