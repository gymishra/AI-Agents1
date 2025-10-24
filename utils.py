"""
SAP Sales Order Agent Workshop - Shared Utilities

Common utilities used across all workshop labs.
"""

import os
import json
import yaml
import boto3
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from botocore.exceptions import ClientError
import pandas as pd


def print_header(title: str, level: int = 1):
    """Print a formatted header for notebook sections."""
    if level == 1:
        print("=" * 60)
        print(f"🚀 {title}")
        print("=" * 60)
    elif level == 2:
        print("-" * 40)
        print(f"📋 {title}")
        print("-" * 40)
    else:
        print(f"• {title}")


def print_success(message: str):
    """Print a success message."""
    print(f"✅ {message}")


def print_error(message: str):
    """Print an error message."""
    print(f"❌ {message}")


def print_info(message: str):
    """Print an info message."""
    print(f"ℹ️  {message}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"⚠️  {message}")


def check_aws_credentials():
    """Check if AWS credentials are configured."""
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print_success(f"AWS credentials configured for account: {identity['Account']}")
        return True
    except Exception as e:
        print_error(f"AWS credentials not configured: {e}")
        print_info("Please run 'aws configure' to set up your credentials")
        return False


def check_bedrock_access():
    """Check if Bedrock access is available."""
    try:
        bedrock = boto3.client('bedrock', region_name='us-east-1')
        models = bedrock.list_foundation_models()
        
        # Check for required models
        required_models = [
            'anthropic.claude-3-5-sonnet-20241022-v2:0',
            'anthropic.claude-3-5-haiku-20241022-v1:0'
        ]
        
        available_models = [model['modelId'] for model in models['modelSummaries']]
        
        for model in required_models:
            if model in available_models:
                print_success(f"Model available: {model}")
            else:
                print_warning(f"Model not available: {model}")
        
        return True
    except Exception as e:
        print_error(f"Bedrock access check failed: {e}")
        return False


def get_ssm_parameter(parameter_name: str, default: Optional[str] = None) -> str:
    """Get parameter from AWS Systems Manager Parameter Store."""
    try:
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(Name=parameter_name, WithDecryption=True)
        return response['Parameter']['Value']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ParameterNotFound':
            if default is not None:
                return default
            raise ValueError(f"Parameter {parameter_name} not found")
        else:
            raise ValueError(f"Error retrieving parameter {parameter_name}: {e}")


def put_ssm_parameter(parameter_name: str, parameter_value: str, 
                     parameter_type: str = 'String', overwrite: bool = True) -> bool:
    """Put parameter to AWS Systems Manager Parameter Store."""
    try:
        ssm = boto3.client('ssm')
        ssm.put_parameter(
            Name=parameter_name,
            Value=parameter_value,
            Type=parameter_type,
            Overwrite=overwrite
        )
        return True
    except Exception as e:
        print_error(f"Error putting parameter {parameter_name}: {e}")
        return False


def create_resource_name(base_name: str, prefix: str = "sapagent") -> str:
    """Create standardized resource name."""
    return f"{prefix}-{base_name}"


def wait_for_resource(check_function, resource_name: str, max_wait: int = 300):
    """Wait for a resource to be ready."""
    print_info(f"Waiting for {resource_name} to be ready...")
    
    start_time = time.time()
    while time.time() - start_time < max_wait:
        if check_function():
            print_success(f"{resource_name} is ready!")
            return True
        
        print(".", end="", flush=True)
        time.sleep(10)
    
    print_error(f"{resource_name} not ready after {max_wait} seconds")
    return False


def format_json(data: Dict[str, Any]) -> str:
    """Format JSON data for display."""
    return json.dumps(data, indent=2, default=str)


def format_table(data: List[Dict[str, Any]]) -> pd.DataFrame:
    """Format data as a pandas DataFrame for display."""
    return pd.DataFrame(data)


def save_config(config_data: Dict[str, Any], filename: str = "workshop_config.yaml"):
    """Save configuration data to a YAML file."""
    try:
        with open(filename, 'w') as f:
            yaml.dump(config_data, f, default_flow_style=False)
        print_success(f"Configuration saved to {filename}")
        return True
    except Exception as e:
        print_error(f"Error saving configuration: {e}")
        return False


def load_config(filename: str = "workshop_config.yaml") -> Dict[str, Any]:
    """Load configuration data from a YAML file."""
    try:
        with open(filename, 'r') as f:
            config = yaml.safe_load(f)
        print_success(f"Configuration loaded from {filename}")
        return config
    except FileNotFoundError:
        print_warning(f"Configuration file {filename} not found")
        return {}
    except Exception as e:
        print_error(f"Error loading configuration: {e}")
        return {}


def validate_email(email: str) -> bool:
    """Validate email address format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def format_currency(amount: float, currency: str = "USD") -> str:
    """Format currency amount."""
    if currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."


def get_timestamp() -> str:
    """Get current timestamp as string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def create_mock_order_data() -> List[Dict[str, Any]]:
    """Create mock SAP order data for workshop demonstrations."""
    return [
        {
            "order_id": "SO001234",
            "customer_number": "CUST001",
            "customer_name": "ACME Corporation",
            "order_date": "2024-01-10",
            "order_value": 15000.00,
            "currency": "USD",
            "status": "In Process",
            "has_delivery_block": True,
            "delivery_block": {
                "reason": "Credit limit exceeded",
                "blocked_date": "2024-01-15",
                "blocked_by": "System (Credit Check)"
            },
            "requested_delivery_date": "2024-01-25",
            "material_description": "Industrial Equipment Package A"
        },
        {
            "order_id": "SO001235",
            "customer_number": "CUST002",
            "customer_name": "TechCorp Ltd",
            "order_date": "2024-01-12",
            "order_value": 8500.00,
            "currency": "USD",
            "status": "In Process",
            "has_delivery_block": True,
            "delivery_block": {
                "reason": "Incomplete documentation",
                "blocked_date": "2024-01-16",
                "blocked_by": "Sales Team"
            },
            "requested_delivery_date": "2024-01-28",
            "material_description": "Software License Bundle"
        },
        {
            "order_id": "SO001236",
            "customer_number": "CUST003",
            "customer_name": "Global Manufacturing Inc",
            "order_date": "2024-01-14",
            "order_value": 25000.00,
            "currency": "USD",
            "status": "Released",
            "has_delivery_block": False,
            "delivery_block": None,
            "requested_delivery_date": "2024-02-01",
            "material_description": "Manufacturing Equipment Set"
        }
    ]


def display_architecture_progress(current_lab: int):
    """Display the current architecture progress."""
    architectures = {
        1: """
Lab 1: Basic Agent
┌─────────────────┐
│   SAP Agent     │
│   (Mock Data)   │
└─────────────────┘
        """,
        2: """
Lab 2: Agent + Memory
┌─────────────────┐    ┌─────────────────┐
│   SAP Agent     │───▶│ AgentCore       │
│                 │    │ Memory          │
└─────────────────┘    └─────────────────┘
        """,
        3: """
Lab 3: Agent + Gateway + Memory
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   SAP Agent     │───▶│ AgentCore       │───▶│ SAP Systems     │
│                 │    │ Gateway         │    │ Email/KB        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│ AgentCore       │
│ Memory          │
└─────────────────┘
        """,
        4: """
Lab 4: Production Runtime
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Users         │───▶│ AgentCore       │───▶│ SAP Agent       │
│                 │    │ Runtime         │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Gateway+Memory  │
                       │ + Observability │
                       └─────────────────┘
        """
    }
    
    print_header(f"Current Architecture - Lab {current_lab}", level=2)
    print(architectures.get(current_lab, "Architecture diagram not available"))


class WorkshopProgress:
    """Track workshop progress across labs."""
    
    def __init__(self):
        self.config_file = "workshop_progress.yaml"
        self.progress = self.load_progress()
    
    def load_progress(self) -> Dict[str, Any]:
        """Load progress from file."""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except FileNotFoundError:
            return {}
    
    def save_progress(self):
        """Save progress to file."""
        with open(self.config_file, 'w') as f:
            yaml.dump(self.progress, f, default_flow_style=False)
    
    def mark_lab_complete(self, lab_number: int, resources: Dict[str, str] = None):
        """Mark a lab as complete."""
        self.progress[f"lab_{lab_number}"] = {
            "completed": True,
            "timestamp": get_timestamp(),
            "resources": resources or {}
        }
        self.save_progress()
        print_success(f"Lab {lab_number} marked as complete!")
    
    def get_lab_resources(self, lab_number: int) -> Dict[str, str]:
        """Get resources created in a specific lab."""
        return self.progress.get(f"lab_{lab_number}", {}).get("resources", {})
    
    def is_lab_complete(self, lab_number: int) -> bool:
        """Check if a lab is complete."""
        return self.progress.get(f"lab_{lab_number}", {}).get("completed", False)
    
    def display_progress(self):
        """Display overall workshop progress."""
        print_header("Workshop Progress", level=2)
        
        labs = [
            "Create SAP Agent",
            "Add Memory",
            "SAP Gateway Integration", 
            "Production Runtime",
            "User Interfaces",
            "Observability"
        ]
        
        for i, lab_name in enumerate(labs, 1):
            status = "✅" if self.is_lab_complete(i) else "⏳"
            print(f"{status} Lab {i}: {lab_name}")


# Global progress tracker
workshop_progress = WorkshopProgress()