import asyncio
import json
import urllib.request

import websockets


WS_URL = "ws://127.0.0.1:8000/ws"
TRIGGER_URL = "http://127.0.0.1:8000/api/ai/summary"


async def main() -> None:
    async with websockets.connect(WS_URL) as ws:
        request = urllib.request.Request(
            TRIGGER_URL,
            data=json.dumps({"limit": 50}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            print(f"trigger_status={response.status}")

        for _ in range(12):
            raw_message = await asyncio.wait_for(ws.recv(), timeout=10)
            print("ws_message=")
            print(raw_message)
            try:
                payload = json.loads(raw_message)
            except json.JSONDecodeError:
                continue
            if payload.get("type") == "ai_report_created":
                report = payload.get("report", {})
                print(f"ai_report_created_report_id={report.get('report_id')}")
                return

        raise RuntimeError("Did not receive ai_report_created websocket message in time")


if __name__ == "__main__":
    asyncio.run(main())
