# 10_macos_mcp (Port 5010)

## Purpose
Provides secure, controlled access to execute commands and interact with the filesystem on target macOS systems, similar to the Linux CLI server.

Tools are organized under the `os.macos.*` namespace.

## Namespaced Tools (Examples)

- **`os.macos.cli.*`**: General command execution and file operations.
  - `runCommand(command: str, cwd: str | None = None, timeout: int = 60) -> dict`: Executes a shell command (`bash -c`).
  - `readFile(path: str) -> str`: Reads file content.
  - `writeFile(path: str, content: str, append: bool = False)`: Writes to a file.
  - `listDirectory(path: str) -> list[str]`.
- **`os.macos.apps.*`**: Application management.
  - `listApps() -> list[str]`: Lists installed applications.
  - `openApp(appName: str)`: Opens an application (requires approval).
- **`os.macos.script.*`**: AppleScript/JXA execution.
  - `runAppleScript(script: str) -> str`: Executes an AppleScript string (requires approval).
  - `runJxaScript(script: str) -> str`: Executes a JXA (JavaScript for Automation) string (requires approval).

## Container Layout
```
10_macos_mcp/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt     # Python MCP SDK, paramiko (for SSH)
├── mcp_server.py
└── README.md
```

## Implementation Details
- **Framework:** Python with `mcp`/`fastmcp`.
- **Target Systems:** Requires an agent or SSH access to the target macOS machine(s).
  - **SSH:** Use `paramiko`. SSH access needs to be enabled on the target Mac.
  - **Agent:** A custom agent running on the Mac that this server communicates with.
- **Note:** Running macOS in Docker is generally not feasible or licensed. This server typically implies managing *external* macOS machines.

## Operating Principles & Security Considerations
Adheres strictly to [Operating Principles](../README.md#operating-principles).

1.  **OS Discovery:** Tool `os.macos.cli.getOsInfo()` using `sw_vers`.
2.  **Backup:** Tools modifying configs must create backups.
3.  **Approval for Modifications:** Required for `writeFile`, `runCommand` (non-read-only), `openApp`, `runAppleScript`, `runJxaScript`.
4.  **Read-Only Allowed:** `readFile`, `listDirectory`, `listApps`, `runCommand` (read-only commands like `ls`, `cat`, `mdfind`).
5.  **Logging:** Log all actions, commands, scripts, outputs via structured logging.
6.  **Shell Consistency:** Use `/bin/bash -c "..."` for `runCommand`.
7.  **Sensitive File Access:** Use `ALLOWED_READ_PATHS`.
8.  **Interactive Commands:** `runCommand` should fail; handle interaction via specific tools or planned approval.
9.  **Critical Actions:** System shutdown/reboot tools require approval.

**Additional Security:**
- **Command/Script Sanitization:** CRITICAL. Validate inputs, use allowlists (`ALLOWED_COMMANDS`). Be extremely cautious with script execution (`runAppleScript`, `runJxaScript`).
- **Path Restrictions:** Enforce `ALLOWED_READ_PATHS`, `ALLOWED_WRITE_PATHS`.
- **SSH Security:** Keys, secure storage (Docker secrets), known_hosts.

## Configuration
- `MCP_PORT=5010`
- `ALLOWED_COMMANDS`
- `ALLOWED_READ_PATHS`
- `ALLOWED_WRITE_PATHS`
- `SSH_HOSTS`
- `SSH_USER`
- `SSH_KEY_SECRET_PATH`

## Observability
- **Logging:** Adheres to project JSON standard, includes `correlation_id`.
- **Metrics:** Implement `os.macos.cli.getMetrics()`.
