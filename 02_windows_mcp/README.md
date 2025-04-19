# 02_windows_mcp (Port 8002)

## Purpose
Provides secure, controlled access to execute PowerShell commands and interact with target Windows systems.

Tools are organized under the `os.windows.*` namespace.

## Namespaced Tools (Examples)

- **`os.windows.ps.*`**: PowerShell execution.
  - `runScript(scriptBlock: str, timeout: int = 60) -> dict`: Executes a PowerShell script block. Returns output streams, exit code.
  - `runCommand(command: str, timeout: int = 60) -> dict`: Executes a single PowerShell command.
- **`os.windows.fs.*`**: File system operations.
  - `readFile(path: str) -> str`: Reads file content (`Get-Content`).
  - `writeFile(path: str, content: str, append: bool = False)`: Writes to a file (`Set-Content`, `Add-Content`).
  - `listDirectory(path: str) -> list[dict]`: Lists directory contents (`Get-ChildItem`).
  - `testPath(path: str) -> bool`: Checks if a path exists (`Test-Path`).
- **`os.windows.process.*`**: Process management.
  - `getProcess(name: str | None = None, id: int | None = None) -> list[dict]`: Gets running processes (`Get-Process`).
  - `stopProcess(name: str | None = None, id: int | None = None)`: Stops a process (Requires approval).
- **`os.windows.service.*`**: Service management.
  - `getService(name: str) -> dict`: Gets service status (`Get-Service`).
  - `startService(name: str)`: Starts a service (Requires approval).
  - `stopService(name: str)`: Stops a service (Requires approval).
  - `restartService(name: str)`: Restarts a service (Requires approval).

## Container Layout
```
02_windows_mcp/
├── Dockerfile             # Likely based on PowerShell Core or Windows container
├── entrypoint.ps1
├── requirements.psd1    # PowerShell module dependencies
├── mcp_server.ps1       # Server implementation (PowerShell)
└── README.md
```
*(Note: Implementation could also be Python using libraries like `pywinrm`)*

## Implementation Details
- **Framework:** Could be PowerShell using a custom MCP implementation or Python using `pywinrm` to connect to remote Windows machines.
- **Target Systems:** Requires WinRM enabled on target Windows machines or an agent.

## Operating Principles & Security Considerations
Adheres strictly to [Operating Principles](../README.md#operating-principles).

1.  **OS Discovery:** Tool `os.windows.ps.getOsInfo()` using `Get-ComputerInfo` or `$PSVersionTable`.
2.  **Backup:** Tools modifying configs must create backups (`Copy-Item ... -Destination "$($path).BAK_$(Get-Date -Format 'yyyyMMdd_HHmm')"`).
3.  **Approval for Modifications:** Required for `writeFile`, `runScript`/`runCommand` (non-read-only), `stopProcess`, `start/stop/restartService`.
4.  **Read-Only Allowed:** `readFile`, `listDirectory`, `testPath`, `getProcess`, `getService`, `runScript`/`runCommand` (read-only commands like `Get-Content`, `Get-ChildItem`, `Get-Process`, `Get-Service`).
5.  **Logging:** Log all actions, commands/scripts, outputs via structured logging.
6.  **Shell Consistency:** Uses PowerShell.
7.  **Sensitive File Access:** Use `ALLOWED_READ_PATHS`.
8.  **Interactive Commands:** Should fail; handle via specific tools or planned approval.
9.  **Critical Actions:** Service/process stopping/starting, system restarts require approval.

**Additional Security:**
- **Command/Script Sanitization:** CRITICAL. Validate inputs, use allowlists (`ALLOWED_COMMANDS`).
- **Path Restrictions:** Enforce `ALLOWED_READ_PATHS`, `ALLOWED_WRITE_PATHS`.
- **WinRM Security:** Use HTTPS (certificate validation), configure trusted hosts carefully, use strong authentication (Kerberos, CredSSP, NTLM - with appropriate security considerations for each).
- **Least Privilege:** Run WinRM endpoints and execute commands with minimal necessary user privileges.

## Configuration
- `MCP_PORT=8002`
- `ALLOWED_COMMANDS` (PowerShell commands)
- `ALLOWED_READ_PATHS`
- `ALLOWED_WRITE_PATHS`
- `WINRM_HOSTS`
- `WINRM_USER`
- `