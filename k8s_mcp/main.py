"""
Kubernetes MCP (Mesh Configuration Protocol) server.

This server provides access to Kubernetes documentation, APIs, and references.
It also provides functionality to interact with a Kubernetes cluster.
"""
import os
import json
import logging
import time
import threading
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request, send_from_directory, render_template, Response, stream_with_context, Blueprint
from dotenv import load_dotenv
import requests
import markdown
from bs4 import BeautifulSoup
import yaml
from templates import get_template, list_templates, save_templates
from k8s_client import get_k8s_client
from flask_cors import CORS
from kubernetes import client, config
from kubernetes.client.rest import ApiException
from queue import Queue

# Load environment variables
load_dotenv()

# Setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler('logs/k8s_mcp.log', maxBytes=10485760, backupCount=5)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Create directories for Kubernetes documentation
os.makedirs('static/docs', exist_ok=True)
os.makedirs('static/api', exist_ok=True)
os.makedirs('static/templates', exist_ok=True)

# URLs for Kubernetes documentation
K8S_DOCS_URL = "https://kubernetes.io/docs"
K8S_API_URL = "https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.27/"

# Directory for Kubernetes resource templates
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')

# Define Blueprints for docs and api sections AFTER app initialization but BEFORE routes
docs_bp = Blueprint('docs_bp', __name__,
                    static_folder='static/docs', # Specifies the static folder for this blueprint
                    template_folder='static/docs') # Specifies the template folder

api_bp = Blueprint('api_bp', __name__,
                   static_folder='static/api',   # Specifies the static folder for this blueprint
                   template_folder='static/api')   # Specifies the template folder

# Initialize Kubernetes client (if available)
k8s_enabled = False
k8s_client = None

try:
    # Try to load Kubernetes config from default location
    config.load_kube_config()
    api_client = client.ApiClient()
    
    # Test the connection to the API server
    try:
        v1 = client.CoreV1Api(api_client)
        v1.list_namespace()
        k8s_enabled = True
        logger.info("Successfully connected to Kubernetes API server")
    except Exception as e:
        logger.error(f"Failed to connect to Kubernetes API server: {e}")
        k8s_enabled = False
except Exception as e:
    logger.error(f"Failed to load Kubernetes config: {e}")
    k8s_enabled = False

# Create a simple K8S client wrapper if connected
if k8s_enabled:
    class K8sClient:
        def __init__(self, api_client):
            self.core_v1 = client.CoreV1Api(api_client)
            self.apps_v1 = client.AppsV1Api(api_client)
            self.batch_v1 = client.BatchV1Api(api_client)
        
        def list_namespaces(self):
            namespaces = []
            try:
                response = self.core_v1.list_namespace()
                for ns in response.items:
                    namespaces.append({
                        "name": ns.metadata.name,
                        "status": ns.status.phase,
                        "creation_time": ns.metadata.creation_timestamp.isoformat() if ns.metadata.creation_timestamp else None
                    })
                return namespaces
            except ApiException as e:
                logger.error(f"Exception when calling list_namespace: {e}")
                return {"error": str(e)}
        
        def list_pods(self, namespace="default"):
            pods = []
            try:
                response = self.core_v1.list_namespaced_pod(namespace)
                for pod in response.items:
                    pods.append({
                        "name": pod.metadata.name,
                        "namespace": pod.metadata.namespace,
                        "status": pod.status.phase,
                        "ip": pod.status.pod_ip,
                        "node": pod.spec.node_name
                    })
                return pods
            except ApiException as e:
                logger.error(f"Exception when calling list_namespaced_pod: {e}")
                return {"error": str(e)}
        
        def get_pod(self, name, namespace="default"):
            try:
                response = self.core_v1.read_namespaced_pod(name, namespace)
                return {
                    "name": response.metadata.name,
                    "namespace": response.metadata.namespace,
                    "status": response.status.phase,
                    "ip": response.status.pod_ip,
                    "node": response.spec.node_name,
                    "containers": [c.name for c in response.spec.containers],
                    "creation_time": response.metadata.creation_timestamp.isoformat() if response.metadata.creation_timestamp else None
                }
            except ApiException as e:
                logger.error(f"Exception when calling read_namespaced_pod: {e}")
                return {"error": str(e)}
    
    # Initialize our K8S client wrapper
    k8s_client = K8sClient(api_client)

