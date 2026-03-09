#!/usr/bin/env python3
"""
End-to-end test for sidebar metadata terminal-stream fallback.

Validates:
1) mutating sidebar CLI commands still work when CMUX_SOCKET_PATH is invalid
2) updates are routed through the terminal stream back to the originating workspace
3) the fallback does not create visible desktop notifications
"""

from __future__ import annotations

import os
import sys
import time
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cmux import cmux, cmuxError  # noqa: E402


def _resolve_cmux_cli() -> str:
    override = os.environ.get("CMUX_CLI")
    if override and os.path.exists(override) and os.access(override, os.X_OK):
        return override

    candidates: list[str] = []
    candidates.extend(glob.glob(os.path.expanduser("~/Library/Developer/Xcode/DerivedData/*/Build/Products/Debug/cmux")))
    candidates.extend(glob.glob("/tmp/cmux-*/Build/Products/Debug/cmux"))
    candidates.extend(glob.glob("/private/tmp/cmux-*/Build/Products/Debug/cmux"))
    candidates = [path for path in candidates if os.path.exists(path) and os.access(path, os.X_OK)]
    if not candidates:
        return "cmux"

    candidates.sort(key=os.path.getmtime, reverse=True)
    return candidates[0]


def _parse_sidebar_state(text: str) -> dict[str, str]:
    data: dict[str, str] = {}
    for raw in (text or "").splitlines():
        line = raw.rstrip("\n")
        if not line or line.startswith("  "):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip()
    return data


def _wait_for_sidebar_field(
    client: cmux,
    tab_id: str,
    key: str,
    expected: str,
    timeout: float = 8.0,
    interval: float = 0.1,
) -> dict[str, str]:
    start = time.time()
    while time.time() - start < timeout:
        state = _parse_sidebar_state(client.sidebar_state(tab=tab_id))
        if state.get(key) == expected:
            return state
        time.sleep(interval)
    raise AssertionError(f"Timed out waiting for {key}={expected!r}")


def _wait_for_sidebar_text(
    client: cmux,
    tab_id: str,
    expected_substring: str,
    timeout: float = 8.0,
    interval: float = 0.1,
) -> None:
    start = time.time()
    while time.time() - start < timeout:
        if expected_substring in client.sidebar_state(tab=tab_id):
            return
        time.sleep(interval)
    raise AssertionError(f"Timed out waiting for sidebar text containing {expected_substring!r}")


def _wait_for_screen_text(
    client: cmux,
    expected_substring: str,
    timeout: float = 8.0,
    interval: float = 0.1,
) -> str:
    start = time.time()
    while time.time() - start < timeout:
        screen = client.read_screen()
        if expected_substring in screen:
            return screen
        time.sleep(interval)
    raise AssertionError(f"Timed out waiting for screen text containing {expected_substring!r}")


def _send_sidebar_command(client: cmux, surface_id: str, command: str) -> None:
    client.send_surface(surface_id, f"{command}\n")
    # The terminal-stream fallback is delivered asynchronously through Ghostty action handling.
    # Giving the surface a brief settle window keeps this E2E test deterministic.
    time.sleep(1.0)


def main() -> int:
    try:
        with cmux() as client:
            cli_path = _resolve_cmux_cli()
            new_tab_id = client.new_tab()
            client.select_tab(new_tab_id)
            time.sleep(0.6)

            tab_id = client.current_workspace()
            client.reset_sidebar(tab=tab_id)
            client.clear_notifications()
            time.sleep(0.2)

            surfaces = client.list_surfaces(tab_id)
            if not surfaces:
                raise AssertionError("Expected at least one surface in the new workspace")
            target_surface = next((surface_id for _, surface_id, focused in surfaces if focused), surfaces[0][1])

            broken_socket = "/tmp/cmux-sidebar-stream-missing.sock"
            shell_prefix = f"env CMUX_SOCKET_PATH={broken_socket}"

            _send_sidebar_command(
                client,
                target_surface,
                f'{shell_prefix} "{cli_path}" set-status remote ok --icon bolt --color "#ff9500"'
            )
            _wait_for_sidebar_field(client, tab_id, "status_count", "1")
            _wait_for_sidebar_text(client, tab_id, "remote=ok icon=bolt color=#ff9500")

            _send_sidebar_command(
                client,
                target_surface,
                f'{shell_prefix} "{cli_path}" set-progress 0.42 --label "remote build"'
            )
            _wait_for_sidebar_field(client, tab_id, "progress", "0.42 remote build")

            _send_sidebar_command(
                client,
                target_surface,
                f'{shell_prefix} "{cli_path}" log --level success --source remote -- "stream path works"'
            )
            _wait_for_sidebar_field(client, tab_id, "log_count", "1")
            _wait_for_sidebar_text(client, tab_id, "[success] stream path works")

            notifications = client.list_notifications()
            if notifications:
                raise AssertionError(f"Expected no notifications from sidebar fallback, got: {notifications}")

            _send_sidebar_command(client, target_surface, f'{shell_prefix} "{cli_path}" clear-status remote')
            _wait_for_sidebar_field(client, tab_id, "status_count", "0")

            _send_sidebar_command(client, target_surface, f'{shell_prefix} "{cli_path}" clear-progress')
            _wait_for_sidebar_field(client, tab_id, "progress", "none")

            _send_sidebar_command(client, target_surface, f'{shell_prefix} "{cli_path}" clear-log')
            _wait_for_sidebar_field(client, tab_id, "log_count", "0")

            _send_sidebar_command(
                client,
                target_surface,
                (
                    "env CMUX_SOCKET_PATH=/tmp/cmux-sidebar-stream-missing.sock "
                    f'"{cli_path}" --socket /tmp/cmux-explicit-target.sock set-status explicit blocked; '
                    'printf "__explicit_socket_exit__:%s\\n" "$?"'
                )
            )
            _wait_for_screen_text(client, "__explicit_socket_exit__:")
            _wait_for_sidebar_field(client, tab_id, "status_count", "0")

            _send_sidebar_command(
                client,
                target_surface,
                (
                    "env CMUX_SOCKET_PATH=/tmp/cmux-sidebar-stream-missing.sock "
                    f'"{cli_path}" --window window:999 set-status explicit blocked; '
                    'printf "__explicit_window_exit__:%s\\n" "$?"'
                )
            )
            _wait_for_screen_text(client, "__explicit_window_exit__:")
            _wait_for_sidebar_field(client, tab_id, "status_count", "0")

            try:
                client.close_tab(new_tab_id)
            except Exception:
                pass

        print("Sidebar terminal-stream fallback test passed.")
        return 0
    except (cmuxError, AssertionError) as error:
        print(f"Sidebar terminal-stream fallback test failed: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
