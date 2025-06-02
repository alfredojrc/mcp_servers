# Multi-Platform MCP Deployment

## Overview
This MCP stack can be deployed on both macOS (laptop/hub) and Ubuntu (edge servers) using the same codebase with platform-specific configurations.

## Architecture Patterns

### 1. Hub Mode (macOS Laptop)
- Full orchestrator with all services
- SSH access to remote servers
- Cloud provider integrations
- Central monitoring and logging

### 2. Edge Mode (Ubuntu Servers) 
- Lightweight local execution
- Direct filesystem access
- No SSH loops (commands run locally)
- Minimal service set

## Deployment

### On macOS (Hub)
```bash
./deploy-macos.sh
```

### On Ubuntu (Edge)
```bash
./deploy-ubuntu.sh
```

## Key Differences

| Feature | macOS (Hub) | Ubuntu (Edge) |
|---------|-------------|---------------|
| SSH Access | ✅ To remote hosts | ❌ Local only |
| Cloud Services | ✅ All enabled | ❌ Disabled |
| macOS Service | ✅ Enabled | ❌ Disabled |
| File Paths | `/Users/alf` | `/home/jeriko` |
| Freqtrade | Via SSH | Direct local |

## Development Workflow

1. **Single Repository**: Both environments use the same repo
2. **Platform Configs**: Use `-f docker-compose.{platform}.yml`
3. **Git Sync**: Regular `git pull` on both machines
4. **Secrets**: Platform-specific (don't sync SSH keys)

## Environment Variables

### Shared
- `MCP_PORT_*`: Service ports
- `LOG_LEVEL`: Logging verbosity

### Platform-Specific
- `PLATFORM`: macos/ubuntu
- `SSH_HOSTS`: Remote hosts (macOS only)
- `PACKAGE_MANAGER`: apt/brew

## Best Practices

1. **Test Locally First**: Changes on Ubuntu before pushing
2. **Use Feature Flags**: For platform-specific code
3. **Abstract Paths**: Use environment variables
4. **Document Differences**: In service READMEs