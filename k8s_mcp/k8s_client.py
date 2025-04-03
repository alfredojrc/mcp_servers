"""
Kubernetes client module.

This module provides functions to interact with a Kubernetes cluster.
"""
import os
import logging
import json
import yaml
import base64
from typing import Dict, List, Optional, Union, Any
from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException

# Setup logging
logger = logging.getLogger(__name__)

class K8sClient:
    """
    Kubernetes client for interacting with a Kubernetes cluster.
    """
    
    def __init__(self, config_file: Optional[str] = None) -> None:
        """
        Initialize the Kubernetes client.
        
        Args:
            config_file: Path to kubeconfig file. If None, uses default.
        """
        self.config_file = config_file
        self._load_config()
        self.core_v1 = client.CoreV1Api()
        self.apps_v1 = client.AppsV1Api()
        self.batch_v1 = client.BatchV1Api()
        self.networking_v1 = client.NetworkingV1Api()
        self.custom_objects = client.CustomObjectsApi()
        
    def _load_config(self) -> None:
        """
        Load Kubernetes configuration.
        """
        try:
            if self.config_file and os.path.exists(self.config_file):
                config.load_kube_config(config_file=self.config_file)
            else:
                # Try in-cluster config first (for running inside a pod)
                try:
                    config.load_incluster_config()
                    logger.info("Using in-cluster configuration")
                except config.config_exception.ConfigException:
                    # Fall back to default kubeconfig
                    config.load_kube_config()
                    logger.info("Using default kubeconfig")
        except Exception as e:
            logger.error(f"Error loading Kubernetes config: {str(e)}")
            raise

    def get_config(self) -> Dict[str, Any]:
        """
        Get the current Kubernetes configuration.
        
        Returns:
            The current Kubernetes configuration as a dict
        """
        if self.config_file and os.path.exists(self.config_file):
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Get from default location
            kube_config_path = os.path.expanduser('~/.kube/config')
            if os.path.exists(kube_config_path):
                with open(kube_config_path, 'r') as f:
                    return yaml.safe_load(f)
        return {"error": "No kubeconfig found"}

    def get_contexts(self) -> List[Dict[str, Any]]:
        """
        Get all available contexts from the Kubernetes configuration.
        
        Returns:
            List of contexts
        """
        kube_config = self.get_config()
        if "contexts" in kube_config:
            return kube_config["contexts"]
        return []

    def get_current_context(self) -> Dict[str, Any]:
        """
        Get the current context.
        
        Returns:
            Current context
        """
        kube_config = self.get_config()
        if "current-context" in kube_config:
            current_context = kube_config["current-context"]
            for context in kube_config.get("contexts", []):
                if context["name"] == current_context:
                    return context
        return {"error": "No current context found"}

    def list_namespaces(self) -> List[Dict[str, Any]]:
        """
        List all namespaces in the cluster.
        
        Returns:
            List of namespaces
        """
        try:
            namespaces = self.core_v1.list_namespace()
            return [
                {
                    "name": ns.metadata.name,
                    "status": ns.status.phase,
                    "created": ns.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") 
                    if ns.metadata.creation_timestamp else None
                }
                for ns in namespaces.items
            ]
        except ApiException as e:
            logger.error(f"Error listing namespaces: {str(e)}")
            return [{"error": f"Error listing namespaces: {str(e)}"}]

    def list_pods(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all pods in the specified namespace or all namespaces.
        
        Args:
            namespace: The namespace to list pods from. If None, list from all namespaces.
            
        Returns:
            List of pods
        """
        try:
            if namespace:
                pods = self.core_v1.list_namespaced_pod(namespace=namespace)
            else:
                pods = self.core_v1.list_pod_for_all_namespaces()
            
            return [
                {
                    "name": pod.metadata.name,
                    "namespace": pod.metadata.namespace,
                    "status": pod.status.phase,
                    "ip": pod.status.pod_ip,
                    "node": pod.spec.node_name,
                    "created": pod.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") 
                    if pod.metadata.creation_timestamp else None
                }
                for pod in pods.items
            ]
        except ApiException as e:
            logger.error(f"Error listing pods: {str(e)}")
            return [{"error": f"Error listing pods: {str(e)}"}]

    def get_pod(self, name: str, namespace: str) -> Dict[str, Any]:
        """
        Get a pod by name from the specified namespace.
        
        Args:
            name: The name of the pod
            namespace: The namespace of the pod
            
        Returns:
            Pod details
        """
        try:
            pod = self.core_v1.read_namespaced_pod(name=name, namespace=namespace)
            containers = []
            
            for container in pod.spec.containers:
                containers.append({
                    "name": container.name,
                    "image": container.image,
                    "resources": {
                        "requests": container.resources.requests if container.resources and container.resources.requests else {},
                        "limits": container.resources.limits if container.resources and container.resources.limits else {}
                    }
                })
            
            return {
                "name": pod.metadata.name,
                "namespace": pod.metadata.namespace,
                "status": pod.status.phase,
                "ip": pod.status.pod_ip,
                "node": pod.spec.node_name,
                "containers": containers,
                "created": pod.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") 
                if pod.metadata.creation_timestamp else None
            }
        except ApiException as e:
            logger.error(f"Error getting pod {name} in namespace {namespace}: {str(e)}")
            return {"error": f"Error getting pod: {str(e)}"}

    def create_pod(self, pod_manifest: Dict[str, Any], namespace: str) -> Dict[str, Any]:
        """
        Create a pod in the specified namespace.
        
        Args:
            pod_manifest: The pod manifest
            namespace: The namespace to create the pod in
            
        Returns:
            Created pod details
        """
        try:
            api_response = self.core_v1.create_namespaced_pod(
                namespace=namespace,
                body=pod_manifest
            )
            return {
                "name": api_response.metadata.name,
                "namespace": api_response.metadata.namespace,
                "status": "Created",
                "message": f"Pod {api_response.metadata.name} created in namespace {api_response.metadata.namespace}"
            }
        except ApiException as e:
            logger.error(f"Error creating pod in namespace {namespace}: {str(e)}")
            return {"error": f"Error creating pod: {str(e)}"}

    def delete_pod(self, name: str, namespace: str) -> Dict[str, Any]:
        """
        Delete a pod by name from the specified namespace.
        
        Args:
            name: The name of the pod
            namespace: The namespace of the pod
            
        Returns:
            Deletion status
        """
        try:
            api_response = self.core_v1.delete_namespaced_pod(
                name=name,
                namespace=namespace,
                body=client.V1DeleteOptions()
            )
            return {
                "status": "Deleted",
                "message": f"Pod {name} deleted from namespace {namespace}"
            }
        except ApiException as e:
            logger.error(f"Error deleting pod {name} in namespace {namespace}: {str(e)}")
            return {"error": f"Error deleting pod: {str(e)}"}

    def get_pod_logs(self, name: str, namespace: str, container: Optional[str] = None,
                   tail_lines: Optional[int] = None) -> Dict[str, Any]:
        """
        Get logs from a pod by name from the specified namespace.
        
        Args:
            name: The name of the pod
            namespace: The namespace of the pod
            container: The container name (if pod has multiple containers)
            tail_lines: Number of lines from the end of the logs to show
            
        Returns:
            Pod logs
        """
        try:
            api_response = self.core_v1.read_namespaced_pod_log(
                name=name,
                namespace=namespace,
                container=container,
                tail_lines=tail_lines
            )
            return {
                "pod": name,
                "namespace": namespace,
                "container": container,
                "logs": api_response
            }
        except ApiException as e:
            logger.error(f"Error getting logs for pod {name} in namespace {namespace}: {str(e)}")
            return {"error": f"Error getting pod logs: {str(e)}"}

    def list_services(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all services in the specified namespace or all namespaces.
        
        Args:
            namespace: The namespace to list services from. If None, list from all namespaces.
            
        Returns:
            List of services
        """
        try:
            if namespace:
                services = self.core_v1.list_namespaced_service(namespace=namespace)
            else:
                services = self.core_v1.list_service_for_all_namespaces()
            
            return [
                {
                    "name": svc.metadata.name,
                    "namespace": svc.metadata.namespace,
                    "type": svc.spec.type,
                    "cluster_ip": svc.spec.cluster_ip,
                    "ports": [
                        {
                            "name": port.name,
                            "port": port.port,
                            "target_port": port.target_port,
                            "protocol": port.protocol
                        }
                        for port in svc.spec.ports
                    ] if svc.spec.ports else [],
                    "created": svc.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") 
                    if svc.metadata.creation_timestamp else None
                }
                for svc in services.items
            ]
        except ApiException as e:
            logger.error(f"Error listing services: {str(e)}")
            return [{"error": f"Error listing services: {str(e)}"}]

    def list_deployments(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List all deployments in the specified namespace or all namespaces.
        
        Args:
            namespace: The namespace to list deployments from. If None, list from all namespaces.
            
        Returns:
            List of deployments
        """
        try:
            if namespace:
                deployments = self.apps_v1.list_namespaced_deployment(namespace=namespace)
            else:
                deployments = self.apps_v1.list_deployment_for_all_namespaces()
            
            return [
                {
                    "name": deploy.metadata.name,
                    "namespace": deploy.metadata.namespace,
                    "replicas": deploy.spec.replicas,
                    "available_replicas": deploy.status.available_replicas,
                    "ready_replicas": deploy.status.ready_replicas,
                    "created": deploy.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") 
                    if deploy.metadata.creation_timestamp else None
                }
                for deploy in deployments.items
            ]
        except ApiException as e:
            logger.error(f"Error listing deployments: {str(e)}")
            return [{"error": f"Error listing deployments: {str(e)}"}]

    def apply_yaml(self, yaml_content: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Apply a YAML manifest to the cluster.
        
        Args:
            yaml_content: The YAML manifest content
            namespace: The namespace to apply the manifest to (if not specified in the manifest)
            
        Returns:
            Application status
        """
        try:
            # Load the YAML manifest
            resources = list(yaml.safe_load_all(yaml_content))
            results = []
            
            for resource in resources:
                # Skip empty documents
                if not resource:
                    continue
                
                kind = resource.get("kind", "")
                name = resource.get("metadata", {}).get("name", "unknown")
                resource_namespace = resource.get("metadata", {}).get("namespace", namespace)
                
                # Create the appropriate API object based on the resource kind
                if kind.lower() == "namespace":
                    api_response = self.core_v1.create_namespace(body=resource)
                    results.append({
                        "kind": kind,
                        "name": name,
                        "status": "Created",
                        "message": f"Namespace {name} created"
                    })
                
                elif kind.lower() == "pod":
                    if not resource_namespace:
                        results.append({
                            "kind": kind,
                            "name": name,
                            "status": "Error",
                            "message": "Namespace is required for Pod resources"
                        })
                        continue
                    
                    api_response = self.core_v1.create_namespaced_pod(
                        namespace=resource_namespace,
                        body=resource
                    )
                    results.append({
                        "kind": kind,
                        "name": name,
                        "namespace": resource_namespace,
                        "status": "Created",
                        "message": f"Pod {name} created in namespace {resource_namespace}"
                    })
                
                elif kind.lower() == "service":
                    if not resource_namespace:
                        results.append({
                            "kind": kind,
                            "name": name,
                            "status": "Error",
                            "message": "Namespace is required for Service resources"
                        })
                        continue
                    
                    api_response = self.core_v1.create_namespaced_service(
                        namespace=resource_namespace,
                        body=resource
                    )
                    results.append({
                        "kind": kind,
                        "name": name,
                        "namespace": resource_namespace,
                        "status": "Created",
                        "message": f"Service {name} created in namespace {resource_namespace}"
                    })
                
                elif kind.lower() == "deployment":
                    if not resource_namespace:
                        results.append({
                            "kind": kind,
                            "name": name,
                            "status": "Error",
                            "message": "Namespace is required for Deployment resources"
                        })
                        continue
                    
                    api_response = self.apps_v1.create_namespaced_deployment(
                        namespace=resource_namespace,
                        body=resource
                    )
                    results.append({
                        "kind": kind,
                        "name": name,
                        "namespace": resource_namespace,
                        "status": "Created",
                        "message": f"Deployment {name} created in namespace {resource_namespace}"
                    })
                
                elif kind.lower() == "configmap":
                    if not resource_namespace:
                        results.append({
                            "kind": kind,
                            "name": name,
                            "status": "Error",
                            "message": "Namespace is required for ConfigMap resources"
                        })
                        continue
                    
                    api_response = self.core_v1.create_namespaced_config_map(
                        namespace=resource_namespace,
                        body=resource
                    )
                    results.append({
                        "kind": kind,
                        "name": name,
                        "namespace": resource_namespace,
                        "status": "Created",
                        "message": f"ConfigMap {name} created in namespace {resource_namespace}"
                    })
                
                elif kind.lower() == "secret":
                    if not resource_namespace:
                        results.append({
                            "kind": kind,
                            "name": name,
                            "status": "Error",
                            "message": "Namespace is required for Secret resources"
                        })
                        continue
                    
                    api_response = self.core_v1.create_namespaced_secret(
                        namespace=resource_namespace,
                        body=resource
                    )
                    results.append({
                        "kind": kind,
                        "name": name,
                        "namespace": resource_namespace,
                        "status": "Created",
                        "message": f"Secret {name} created in namespace {resource_namespace}"
                    })
                
                else:
                    results.append({
                        "kind": kind,
                        "name": name,
                        "status": "Error",
                        "message": f"Unsupported resource kind: {kind}"
                    })
            
            return {"results": results}
        
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML: {str(e)}")
            return {"error": f"Error parsing YAML: {str(e)}"}
        
        except ApiException as e:
            logger.error(f"Error applying YAML: {str(e)}")
            return {"error": f"Error applying YAML: {str(e)}"}

    def exec_command(self, name: str, namespace: str, container: Optional[str] = None, 
                   command: List[str] = None) -> Dict[str, Any]:
        """
        Execute a command in a container of a pod.
        
        Args:
            name: The name of the pod
            namespace: The namespace of the pod
            container: The container name (if pod has multiple containers)
            command: The command to execute
            
        Returns:
            Command execution results
        """
        try:
            if not command:
                command = ['/bin/sh', '-c', 'echo "Hello from the container!"']
                
            api_response = client.CoreV1Api().connect_get_namespaced_pod_exec(
                name=name,
                namespace=namespace,
                container=container,
                command=command,
                stderr=True,
                stdin=False,
                stdout=True,
                tty=False
            )
            
            return {
                "pod": name,
                "namespace": namespace,
                "container": container,
                "command": command,
                "result": api_response
            }
        except ApiException as e:
            logger.error(f"Error executing command in pod {name} in namespace {namespace}: {str(e)}")
            return {"error": f"Error executing command: {str(e)}"}

    def port_forward(self, name: str, namespace: str, local_port: int, remote_port: int) -> Dict[str, Any]:
        """
        Set up port forwarding to a pod.
        
        Note: This method is not truly implementing port forwarding as that requires
        a persistent process. It returns instructions on how to perform port forwarding
        using kubectl.
        
        Args:
            name: The name of the pod
            namespace: The namespace of the pod
            local_port: The local port to forward from
            remote_port: The remote port to forward to
            
        Returns:
            Port forwarding instructions
        """
        return {
            "status": "Instructions",
            "message": "Port forwarding requires a persistent process. Use kubectl instead.",
            "kubectl_command": f"kubectl port-forward -n {namespace} {name} {local_port}:{remote_port}"
        }

    def describe_resource(self, kind: str, name: str, namespace: Optional[str] = None) -> Dict[str, Any]:
        """
        Describe a Kubernetes resource.
        
        Args:
            kind: The kind of resource (pod, service, deployment, etc.)
            name: The name of the resource
            namespace: The namespace of the resource (required for namespaced resources)
            
        Returns:
            Resource description
        """
        try:
            if kind.lower() == "namespace":
                resource = self.core_v1.read_namespace(name=name)
                return {
                    "kind": "Namespace",
                    "name": resource.metadata.name,
                    "status": resource.status.phase,
                    "created": resource.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") 
                    if resource.metadata.creation_timestamp else None,
                    "labels": resource.metadata.labels,
                    "annotations": resource.metadata.annotations
                }
            
            elif kind.lower() == "pod":
                if not namespace:
                    return {"error": "Namespace is required for Pod resources"}
                
                resource = self.core_v1.read_namespaced_pod(name=name, namespace=namespace)
                return {
                    "kind": "Pod",
                    "name": resource.metadata.name,
                    "namespace": resource.metadata.namespace,
                    "status": resource.status.phase,
                    "ip": resource.status.pod_ip,
                    "node": resource.spec.node_name,
                    "containers": [
                        {
                            "name": container.name,
                            "image": container.image,
                            "ports": [
                                {
                                    "container_port": port.container_port,
                                    "protocol": port.protocol
                                }
                                for port in container.ports
                            ] if container.ports else []
                        }
                        for container in resource.spec.containers
                    ],
                    "created": resource.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") 
                    if resource.metadata.creation_timestamp else None,
                    "labels": resource.metadata.labels,
                    "annotations": resource.metadata.annotations
                }
            
            elif kind.lower() == "service":
                if not namespace:
                    return {"error": "Namespace is required for Service resources"}
                
                resource = self.core_v1.read_namespaced_service(name=name, namespace=namespace)
                return {
                    "kind": "Service",
                    "name": resource.metadata.name,
                    "namespace": resource.metadata.namespace,
                    "type": resource.spec.type,
                    "cluster_ip": resource.spec.cluster_ip,
                    "ports": [
                        {
                            "name": port.name,
                            "port": port.port,
                            "target_port": port.target_port,
                            "protocol": port.protocol
                        }
                        for port in resource.spec.ports
                    ] if resource.spec.ports else [],
                    "selector": resource.spec.selector,
                    "created": resource.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") 
                    if resource.metadata.creation_timestamp else None,
                    "labels": resource.metadata.labels,
                    "annotations": resource.metadata.annotations
                }
            
            elif kind.lower() == "deployment":
                if not namespace:
                    return {"error": "Namespace is required for Deployment resources"}
                
                resource = self.apps_v1.read_namespaced_deployment(name=name, namespace=namespace)
                return {
                    "kind": "Deployment",
                    "name": resource.metadata.name,
                    "namespace": resource.metadata.namespace,
                    "replicas": resource.spec.replicas,
                    "strategy": resource.spec.strategy.type,
                    "selector": resource.spec.selector.match_labels,
                    "containers": [
                        {
                            "name": container.name,
                            "image": container.image
                        }
                        for container in resource.spec.template.spec.containers
                    ],
                    "status": {
                        "available_replicas": resource.status.available_replicas,
                        "ready_replicas": resource.status.ready_replicas,
                        "updated_replicas": resource.status.updated_replicas
                    },
                    "created": resource.metadata.creation_timestamp.strftime("%Y-%m-%d %H:%M:%S") 
                    if resource.metadata.creation_timestamp else None,
                    "labels": resource.metadata.labels,
                    "annotations": resource.metadata.annotations
                }
            
            else:
                return {"error": f"Unsupported resource kind: {kind}"}
                
        except ApiException as e:
            logger.error(f"Error describing {kind} {name}: {str(e)}")
            return {"error": f"Error describing resource: {str(e)}"}

# Initialize the Kubernetes client
def get_k8s_client(config_file: Optional[str] = None) -> K8sClient:
    """
    Get a Kubernetes client instance.
    
    Args:
        config_file: Path to kubeconfig file. If None, uses default.
        
    Returns:
        K8sClient instance
    """
    return K8sClient(config_file=config_file) 