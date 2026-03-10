# n8n + PyAutoGUI integration

Bridge nay cho phep n8n dieu khien chuot/ban phim thong qua `pyautogui`.

## 1) Cai dat

```bash
cd /workspace/automation
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Neu chay Linux, can GUI session va mot so goi he thong:

```bash
sudo apt-get update
sudo apt-get install -y scrot python3-tk python3-dev
```

## 2) Chay bridge service

```bash
cd /workspace/automation
source .venv/bin/activate
export PYAUTOGUI_BRIDGE_HOST=127.0.0.1
export PYAUTOGUI_BRIDGE_PORT=8765
export PYAUTOGUI_BRIDGE_TOKEN=changeme
python pyautogui_bridge.py
```

Health check:

```bash
curl http://127.0.0.1:8765/health
```

## 3) Goi tu n8n

Import file `n8n_pyautogui_template.json` vao n8n, sau do set env cho n8n:

- `PYAUTOGUI_BRIDGE_URL=http://127.0.0.1:8765/action`
- `PYAUTOGUI_BRIDGE_TOKEN=changeme`

Node HTTP Request se POST payload:

```json
{
  "actions": [
    { "type": "moveTo", "x": 900, "y": 500, "duration": 0.2 },
    { "type": "click", "button": "left" },
    { "type": "type", "text": "Hello", "interval": 0.03 },
    { "type": "press", "key": "enter" }
  ]
}
```

## 4) Action duoc ho tro

- `moveTo`: `x`, `y`, optional `duration`
- `click`: optional `x`, `y`, `button`, `clicks`, `interval`
- `doubleClick`: optional `x`, `y`, `button`
- `type`: `text`, optional `interval`
- `press`: `key`, optional `presses`, `interval`
- `hotkey`: `keys` (array), vd `["ctrl", "c"]`
- `scroll`: `amount`
- `sleep`: `seconds`

## 5) Luu y quan trong

- PyAutoGUI dieu khien chuot/ban phim that tren may dang chay bridge.
- Moi truong headless khong co desktop thuong se khong click/type duoc.
- Co bat `FAILSAFE`: day chuot vao goc tren-trai de dung khan cap.