# MCP Server event streaming
class MCPEventStream:
    """Manages event streaming for SSE connections."""
    
    def __init__(self):
        """Initialize the event stream manager."""
        self.listeners = []
        self.lock = threading.Lock()
    
    def add_listener(self, listener):
        """Add a new listener for events."""
        with self.lock:
            self.listeners.append(listener)
    
    def remove_listener(self, listener):
        """Remove a listener."""
        with self.lock:
            if listener in self.listeners:
                self.listeners.remove(listener)
    
    def broadcast_event(self, event_type, data):
        """Broadcast an event to all listeners."""
        event = {
            "type": event_type,
            "data": data,
            "timestamp": time.time()
        }
        with self.lock:
            for listener in self.listeners:
                listener.put(event)

# Initialize event stream
event_stream = MCPEventStream()

def fetch_k8s_docs() -> None:
    """
    Fetch Kubernetes documentation from the official website.
    """
    try:
        # Fetch main documentation index
        response = requests.get(f"{K8S_DOCS_URL}/home/")
        if response.status_code == 200:
            with open('static/docs/index.html', 'w') as f:
                f.write(response.text)
            logger.info("Downloaded K8s documentation index")
            
        # Fetch API reference
        api_response = requests.get(K8S_API_URL)
        if api_response.status_code == 200:
            with open('static/api/index.html', 'w') as f:
                f.write(api_response.text)
            logger.info("Downloaded K8s API reference")
                
    except Exception as e:
        logger.error(f"Error fetching K8s docs: {str(e)}")

# SSE endpoint for Cursor IDE integration
@app.route('/events')
def sse_events():
    """
    Server-Sent Events endpoint for Cursor IDE.
    """
    def generate_events():
        # Create a queue for this client
        q = Queue()
        
        # Register with event manager
        event_stream.add_listener(q)
        
        try:
            # Send a welcome event
            welcome_data = {
                "type": "connected", 
                "data": {
                    "server": "Kubernetes MCP Server",
                    "k8s_enabled": k8s_enabled
                }
            }
            yield f"data: {json.dumps(welcome_data)}\n\n"
            
            # Keep connection alive until client disconnects
            while True:
                # Send keepalive every 30 seconds if no events
                try:
                    event = q.get(timeout=30)
                    yield f"data: {json.dumps(event)}\n\n"
                except:
                    # Send keepalive
                    yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
        finally:
            # Cleanup when client disconnects
            event_stream.remove_listener(q)
    
    # Set up the SSE response with proper headers
    return Response(
        generate_events(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'  # Disable proxy buffering
        }
    )

