# 13_secrets_mcp (Port 5013)

## Purpose
Provides a unified interface to retrieve secrets (API keys, passwords, etc.) from various configured backend secret management systems.

This server abstracts the underlying secret storage mechanism from the consuming services, allowing them to request secrets by name without needing to know how to interact with KeePass, Azure Key Vault, Google Secret Manager, etc.

Tools can be organized under namespaces corresponding to the backend (e.g., `secrets.keepass.*`, `secrets.azurekv.*`).

## Supported Backends (Examples)

- **Local KeePass (`.kdbx` file):** See important security caveats below.
- **Azure Key Vault:** Uses Azure SDK and Service Principal/Managed Identity.
- **Google Secret Manager:** Uses Google Cloud SDK and ADC/Service Account.
- **HashiCorp Vault:** Uses Vault API/SDK.
- **Environment Variables:** Can expose specific environment variables passed to this container as "secrets".

## Namespaced Tools (Examples)

- **`secrets.getSecret(secretName: str, version: str | None = None) -> str | None`**: Attempts to retrieve the latest (or specific version) of a secret by its logical name. The server internally determines which backend holds this secret based on configuration or naming convention.
- **`secrets.keepass.getEntry(entryPath: str, field: str = 'password') -> str | None`**: Retrieves a specific field (password, username, notes) from a KeePass entry specified by its path.
- **`secrets.azurekv.getSecret(secretName: str, vaultUrl: str | None = None) -> str | None`**: Retrieves a secret from Azure Key Vault.
- **`secrets.gcpsm.getSecret(secretName: str, projectId: str | None = None, version: str = 'latest') -> str | None`**: Retrieves a secret from Google Secret Manager.

## Container Layout
```
13_secrets_mcp/
├── Dockerfile
├── entrypoint.sh
├── requirements.txt     # Python MCP SDK, pykeepass, azure-keyvault-secrets, google-cloud-secret-manager, hvac (for Vault), etc.
├── mcp_server.py        # Server implementation
├── config.yaml          # Optional: Configuration mapping secret names to backends
└── README.md            # (this file)
```

## Implementation Details
- **Framework:** Python with `mcp`/`fastmcp`.
- **Backend Logic:** The core logic resides in `mcp_server.py`, which needs to:
    - Initialize clients for configured backends.
    - Implement the `getSecret` tool to route requests based on `secretName` to the appropriate backend client.
    - Implement backend-specific tools if needed.

## Operating Principles & Security Considerations
This service is critical for security.

1.  **OS Discovery:** N/A.
2.  **Backup:** N/A (Backups handled by underlying secret stores like KeePass file backups or cloud provider backups).
3.  **Approval for Modifications:** N/A (This service should ideally be READ-ONLY for secrets). Modifying secrets should happen directly in the backend stores.
4.  **Read-Only Allowed:** Yes, retrieving secrets is the primary function.
5.  **Logging:** Log **secret retrieval requests** (including requested secret name, requesting agent/context ID if available) but **NEVER log the secret values themselves**. Log errors from backend stores. Use structured logging.
6.  **Shell Consistency:** N/A.
7.  **Sensitive File Access:** Reads backend credentials (KeePass password/keyfile, SP secrets, service account keys).
8.  **Interactive Commands:** N/A.
9.  **Critical Actions:** Retrieving highly sensitive secrets.

**Additional Security (VERY IMPORTANT):**
- **KeePass Unlocking Challenge:** Accessing a local `.kdbx` file from a container is problematic. Securely providing the master password/keyfile is difficult. The recommended approach is using Docker secrets (`KEEPASS_PASSWORD_SECRET_PATH`), but this requires careful setup and understanding the implications. **Using dedicated, API-driven secret managers (Azure KV, GCP SM, Vault) is generally more secure and robust for server environments.**
- **Backend Credential Security:** Store credentials for Azure, GCP, Vault, etc., using Docker secrets and mount them read-only into the container.
- **Network Security:** Limit network access to this container. Ensure communication with cloud secret managers uses TLS.
- **Access Control:** Implement logic within the `getSecret` tool (or via `00_master_mcp` policies) to restrict which secrets can be requested by which downstream service/context.
- **Least Privilege:** The credentials used by this service to access backends (e.g., Azure Service Principal, GCP Service Account) should have ONLY the necessary permissions (e.g., read-only access to specific secrets).
- **Auditing:** Ensure logging provides a clear audit trail of *who* or *what* requested *which* secret (by name) and *when*.

## Configuration
- `MCP_PORT=5013`
- **Per-Backend Configuration (Examples):**
  - `KEEPASS_DB_PATH` (Path to mounted .kdbx file)
  - `KEEPASS_PASSWORD_SECRET_PATH` (Path to Docker secret containing master password)
  - `KEEPASS_KEYFILE_PATH` (Optional: path to mounted keyfile)
  - `AZURE_VAULT_URL`
  - `AZURE_CLIENT_ID`
  - `AZURE_TENANT_ID`
  - `AZURE_CLIENT_SECRET_SECRET_PATH`
  - `GOOGLE_APPLICATION_CREDENTIALS` (Path to mounted GCP service account key)
  - `VAULT_ADDR`
  - `VAULT_TOKEN_SECRET_PATH`

## Observability
- **Logging:** Adheres to project JSON standard, includes `correlation_id`. CRITICAL: **Do not log secret values.**
- **Metrics:** Implement `secrets.getMetrics()` (e.g., secrets requested count, backend errors). 