# File: src/aireview/services/debugger.py

import os
import time
import json
from pathlib import Path
from typing import Any

class Debugger:
    def __init__(self, enabled: bool):
        self.enabled = enabled
        self.debug_dir = Path(".aireview/debug")

    def dump_request(self, check_id: str, content: str):
        if not self.enabled: return
        try:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            timestamp = int(time.time())
            filename = self.debug_dir / f"{timestamp}_{check_id}_req.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"  📝 [DEBUG] Request dumped to: {filename}")
        except Exception as e:
            print(f"  ⚠️ [DEBUG] Failed to dump request: {e}")

    # --- NEW METHOD ---
    def dump_response(self, check_id: str, response_data: Any):
        """Saves the parsed JSON response to a file."""
        if not self.enabled: return
        try:
            self.debug_dir.mkdir(parents=True, exist_ok=True)
            timestamp = int(time.time())
            # Save as .json for easy reading/reuse
            filename = self.debug_dir / f"{timestamp}_{check_id}_resp.json"

            with open(filename, "w", encoding="utf-8") as f:
                json.dump(response_data, f, indent=2, ensure_ascii=False)

            print(f"  💾 [DEBUG] Response dumped to: {filename}")
        except Exception as e:
            print(f"  ⚠️ [DEBUG] Failed to dump response: {e}")