@app.route('/mcp', methods=['POST'])
def mcp_request():
    """
    Handle MCP protocol requests from Cursor IDE.
    """
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.json
    request_type = data.get('type', '')
    request_id = data.get('id', 'unknown')
    
    # Log incoming request for debugging
    logger.debug(f"Received MCP request: {request_type} (ID: {request_id})")
    
    if request_type == 'ping':
        return jsonify({
            "type": "pong",
            "id": request_id,
            "data": {
                "status": "ok",
                "server": "Kubernetes MCP Server",
                "version": "1.0.0"
            }
        })
    
    elif request_type == 'initialize':
        # Cursor sends this when first connecting
        return jsonify({
            "type": "initialized",
            "id": request_id,
            "data": {
                "server_info": {
                    "name": "Kubernetes MCP Server",
                    "version": "1.0.0",
                    "capabilities": {
                        "kubernetes": k8s_enabled,
                        "documentation": True,
                        "templates": True
                    }
                }
            }
        })
    
    elif request_type == 'shutdown':
        # Cursor is disconnecting
        return jsonify({
            "type": "shutdown_result",
            "id": request_id,
            "data": {"success": True}
        })
    
    elif request_type == 'k8s_query':
        if not k8s_enabled:
            return jsonify({
                "type": "error",
                "id": request_id,
                "data": {
                    "message": "Kubernetes integration is not enabled"
                }
            }), 503
        
        query = data.get('data', {})
        action = query.get('action', '')
        
        result = {"status": "error", "message": "Unknown action"}
        
        if action == 'list_namespaces':
            result = {
                "status": "success",
                "data": k8s_client.list_namespaces()
            }
        elif action == 'list_pods':
            namespace = query.get('namespace')
            result = {
                "status": "success",
                "data": k8s_client.list_pods(namespace=namespace)
            }
        elif action == 'get_pod':
            name = query.get('name')
            namespace = query.get('namespace')
            if name and namespace:
                result = {
                    "status": "success",
                    "data": k8s_client.get_pod(name=name, namespace=namespace)
                }
            else:
                result = {"status": "error", "message": "Missing name or namespace"}
        
        # Broadcast the event to all listeners
        event_stream.broadcast_event('k8s_update', result)
        
        return jsonify({
            "type": "k8s_result",
            "id": request_id,
            "data": result
        })
    
    elif request_type == 'get_template':
        template_name = data.get('data', {}).get('name')
        format_type = data.get('data', {}).get('format', 'yaml')
        
        if not template_name:
            return jsonify({
                "type": "error",
                "id": request_id,
                "data": {"message": "Template name is required"}
            }), 400
        
        template_content = get_template(template_name, format_type)
        if template_content is None:
            return jsonify({
                "type": "error",
                "id": request_id,
                "data": {
                    "message": f"Template '{template_name}' not found",
                    "available_templates": list_templates()
                }
            }), 404
        
        return jsonify({
            "type": "template_result",
            "id": request_id,
            "data": {
                "name": template_name,
                "format": format_type,
                "content": template_content
            }
        })
    
    elif request_type == 'list_templates':
        return jsonify({
            "type": "templates_list",
            "id": request_id,
            "data": {
                "templates": list_templates()
            }
        })
    
    elif request_type == 'search_docs':
        query = data.get('data', {}).get('query', '')
        if not query:
            return jsonify({
                "type": "error",
                "id": request_id,
                "data": {"message": "Search query is required"}
            }), 400
        
        # Simple search implementation
        results = []
        
        # Search in docs
        if os.path.exists('static/docs/index.html'):
            with open('static/docs/index.html', 'r') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')
                for link in soup.find_all('a'):
                    if query.lower() in link.text.lower():
                        results.append({
                            "title": link.text,
                            "url": link.get('href'),
                            "source": "docs"
                        })
        
        # Search in API reference
        if os.path.exists('static/api/index.html'):
            with open('static/api/index.html', 'r') as f:
                content = f.read()
                soup = BeautifulSoup(content, 'html.parser')
                for link in soup.find_all('a'):
                    if query.lower() in link.text.lower():
                        results.append({
                            "title": link.text,
                            "url": link.get('href'),
                            "source": "api"
                        })
        
        return jsonify({
            "type": "search_results",
            "id": request_id,
            "data": {
                "query": query,
                "results": results
            }
        })
    
    # Default response for unknown request types
    return jsonify({
        "type": "error",
        "id": request_id,
        "data": {
            "message": f"Unknown request type: {request_type}"
        }
    }), 400

@app.route('/')
def index() -> str:
    """
    Main endpoint to check if the server is running.
    """
    return jsonify({
        "status": "running",
        "service": "Kubernetes MCP Server",
        "k8s_enabled": k8s_enabled,
        "endpoints": {
            "docs": "/docs",
            "api": "/api",
            "status": "/status",
            "templates": "/templates",
            "search": "/search?q=<query>",
            "events": "/events",
            "mcp": "/mcp",
            "cluster": "/cluster" if k8s_enabled else None
        }
    })

# Register docs blueprint route for index
@docs_bp.route('/')
def docs_index():
    if not os.path.exists(os.path.join(docs_bp.template_folder, 'index.html')):
        fetch_k8s_docs()
    return send_from_directory(docs_bp.template_folder, 'index.html')

