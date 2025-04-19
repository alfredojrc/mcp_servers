# 01_linux_cli_mcp (Port 5001)

## Purpose
This MCP server provides secure, controlled access to execute commands and interact with the filesystem on target Linux systems. It serves as the primary interface for managing Linux hosts and the services running on them (like Nginx, Ceph, MTAs, SFTP, etc.) without needing dedicated MCP servers for each subsystem.

Tools are organized using namespaces under the `os.linux.*` domain, managed by the central `00_master_mcp` host.

## Namespaced Tools

This server organizes its tools under namespaces to provide clarity and avoid collisions. Examples:

- **`os.linux.cli.*`**: General command execution and basic file operations.
  - `runCommand(command: str, cwd: str | None = None, timeout: int = 60) -> dict`: Executes a shell command. Returns stdout, stderr, exit code.
  - `readFile(path: str) -> str`: Reads the content of a file.
  - `writeFile(path: str, content: str, append: bool = False)`: Writes content to a file.
  - `listDirectory(path: str) -> list[str]`: Lists directory contents.
- **`os.linux.nginx.*`**: Tools specific to managing Nginx.
  - `reloadConfig() -> dict`: Attempts to reload the Nginx configuration (`nginx -s reload`).
  - `checkConfig() -> dict`: Runs `nginx -t` to test configuration.
  - `getAccessLogTail(lines: int = 50) -> str`: Tails the primary Nginx access log.
- **`os.linux.ceph.*`**: Tools for interacting with a Ceph cluster via CLI.
  - `getStatus() -> dict`: Runs `ceph status`.
  - `getOSDTree() -> dict`: Runs `ceph osd tree`.
- **`os.linux.mta.*`**: Tools for managing a Mail Transfer Agent (e.g., Postfix).
  - `checkQueue() -> dict`: Shows the mail queue status.
- **`os.linux.sftp.*`**: Tools for managing an SFTP server.
  - `listUsers() -> list[str]`: Lists configured SFTP users.

*(Note: These are illustrative examples. Actual implementation requires defining these tools using an MCP server framework like Python's `mcp` or `fastmcp`)*

## Container Layout

```
01_linux_cli_mcp/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt     # Python MCP SDK, paramiko (optional for direct SSH)
├── mcp_server.py        # Server implementation
└── README.md            # (this file)
```

## Implementation Details

- **Framework:** Typically built using Python with the `mcp` or `fastmcp` library.
- **Command Execution:** Uses Python's `subprocess` module to run shell commands safely.
- **Tool Registration:** Tools must be registered with the MCP server instance, specifying their full namespaced name (e.g., `@mcp_server.tool("os.linux.nginx.reloadConfig")`).
- **Target Systems:** How this server connects to the target Linux machine(s) needs definition:
    - **Option A (Managing the Host):** If the container needs to manage the Docker host it runs on, mount relevant host paths or the Docker socket (`/var/run/docker.sock`) and potentially run commands via `docker exec` on other containers or directly if privileged.
    - **Option B (Managing Remote Hosts):** Use SSH libraries (like `paramiko` in Python) to connect to remote Linux machines. SSH credentials/keys would need to be securely provided via environment variables or mounted secrets.
    - **Option C (Agent Installation):** Install a lightweight agent on target machines that this MCP server communicates with (more complex).

## Operating Principles & Security Considerations

This server interacts directly with Linux systems and therefore adheres strictly to the [Operating Principles](../README.md#operating-principles) defined project-wide:

1.  **OS Discovery:** Implement a tool like `os.linux.cli.getOsInfo()` that reads `/etc/os-release` or uses `lsb_release -a` before modification tasks.
2.  **Configuration Backup:** Tools modifying config files (e.g., `writeFile` if used on conf files, or specific tools like `nginx.updateSiteConfig`) *must* programmatically create a backup (`*.BAK_YYYYMMDD_hhmm`) before writing changes.
3.  **Approval for Modifications:** Any tool designed to modify the system state (write files, install packages, change service status, run non-read-only commands via `runCommand`) MUST include a parameter (e.g., `require_approval: bool = True`) or internal logic that prevents execution unless explicit approval context is provided (mechanism TBD by `00_master_mcp` orchestration).
4.  **Read-Only Allowed:** Tools like `readFile`, `listDirectory`, `runCommand` (when executing explicitly allowed read-only commands like `ls`, `cat`, `grep`, `ps`, `df`, `ceph status`, `nginx -t`) can execute without prior approval.
5.  **Logging:** All tool executions, including the *full command string* for `runCommand`, parameters, target paths, stdout/stderr, and exit codes MUST be logged via structured logging (see [Observability](#observability)).
6.  **Shell Consistency:** The `runCommand` tool MUST use `/bin/bash -c "..."` for execution.
7.  **Sensitive File Access:** Limit `readFile` paths via `ALLOWED_READ_PATHS`. Avoid reading files like `/etc/shadow` unless absolutely necessary and approved.
8.  **Interactive Commands:** The `runCommand` tool should generally *fail* if a command requires interactive input. If interaction is essential for a specific *approved* task, the plan must be outlined during the approval step.
9.  **Critical Actions:** Tools for rebooting (`os.linux.cli.rebootSystem`) require approval and should include checks (e.g., checking for active users or critical processes) before execution.

**Additional Security:**

-   **Command Sanitization/Filtering:** Implement rigorous input sanitization for *all* parameters, especially for `runCommand` and `writeFile`. Use allowlists for commands passed to `runCommand` via the `ALLOWED_COMMANDS` environment variable.
-   **Path Restrictions:** Enforce `ALLOWED_READ_PATHS` and `ALLOWED_WRITE_PATHS`.
-   **Least Privilege:** Run the container process as a non-root user if possible. If root is needed inside, ensure the container itself runs with minimal host privileges.
-   **SSH Security (if using Remote Hosts):** Use key-based auth, secure key storage (Docker secrets preferred over env vars), known_hosts checking.

## Configuration

Environment variables needed might include:

-   `MCP_PORT=5001`
-   `ALLOWED_COMMANDS` (Comma-separated list of allowed base commands, e.g., `ls,cat,grep,ps,df,ceph,nginx,systemctl,useradd`)
-   `ALLOWED_READ_PATHS` (Colon-separated list of allowed directories/files for reading, e.g., `/var/log:/etc/nginx:/home/user/.config`)
-   `ALLOWED_WRITE_PATHS` (Colon-separated list of allowed directories for writing, e.g., `/etc/nginx/sites-enabled:/tmp`)
-   `SSH_HOSTS` (Comma-separated list of allowed target hosts if using SSH)
-   `SSH_USER`
-   `SSH_KEY_SECRET_PATH` (Path to mounted Docker secret for SSH key)

## Observability

-   **Logging:** Adheres to the project's structured JSON logging standard, including `correlation_id` received from the orchestrator.
-   **Metrics:** Implements a Prometheus metrics endpoint on port `9091` (configurable via `METRICS_PORT` env var). Exposes metrics like `mcp_tool_latency_seconds`, `mcp_tool_calls_total`, and `mcp_tool_errors_total` labeled by `tool_name`.
-   Should implement a tool `os.linux.cli.getMetrics()` returning basic counters (e.g., commands run, files read/written, errors).
