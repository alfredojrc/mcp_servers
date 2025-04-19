"""
Kubernetes resource templates module.

This module provides templates for common Kubernetes resources.
"""
import os
import yaml
import json

# Ensure templates directory exists
os.makedirs('static/templates', exist_ok=True)

# Dictionary of Kubernetes resource templates
TEMPLATES = {
    "deployment": {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": "example-deployment",
            "labels": {
                "app": "example"
            }
        },
        "spec": {
            "replicas": 3,
            "selector": {
                "matchLabels": {
                    "app": "example"
                }
            },
            "template": {
                "metadata": {
                    "labels": {
                        "app": "example"
                    }
                },
                "spec": {
                    "containers": [
                        {
                            "name": "example-container",
                            "image": "nginx:latest",
                            "ports": [
                                {
                                    "containerPort": 80
                                }
                            ],
                            "resources": {
                                "limits": {
                                    "cpu": "100m",
                                    "memory": "128Mi"
                                },
                                "requests": {
                                    "cpu": "50m",
                                    "memory": "64Mi"
                                }
                            }
                        }
                    ]
                }
            }
        }
    },
    "service": {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": "example-service"
        },
        "spec": {
            "selector": {
                "app": "example"
            },
            "ports": [
                {
                    "port": 80,
                    "targetPort": 80
                }
            ]
        }
    },
    "configmap": {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": "example-configmap"
        },
        "data": {
            "config.json": json.dumps({"key": "value"}),
            "app.properties": "property=value\nanother.property=value2"
        }
    },
    "secret": {
        "apiVersion": "v1",
        "kind": "Secret",
        "metadata": {
            "name": "example-secret"
        },
        "type": "Opaque",
        "data": {
            "username": "YWRtaW4=",  # base64 encoded "admin"
            "password": "cGFzc3dvcmQxMjM="  # base64 encoded "password123"
        }
    },
    "ingress": {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": "example-ingress",
            "annotations": {
                "nginx.ingress.kubernetes.io/rewrite-target": "/"
            }
        },
        "spec": {
            "rules": [
                {
                    "host": "example.com",
                    "http": {
                        "paths": [
                            {
                                "path": "/",
                                "pathType": "Prefix",
                                "backend": {
                                    "service": {
                                        "name": "example-service",
                                        "port": {
                                            "number": 80
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        }
    },
    "persistentvolumeclaim": {
        "apiVersion": "v1",
        "kind": "PersistentVolumeClaim",
        "metadata": {
            "name": "example-pvc"
        },
        "spec": {
            "accessModes": ["ReadWriteOnce"],
            "resources": {
                "requests": {
                    "storage": "1Gi"
                }
            }
        }
    }
}

def save_templates() -> None:
    """
    Save all templates to static/templates directory.
    """
    for name, template in TEMPLATES.items():
        # Save as YAML
        with open(f'static/templates/{name}.yaml', 'w') as f:
            yaml.dump(template, f, default_flow_style=False)
        
        # Save as JSON
        with open(f'static/templates/{name}.json', 'w') as f:
            json.dump(template, f, indent=2)

def get_template(name: str, format: str = 'yaml') -> str:
    """
    Get a template by name and format.
    
    Args:
        name: The name of the template
        format: The format to return (yaml or json)
    
    Returns:
        The template as a string in the requested format
    """
    if name not in TEMPLATES:
        return None
    
    template = TEMPLATES[name]
    
    if format.lower() == 'json':
        return json.dumps(template, indent=2)
    else:  # default to yaml
        return yaml.dump(template, default_flow_style=False)

def list_templates() -> list:
    """
    List all available templates.
    
    Returns:
        A list of template names
    """
    return list(TEMPLATES.keys())

if __name__ == '__main__':
    # Save templates when run directly
    save_templates() 