# Add a route within the docs blueprint to serve its static files
@docs_bp.route('/<path:filename>')
def docs_static(filename):
    return send_from_directory(docs_bp.static_folder, filename)

@app.route('/status')
def status() -> str:
    """
    Return server status and information.
    """
    return jsonify({
        "status": "healthy",
        "version": "1.0.0",
        "docs_available": os.path.exists('static/docs/index.html'),
        "api_available": os.path.exists('static/api/index.html'),
        "templates_available": os.path.exists('static/templates'),
        "k8s_enabled": k8s_enabled
    })

@app.route('/search')
def search() -> str:
    """
    Search Kubernetes documentation.
    """
    query = request.args.get('q', '')
    if not query:
        return jsonify({"error": "No search query provided"}), 400
    
    # Simple search implementation
    results = []
    
    # Search in docs
    if os.path.exists('static/docs/index.html'):
        with open('static/docs/index.html', 'r') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            for link in soup.find_all('a'):
                if query.lower() in link.text.lower():
                    results.append({
                        "title": link.text,
                        "url": link.get('href'),
                        "source": "docs"
                    })
    
    # Search in API reference
    if os.path.exists('static/api/index.html'):
        with open('static/api/index.html', 'r') as f:
            content = f.read()
            soup = BeautifulSoup(content, 'html.parser')
            for link in soup.find_all('a'):
                if query.lower() in link.text.lower():
                    results.append({
                        "title": link.text,
                        "url": link.get('href'),
                        "source": "api"
                    })
    
    return jsonify({"query": query, "results": results})

@app.route('/templates')
def templates() -> str:
    """
    List all available Kubernetes resource templates.
    """
    template_list = list_templates()
    return jsonify({
        "templates": template_list,
        "usage": "GET /templates/<template_name>?format=yaml|json"
    })

@app.route('/templates/<template_name>')
def template(template_name: str) -> str:
    """
    Retrieve a specific Kubernetes resource template.
    
    Args:
        template_name: The name of the template to retrieve
    """
    format_type = request.args.get('format', 'yaml')
    if format_type not in ['yaml', 'json']:
        return jsonify({"error": "Invalid format. Use 'yaml' or 'json'"}), 400
    
    template_content = get_template(template_name, format_type)
    
    if template_content is None:
        return jsonify({
            "error": f"Template '{template_name}' not found",
            "available_templates": list_templates()
        }), 404
    
    if format_type == 'json':
        return jsonify(json.loads(template_content))
    else:
        return template_content, 200, {'Content-Type': 'text/yaml'}

# Kubernetes Cluster API endpoints

