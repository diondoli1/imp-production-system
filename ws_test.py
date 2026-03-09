import asyncio
import urllib.request

import websockets


WS_URL = "ws://127.0.0.1:8000/ws"
TRIGGER_URL = "http://127.0.0.1:8000/api/ai/placeholder-report"


async def main() -> None:
    async with websockets.connect(WS_URL) as ws:
        request = urllib.request.Request(
            TRIGGER_URL,
            data=b"{}",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            print(f"trigger_status={response.status}")

        message = await asyncio.wait_for(ws.recv(), timeout=10)
        print("first_message=")
        print(message)


if __name__ == "__main__":
    asyncio.run(main())