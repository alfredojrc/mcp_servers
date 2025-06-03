#!/usr/bin/env python3
"""
Demo: External Project Connecting to Documentation MCP Service
Shows how other projects can use the documentation service via Claude Code
"""
import asyncio
import httpx
import json
from datetime import datetime

DOCS_MCP_URL = "http://localhost:8011"

async def create_project_documentation():
    """Example: Create documentation for an external project"""
    print("\n🚀 Demo: External Project Documentation via MCP")
    print("="*60)
    
    # Simulate an external project wanting to document itself
    project_name = "MyAwesomeProject"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # 1. Create main project documentation
        print(f"\n1. Creating documentation for '{project_name}'...")
        
        project_doc = {
            "tool": "docs.create",
            "arguments": {
                "title": f"{project_name} - Overview",
                "content": f"""# {project_name} Documentation

## Overview
{project_name} is a revolutionary application that demonstrates how external projects can integrate with the MCP documentation service.

## Features
- Real-time data processing
- Cloud-native architecture
- AI-powered analytics
- Seamless MCP integration

## Architecture
The project follows a microservices architecture:
- Frontend: React + TypeScript
- Backend: Python FastAPI
- Database: PostgreSQL
- Cache: Redis
- Message Queue: RabbitMQ

## Getting Started
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables
4. Run: `python main.py`

## MCP Integration
This project uses the MCP Documentation Service to maintain its documentation automatically.
""",
                "category": "projects",
                "tags": ["external", "demo", "integration", "microservices"],
                "metadata": {
                    "author": project_name,
                    "project_url": f"https://github.com/example/{project_name.lower()}",
                    "version": "1.0.0"
                },
                "approval_token": "demo-token"  # In real use, this would be properly managed
            }
        }
        
        try:
            response = await client.post(f"{DOCS_MCP_URL}/execute", json=project_doc)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Created: {result.get('title')} (ID: {result.get('id')})")
                project_doc_id = result.get('id')
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Error: {e}")
            return
        
        # 2. Create API documentation
        print(f"\n2. Creating API documentation...")
        
        api_doc = {
            "tool": "docs.create",
            "arguments": {
                "title": f"{project_name} - API Reference",
                "content": f"""# {project_name} API Reference

## Base URL
```
https://api.{project_name.lower()}.com/v1
```

## Authentication
All API requests require a Bearer token in the Authorization header:
```
Authorization: Bearer YOUR_API_TOKEN
```

## Endpoints

### GET /health
Health check endpoint
- **Response**: `{{"status": "healthy", "version": "1.0.0"}}`

### POST /data/process
Process incoming data
- **Request Body**:
  ```json
  {{
    "data": "base64_encoded_data",
    "format": "json|csv|xml",
    "options": {{}}
  }}
  ```
- **Response**: Processing result

### GET /analytics/report
Generate analytics report
- **Query Parameters**:
  - `start_date`: ISO date string
  - `end_date`: ISO date string
  - `metrics`: Comma-separated list
""",
                "category": "api",
                "tags": ["external", "api", "rest", project_name.lower()],
                "metadata": {
                    "author": project_name,
                    "api_version": "v1"
                },
                "approval_token": "demo-token"
            }
        }
        
        try:
            response = await client.post(f"{DOCS_MCP_URL}/execute", json=api_doc)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Created: {result.get('title')} (ID: {result.get('id')})")
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # 3. Create a guide
        print(f"\n3. Creating deployment guide...")
        
        guide_doc = {
            "tool": "docs.create",
            "arguments": {
                "title": f"Deploying {project_name} to Production",
                "content": f"""# Deploying {project_name} to Production

## Prerequisites
- Docker and Docker Compose
- Kubernetes cluster (1.20+)
- Helm 3.x
- Valid SSL certificates

## Step-by-Step Deployment

### 1. Build Docker Images
```bash
docker build -t {project_name.lower()}:latest .
docker tag {project_name.lower()}:latest your-registry/{project_name.lower()}:latest
docker push your-registry/{project_name.lower()}:latest
```

### 2. Configure Secrets
Create Kubernetes secrets:
```bash
kubectl create secret generic {project_name.lower()}-secrets \\
  --from-literal=db_password=$DB_PASSWORD \\
  --from-literal=api_key=$API_KEY
```

### 3. Deploy with Helm
```bash
helm install {project_name.lower()} ./charts/{project_name.lower()} \\
  --namespace production \\
  --values values.production.yaml
```

### 4. Verify Deployment
```bash
kubectl get pods -n production
kubectl logs -f deployment/{project_name.lower()}
```

## Monitoring
- Metrics: Prometheus + Grafana
- Logs: ELK Stack
- Traces: Jaeger

## Troubleshooting
Common issues and solutions...
""",
                "category": "guides",
                "tags": ["deployment", "kubernetes", "docker", "production"],
                "metadata": {
                    "author": project_name,
                    "difficulty": "intermediate"
                },
                "approval_token": "demo-token"
            }
        }
        
        try:
            response = await client.post(f"{DOCS_MCP_URL}/execute", json=guide_doc)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Created: {result.get('title')} (ID: {result.get('id')})")
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # 4. Update existing documentation
        if project_doc_id:
            print(f"\n4. Updating project documentation...")
            
            update_doc = {
                "tool": "docs.update",
                "arguments": {
                    "doc_id": project_doc_id,
                    "content": f"""# {project_name} Documentation

## Overview
{project_name} is a revolutionary application that demonstrates how external projects can integrate with the MCP documentation service.

## 🆕 Recent Updates (v1.1.0)
- Added real-time WebSocket support
- Improved performance by 40%
- Enhanced security features
- New analytics dashboard

## Features
- Real-time data processing
- Cloud-native architecture
- AI-powered analytics
- Seamless MCP integration
- **NEW**: WebSocket API
- **NEW**: Advanced caching

## Architecture
The project follows a microservices architecture:
- Frontend: React + TypeScript
- Backend: Python FastAPI
- Database: PostgreSQL
- Cache: Redis
- Message Queue: RabbitMQ
- **NEW**: WebSocket Server

## Getting Started
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure environment variables
4. Run: `python main.py`

## MCP Integration
This project uses the MCP Documentation Service to maintain its documentation automatically.

## Contributing
See CONTRIBUTING.md for guidelines.
""",
                    "version_note": "Added v1.1.0 features and updates",
                    "approval_token": "demo-token"
                }
            }
            
            try:
                response = await client.post(f"{DOCS_MCP_URL}/execute", json=update_doc)
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ Updated to version: {result.get('version')}")
                else:
                    print(f"❌ Failed: HTTP {response.status_code}")
            except Exception as e:
                print(f"❌ Error: {e}")
        
        # 5. Search for the created documentation
        print(f"\n5. Searching for our documentation...")
        
        search_request = {
            "tool": "docs.search",
            "arguments": {
                "query": project_name,
                "tags": ["external"]
            }
        }
        
        try:
            response = await client.post(f"{DOCS_MCP_URL}/execute", json=search_request)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Found {result.get('count')} documents:")
                for doc in result.get('documents', []):
                    print(f"   - {doc['title']} ({doc['category']})")
            else:
                print(f"❌ Search failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

async def demonstrate_automated_docs():
    """Show how a CI/CD pipeline might update docs automatically"""
    print("\n\n📋 Demo: Automated Documentation Updates (CI/CD)")
    print("="*60)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Simulate automated changelog updates
        changelog = {
            "tool": "docs.create",
            "arguments": {
                "title": "Release Notes - v2.5.0",
                "content": f"""# Release Notes - v2.5.0

**Release Date**: {datetime.now().strftime('%Y-%m-%d')}

## 🎉 New Features
- **API Rate Limiting**: Implemented configurable rate limits per endpoint
- **Batch Processing**: New batch API for processing multiple requests
- **Webhooks**: Real-time event notifications via webhooks

## 🐛 Bug Fixes
- Fixed memory leak in data processing pipeline
- Resolved authentication timeout issues
- Corrected timezone handling in reports

## 🔧 Improvements
- 30% faster response times for analytics queries
- Reduced Docker image size by 45%
- Enhanced error messages and logging

## 📦 Dependencies
- Updated FastAPI to 0.104.1
- Upgraded PostgreSQL driver
- Security patches applied

## 🚨 Breaking Changes
- API endpoint `/v1/data` renamed to `/v1/process`
- Removed deprecated authentication methods

## 📝 Migration Guide
See the full migration guide in the documentation.

---
*This release was automatically documented by our CI/CD pipeline*
""",
                "category": "projects",
                "tags": ["release-notes", "changelog", "v2.5.0", "automated"],
                "metadata": {
                    "author": "CI/CD Pipeline",
                    "build_number": "2024.1.1234",
                    "commit_hash": "abc123def456"
                },
                "approval_token": "demo-token"
            }
        }
        
        try:
            response = await client.post(f"{DOCS_MCP_URL}/execute", json=changelog)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Automated release notes created: {result.get('title')}")
            else:
                print(f"❌ Failed: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ Error: {e}")

async def main():
    """Run demonstrations"""
    print("\n" + "="*60)
    print("MCP Documentation Service - External Project Integration Demo")
    print("="*60)
    print("\nThis demo shows how external projects can use the MCP")
    print("documentation service to manage their documentation.")
    
    # Check if documentation service is running
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{DOCS_MCP_URL}/health")
            if response.status_code != 200:
                print("\n❌ Documentation service is not running!")
                print("   Please start it with: docker-compose up -d mcp_11_documentation")
                return
    except:
        print("\n❌ Cannot connect to documentation service at", DOCS_MCP_URL)
        print("   Please ensure the service is running")
        return
    
    print("\n✅ Documentation service is available")
    
    # Run demonstrations
    await create_project_documentation()
    await demonstrate_automated_docs()
    
    print("\n\n" + "="*60)
    print("✨ Demo completed successfully!")
    print("\nKey Takeaways:")
    print("1. External projects can easily create and update documentation")
    print("2. Documentation is organized by categories (projects, api, guides, etc.)")
    print("3. Full-text search makes finding docs easy")
    print("4. Version control tracks all changes")
    print("5. CI/CD pipelines can automate documentation updates")
    print("\nThe documentation service acts as a central knowledge base")
    print("for all your projects, accessible via Claude Code!")

if __name__ == "__main__":
    asyncio.run(main())