@app.route('/cluster')
def cluster() -> str:
    """
    Get cluster information.
    """
    if not k8s_enabled:
        return jsonify({"error": "Kubernetes integration is not enabled"}), 503
    
    try:
        current_context = k8s_client.get_current_context()
        return jsonify({
            "status": "connected",
            "current_context": current_context,
            "endpoints": {
                "contexts": "/cluster/contexts",
                "namespaces": "/cluster/namespaces",
                "pods": "/cluster/pods",
                "services": "/cluster/services",
                "deployments": "/cluster/deployments"
            }
        })
    except Exception as e:
        logger.error(f"Error getting cluster info: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/cluster/contexts')
def get_contexts() -> str:
    """
    Get all available Kubernetes contexts.
    """
    if not k8s_enabled:
        return jsonify({"error": "Kubernetes integration is not enabled"}), 503
    
    try:
        contexts = k8s_client.get_contexts()
        current_context = k8s_client.get_current_context()
        return jsonify({
            "current_context": current_context.get("name", ""),
            "contexts": contexts
        })
    except Exception as e:
        logger.error(f"Error getting contexts: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/cluster/namespaces')
def list_namespaces() -> str:
    """
    List all namespaces in the cluster.
    """
    if not k8s_enabled:
        return jsonify({"error": "Kubernetes integration is not enabled"}), 503
    
    try:
        namespaces = k8s_client.list_namespaces()
        return jsonify({
            "namespaces": namespaces
        })
    except Exception as e:
        logger.error(f"Error listing namespaces: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/cluster/pods')
def list_pods() -> str:
    """
    List all pods in the cluster or in a specific namespace.
    """
    if not k8s_enabled:
        return jsonify({"error": "Kubernetes integration is not enabled"}), 503
    
    namespace = request.args.get('namespace')
    
    try:
        pods = k8s_client.list_pods(namespace=namespace)
        return jsonify({
            "namespace": namespace if namespace else "all",
            "pods": pods
        })
    except Exception as e:
        logger.error(f"Error listing pods: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/cluster/pod/<namespace>/<name>')
def get_pod(namespace: str, name: str) -> str:
    """
    Get details of a specific pod.
    
    Args:
        namespace: The namespace of the pod
        name: The name of the pod
    """
    if not k8s_enabled:
        return jsonify({"error": "Kubernetes integration is not enabled"}), 503
    
    try:
        pod = k8s_client.get_pod(name=name, namespace=namespace)
        return jsonify(pod)
    except Exception as e:
        logger.error(f"Error getting pod {name} in namespace {namespace}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/cluster/pod/<namespace>/<name>/logs')
def get_pod_logs(namespace: str, name: str) -> str:
    """
    Get logs from a specific pod.
    
    Args:
        namespace: The namespace of the pod
        name: The name of the pod
    """
    if not k8s_enabled:
        return jsonify({"error": "Kubernetes integration is not enabled"}), 503
    
    container = request.args.get('container')
    tail_lines = request.args.get('tail_lines')
    if tail_lines:
        try:
            tail_lines = int(tail_lines)
        except ValueError:
            return jsonify({"error": "tail_lines must be an integer"}), 400
    
    try:
        logs = k8s_client.get_pod_logs(
            name=name, 
            namespace=namespace, 
            container=container,
            tail_lines=tail_lines
        )
        return jsonify(logs)
    except Exception as e:
        logger.error(f"Error getting logs for pod {name} in namespace {namespace}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/cluster/services')
def list_services() -> str:
    """
    List all services in the cluster or in a specific namespace.
    """
    if not k8s_enabled:
        return jsonify({"error": "Kubernetes integration is not enabled"}), 503
    
    namespace = request.args.get('namespace')
    
    try:
        services = k8s_client.list_services(namespace=namespace)
        return jsonify({
            "namespace": namespace if namespace else "all",
            "services": services
        })
    except Exception as e:
        logger.error(f"Error listing services: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/cluster/deployments')
def list_deployments() -> str:
    """
    List all deployments in the cluster or in a specific namespace.
    """
    if not k8s_enabled:
        return jsonify({"error": "Kubernetes integration is not enabled"}), 503
    
    namespace = request.args.get('namespace')
    
    try:
        deployments = k8s_client.list_deployments(namespace=namespace)
        return jsonify({
            "namespace": namespace if namespace else "all",
            "deployments": deployments
        })
    except Exception as e:
        logger.error(f"Error listing deployments: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/cluster/apply', methods=['POST'])
def apply_yaml() -> str:
    """
    Apply a YAML manifest to the cluster.
    """
    if not k8s_enabled:
        return jsonify({"error": "Kubernetes integration is not enabled"}), 503
    
    if not request.is_json and not request.files:
        return jsonify({"error": "Request must contain a JSON payload or a YAML file"}), 400
    
    namespace = request.args.get('namespace')
    
    try:
        if request.is_json:
            # Handle JSON payload
            payload = request.json
            
            if 'yaml' not in payload:
                return jsonify({"error": "JSON payload must contain a 'yaml' field"}), 400
            
            yaml_content = payload['yaml']
        else:
            # Handle file upload
            if 'file' not in request.files:
                return jsonify({"error": "No file part in the request"}), 400
            
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No selected file"}), 400
            
            yaml_content = file.read().decode('utf-8')
        
        result = k8s_client.apply_yaml(yaml_content=yaml_content, namespace=namespace)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error applying YAML: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/cluster/pod/<namespace>/<name>', methods=['DELETE'])
def delete_pod(namespace: str, name: str) -> str:
    """
    Delete a specific pod.
    
    Args:
        namespace: The namespace of the pod
        name: The name of the pod
    """
    if not k8s_enabled:
        return jsonify({"error": "Kubernetes integration is not enabled"}), 503
    
    try:
        result = k8s_client.delete_pod(name=name, namespace=namespace)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error deleting pod {name} in namespace {namespace}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/cluster/pod/<namespace>/<name>/exec', methods=['POST'])
def exec_command(namespace: str, name: str) -> str:
    """
    Execute a command in a container of a pod.
    
    Args:
        namespace: The namespace of the pod
        name: The name of the pod
    """
    if not k8s_enabled:
        return jsonify({"error": "Kubernetes integration is not enabled"}), 503
    
    if not request.is_json:
        return jsonify({"error": "Request must contain a JSON payload"}), 400
    
    payload = request.json
    container = payload.get('container')
    command = payload.get('command')
    
    if not command:
        return jsonify({"error": "Command is required"}), 400
    
    try:
        result = k8s_client.exec_command(
            name=name,
            namespace=namespace,
            container=container,
            command=command
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error executing command in pod {name} in namespace {namespace}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/cluster/describe/<kind>/<name>')
def describe_resource(kind: str, name: str) -> str:
    """
    Describe a Kubernetes resource.
    
    Args:
        kind: The kind of resource (pod, service, deployment, etc.)
        name: The name of the resource
    """
    if not k8s_enabled:
        return jsonify({"error": "Kubernetes integration is not enabled"}), 503
    
    namespace = request.args.get('namespace')
    
    try:
        result = k8s_client.describe_resource(
            kind=kind,
            name=name,
            namespace=namespace
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error describing {kind} {name}: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/cluster/create/pod', methods=['POST'])
def create_pod() -> str:
    """
    Create a pod in a namespace.
    """
    if not k8s_enabled:
        return jsonify({"error": "Kubernetes integration is not enabled"}), 503
    
    if not request.is_json:
        return jsonify({"error": "Request must contain a JSON payload"}), 400
    
    payload = request.json
    
    if 'namespace' not in payload:
        return jsonify({"error": "Namespace is required"}), 400
    
    if 'pod' not in payload:
        return jsonify({"error": "Pod manifest is required"}), 400
    
    try:
        result = k8s_client.create_pod(
            pod_manifest=payload['pod'],
            namespace=payload['namespace']
        )
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error creating pod: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

# Template handling functions
def list_templates():
    """List all available Kubernetes resource templates."""
    if not os.path.exists(TEMPLATES_DIR):
        os.makedirs(TEMPLATES_DIR)
        # Create a default template
        with open(os.path.join(TEMPLATES_DIR, 'pod.yaml'), 'w') as f:
            f.write("""apiVersion: v1
kind: Pod
metadata:
  name: example-pod
  labels:
    app: example
spec:
  containers:
  - name: nginx
    image: nginx:latest
    ports:
    - containerPort: 80
""")
    
    templates = []
    for filename in os.listdir(TEMPLATES_DIR):
        if filename.endswith('.yaml') or filename.endswith('.json'):
            template_info = {
                "name": os.path.splitext(filename)[0],
                "format": os.path.splitext(filename)[1][1:],  # Remove the dot
                "path": os.path.join(TEMPLATES_DIR, filename)
            }
            templates.append(template_info)
    
    return templates

def get_template(name, format_type='yaml'):
    """
    Get the content of a template by name and format.
    """
    filename = f"{name}.{format_type}"
    file_path = os.path.join(TEMPLATES_DIR, filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return f.read()
    return None

# Register blueprints with the main app AFTER defining their routes
app.register_blueprint(docs_bp, url_prefix='/docs')
app.register_blueprint(api_bp, url_prefix='/api')

if __name__ == '__main__':
    # Initial fetch of documentation
    fetch_k8s_docs()
    
    # Start Flask server
    port = int(os.environ.get('WEBCONTROL_PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True, threaded=True) 