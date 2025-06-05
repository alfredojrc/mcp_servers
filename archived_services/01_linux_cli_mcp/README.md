# Linux CLI MCP Service (`01_linux_cli_mcp`)

This MCP service provides tools to interact with a Linux command-line interface.

## Configuration

The service is configured via environment variables in `docker-compose.yml`:

- `MCP_PORT`: Port the MCP service listens on (default: `8001`).
- `ALLOWED_COMMANDS`: Comma-separated list of commands that `run_local_command` is allowed to execute (e.g., `ls,cat,grep,ps,df,echo,stat,head,tail,find,ssh`).
- `ALLOWED_READ_PATHS`: Colon-separated list of base paths that `read_file_tool` is allowed to read from (e.g., `/etc:/var/log:/tmp:/home`).
- `ALLOWED_WRITE_PATHS`: Colon-separated list of base paths that `write_file_tool` is allowed to write to (e.g., `/tmp`).

### SSH Configuration

This service can also execute commands on remote Linux hosts via SSH.

- `SSH_HOSTS`: Comma-separated list of hostnames that are configured for SSH access (e.g., `aicrusher,webserver01`).
- `SSH_USER`: The username to use for SSH connections (e.g., `jeriko`). This user is currently global for all configured `SSH_HOSTS`.
- `SSH_KEY_SECRET_PATH`: The path *inside the container* to the SSH private key file (e.g., `/secrets/aicrusher_jeriko_id_rsa`). This key is currently global for all configured `SSH_HOSTS`.

The corresponding SSH private key must be mounted into the container via `docker-compose.yml`, and the public key must be present in the `authorized_keys` file for the `SSH_USER` on each `SSH_HOSTS`.

Example `docker-compose.yml` snippet for SSH:
```yaml
services:
  01_linux_cli_mcp:
    # ... other config ...
    environment:
      - SSH_HOSTS=aicrusher
      - SSH_USER=jeriko
      - SSH_KEY_SECRET_PATH=/secrets/ssh_private_key_for_aicrusher
    volumes:
      - ./secrets/actual_private_key_file_on_host:/secrets/ssh_private_key_for_aicrusher:ro
      # ... other volumes ...
```

## Available Tools

- **`linux.runLocalCommand(command: str, args: Optional[List[str]] = None) -> Dict[str, Any]`**:
  - Executes a shell command directly on the container where the MCP service is running.
  - The `command` must be in the `ALLOWED_COMMANDS` list.
  - Example: `{"tool": "linux.runLocalCommand", "params": {"command": "ls", "args": ["-la", "/tmp"]}}`

- **`linux.readFile(path: str) -> Dict[str, Any]`**:
  - Reads the content of a file from the container.
  - The `path` must be within one of the `ALLOWED_READ_PATHS`.
  - Example: `{"tool": "linux.readFile", "params": {"path": "/var/log/syslog"}}`

- **`linux.writeFile(path: str, content: str, append: Optional[bool] = False) -> Dict[str, Any]`**:
  - Writes content to a file in the container.
  - The `path` must be within one of the `ALLOWED_WRITE_PATHS`.
  - Example: `{"tool": "linux.writeFile", "params": {"path": "/tmp/test.txt", "content": "Hello World"}}`

- **`linux.sshExecuteCommand(target_host: str, remote_command: str) -> Dict[str, Any]`**:
  - Executes a command on a pre-configured remote Linux host via SSH.
  - `target_host` must be one of the hosts defined in the `SSH_HOSTS` environment variable.
  - `remote_command` is the command string to execute on the remote host.
  - The connection uses the globally configured `SSH_USER` and `SSH_KEY_SECRET_PATH`.
  - SSH options `-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null` are used for convenience in containerized environments.
  - Example: `{"tool": "linux.sshExecuteCommand", "params": {"target_host": "aicrusher", "remote_command": "ls -la /home/jeriko"}}`

## Security

- Command and path validation is performed based on the `ALLOWED_*` environment variables.
- For SSH, security relies on the permissions of the SSH key and the user on the remote host. Be cautious with the commands executed remotely.
