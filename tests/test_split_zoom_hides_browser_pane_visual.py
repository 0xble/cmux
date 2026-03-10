#!/usr/bin/env python3
"""
Visual regression test for split zoom hiding a sibling browser pane cleanly.

Scenario:
  - Render deterministic terminal content in a single pane and capture a baseline screenshot.
  - Split right with a browser pane and wait for content to load.
  - Zoom the left pane.
  - Compare a right-edge crop from each screenshot.

Expected:
  - The split-state crop differs substantially from the single-pane baseline.
  - The zoomed-state crop matches the single-pane baseline closely.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cmux import cmux, cmuxError


SOCKET_PATH = os.environ.get("CMUX_SOCKET", "/tmp/cmux-debug.sock")
MAX_AFTER_DIFF_PIXELS = 6_000
MIN_DURING_DIFF_PIXELS = 8_000
MIN_DURING_TO_AFTER_RATIO = 3.0


def _wait_until(predicate, timeout_s: float = 5.0, interval_s: float = 0.05) -> bool:
    start = time.time()
    while time.time() - start < timeout_s:
        if predicate():
            return True
        time.sleep(interval_s)
    return False


def _wait_url_contains(client: cmux, panel_id: str, needle: str, timeout_s: float = 20.0) -> str:
    last = ""

    def _matches() -> bool:
        nonlocal last
        last = client._send_command(f"get_url {panel_id}").strip()
        return not last.startswith("ERROR") and needle.lower() in last.lower()

    if not _wait_until(_matches, timeout_s=timeout_s, interval_s=0.1):
        raise cmuxError(f"Timed out waiting for browser URL containing '{needle}', got: {last}")
    return last


def _capture_screenshot(client: cmux, label: str) -> str:
    response = client._send_command(f"screenshot {label}").strip()
    if not response.startswith("OK "):
        raise cmuxError(f"screenshot failed for {label}: {response}")
    return response.split(" ", 2)[2]


def _image_size(path: str) -> tuple[int, int]:
    result = subprocess.run(
        ["magick", "identify", "-format", "%w %h", path],
        capture_output=True,
        text=True,
        check=True,
    )
    width_text, height_text = result.stdout.strip().split()
    return int(width_text), int(height_text)


def _crop_right_focus_region(path: str, label: str) -> str:
    width, height = _image_size(path)
    crop_width = max(1, int(width * 0.28))
    crop_height = max(1, int(height * 0.72))
    crop_x = max(0, width - crop_width - int(width * 0.03))
    crop_y = max(0, int(height * 0.16))
    output = Path(tempfile.gettempdir()) / f"{label}_{Path(path).name}"
    subprocess.run(
        [
            "magick",
            path,
            "-crop",
            f"{crop_width}x{crop_height}+{crop_x}+{crop_y}",
            "+repage",
            str(output),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return str(output)


def _image_diff_pixels(path_a: str, path_b: str) -> int:
    result = subprocess.run(
        ["magick", "compare", "-metric", "AE", path_a, path_b, "null:"],
        capture_output=True,
        text=True,
        check=False,
    )
    metric_output = (result.stderr or result.stdout).strip()
    if not metric_output:
        raise RuntimeError(
            f"ImageMagick compare produced no metric output for {path_a} vs {path_b}"
        )
    return int(float(metric_output.split()[0]))


def _paint_terminal(client: cmux, panel_id: str, line: str) -> None:
    client.send_surface(
        panel_id,
        "clear\n"
        "printf '\\033[?25l'\n"
        "python3 - <<'PY'\n"
        f"for _ in range(22):\n    print({line!r})\n"
        "PY\n",
    )


def _selected_panels_by_x(client: cmux) -> list[dict]:
    payload = client.layout_debug()
    rows = payload.get("selectedPanels") or []
    valid_rows = [row for row in rows if row.get("paneFrame") and row.get("panelId")]
    return sorted(valid_rows, key=lambda row: float(row["paneFrame"]["x"]))


def _wait_for_split_panels(client: cmux, expected: int = 2, timeout_s: float = 4.0) -> list[dict]:
    rows: list[dict] = []

    def _ready() -> bool:
        nonlocal rows
        rows = _selected_panels_by_x(client)
        return len(rows) >= expected

    if not _wait_until(_ready, timeout_s=timeout_s, interval_s=0.05):
        raise cmuxError(f"Timed out waiting for {expected} selected panels, got: {rows}")
    return rows


def main() -> int:
    with cmux(SOCKET_PATH) as client:
        if not client.ping():
            raise cmuxError(
                f"Socket ping failed on {SOCKET_PATH}. "
                "Launch Debug app with CMUX_SOCKET_MODE=allowAll for this test."
            )

        client.activate_app()
        workspace_id = client.new_workspace()
        crop_paths: list[str] = []
        try:
            client.select_workspace(workspace_id)
            time.sleep(0.25)

            surfaces = client.list_surfaces()
            if len(surfaces) != 1:
                raise cmuxError(f"Expected a fresh workspace with 1 surface, got: {surfaces}")
            left_panel_id = surfaces[0][1]

            _paint_terminal(client, left_panel_id, "CMUX ZOOM LEFT BASELINE")
            time.sleep(0.6)
            before_screenshot = _capture_screenshot(client, "split_zoom_browser_before")

            client.new_pane("right", panel_type="browser", url="https://example.com")
            split_rows = _wait_for_split_panels(client, expected=2, timeout_s=4.0)
            left_row, right_row = split_rows[0], split_rows[1]
            left_pane_id = left_row["paneId"]
            right_panel_id = right_row["panelId"]

            _wait_url_contains(client, right_panel_id, "example.com", timeout_s=20.0)
            time.sleep(0.8)
            during_screenshot = _capture_screenshot(client, "split_zoom_browser_during")

            client.focus_pane(left_pane_id)
            time.sleep(0.2)
            client.simulate_shortcut("cmd+shift+enter")
            time.sleep(1.0)
            after_screenshot = _capture_screenshot(client, "split_zoom_browser_after")
            after_layout = client.layout_debug()

            before_crop = _crop_right_focus_region(before_screenshot, "split_zoom_browser_before_crop")
            during_crop = _crop_right_focus_region(during_screenshot, "split_zoom_browser_during_crop")
            after_crop = _crop_right_focus_region(after_screenshot, "split_zoom_browser_after_crop")
            crop_paths.extend([before_crop, during_crop, after_crop])

            before_after_diff = _image_diff_pixels(before_crop, after_crop)
            before_during_diff = _image_diff_pixels(before_crop, during_crop)

            failures: list[str] = []

            if before_after_diff > MAX_AFTER_DIFF_PIXELS:
                failures.append(
                    f"Zoomed crop drifted too far from single-pane baseline: "
                    f"{before_after_diff} > {MAX_AFTER_DIFF_PIXELS}"
                )

            if before_during_diff < MIN_DURING_DIFF_PIXELS:
                failures.append(
                    f"Split crop did not diverge enough from single-pane baseline: "
                    f"{before_during_diff} < {MIN_DURING_DIFF_PIXELS}"
                )

            if before_after_diff > 0 and before_during_diff / before_after_diff < MIN_DURING_TO_AFTER_RATIO:
                failures.append(
                    "Split crop was not separated enough from the zoomed crop: "
                    f"{before_during_diff}/{before_after_diff} < {MIN_DURING_TO_AFTER_RATIO:.1f}x"
                )

            if failures:
                payload = {
                    "workspace": workspace_id,
                    "left_panel": left_panel_id,
                    "right_panel": right_panel_id,
                    "before_screenshot": before_screenshot,
                    "during_screenshot": during_screenshot,
                    "after_screenshot": after_screenshot,
                    "before_crop": before_crop,
                    "during_crop": during_crop,
                    "after_crop": after_crop,
                    "before_after_diff_pixels": before_after_diff,
                    "before_during_diff_pixels": before_during_diff,
                    "after_layout": after_layout,
                    "failures": failures,
                }
                raise cmuxError(json.dumps(payload, indent=2))

            print("PASS: zoomed pane hides the sibling browser visually")
            print(f"before_screenshot={before_screenshot}")
            print(f"during_screenshot={during_screenshot}")
            print(f"after_screenshot={after_screenshot}")
            print(f"before_crop={before_crop}")
            print(f"during_crop={during_crop}")
            print(f"after_crop={after_crop}")
            print(f"before_after_diff_pixels={before_after_diff}")
            print(f"before_during_diff_pixels={before_during_diff}")
            return 0
        finally:
            for crop_path in crop_paths:
                try:
                    os.remove(crop_path)
                except OSError:
                    pass
            try:
                client.close_workspace(workspace_id)
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
