# Available MCP Commands

## System Commands (Master Orchestrator)
- `system.health` - Check health status of all MCP services
- `system.listServices` - List all available MCP services and their endpoints

## Documentation Service (11_documentation_mcp)
- `docs.search` - Search documentation with keywords
- `docs.get` - Get a specific document by ID
- `docs.list` - List all available documents
- `docs.create` - Create a new document
- `docs.update` - Update an existing document

## Crypto Trading Service (17_crypto_trader_mcp)
- `crypto.market.price` - Get current cryptocurrency prices
- `crypto.market.ohlcv` - Get OHLCV (Open/High/Low/Close/Volume) data
- `crypto.ta.indicators` - Calculate technical analysis indicators
- `crypto.ta.signals` - Get trading signals based on TA
- `crypto.trade.simulate` - Simulate trades with historical data

## Vector Database Service (18_vector_db_mcp)
- `vector.collection.create` - Create a new vector collection
- `vector.collection.list` - List all collections
- `vector.document.add` - Add documents to a collection
- `vector.search.semantic` - Perform semantic search
- `vector.document.update` - Update documents in a collection

## Services Without Standard MCP Tools

These services may have different implementations or require checking their specific files:

### Linux CLI Service (01_linux_cli_mcp)
- `os.linux.cli.getOsInfo` - Get operating system information
- `os.linux.cli.runCommand` - Execute shell commands (requires approval)
- `os.linux.cli.readFile` - Read file contents
- `os.linux.cli.writeFile` - Write to files (requires approval)
- `linux.sshExecuteCommand` - Execute commands via SSH

### Kubernetes Service (08_k8s_mcp)  
- Expected: `infra.k8s.*` commands for cluster management
- Status: Needs investigation

### CMDB Service (12_cmdb_mcp)
- Expected: `cmdb.*` commands for configuration management
- Status: Needs investigation

### Secrets Service (13_secrets_mcp)
- Expected: `secrets.*` commands for secret management
- Status: Needs investigation

### FreqTrade Service (15_freqtrade_mcp)
- Expected: `trading.freqtrade.knowledge.*` commands
- Status: Needs investigation

### AI Models Service (16_ai_models_mcp)
- Expected: `ai.models.*` commands for LLM access
- Status: Needs investigation

## Usage Example

To use these commands through Claude Code, the MCP orchestrator will route your requests to the appropriate service based on the command namespace.