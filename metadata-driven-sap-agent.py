#!/usr/bin/env python3
"""
Metadata-Driven SAP Agent with Dynamic Association Discovery
This agent reads SAP OData metadata to dynamically create tools based on actual associations
"""

import json
import urllib3
import xml.etree.ElementTree as ET
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass

# Real Strands imports
from strands import Agent, tool
from strands.models import BedrockModel

# Disable SSL warnings for demo
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass
class SAPConfig:
    base_url: str
    username: str
    password: str
    verify_ssl: bool = False

# SAP Configuration
SAP_CONFIG = SAPConfig(
    base_url="https://beydev.ramadokr.people.aws.dev:8443",
    username="ACCAPI",
    password="aws4sapD"
)

class SAPMetadataParser:
    """Parser for SAP OData metadata to discover entities and associations"""
    
    def __init__(self, sap_service):
        self.sap_service = sap_service
        self.metadata = None
        self.entities = {}
        self.associations = {}
        self.navigation_properties = {}
        
    def fetch_metadata(self) -> bool:
        """Fetch and parse SAP OData metadata in JSON format"""
        try:
            url = f"{self.sap_service.config.base_url}/sap/opu/odata/sap/API_SALES_ORDER_SRV/$metadata"
            
            # Only pass authentication headers for metadata - no Content-Type or Accept
            headers = urllib3.make_headers(basic_auth=f"{self.sap_service.config.username}:{self.sap_service.config.password}")
            
            print("🔍 Fetching SAP metadata in JSON format...")
            response = self.sap_service.http.request('GET', url, headers=headers)
            
            if response.status == 200:
                self.metadata = response.data.decode('utf-8')
                self._parse_xml_metadata()
                print(f"✅ Metadata parsed: {len(self.entities)} entities, {len(self.associations)} associations")
                return True
            else:
                print(f"❌ Failed to fetch metadata: {response.status}")
                print(f"Response: {response.data.decode('utf-8')[:500]}...")
                return False
                
        except Exception as e:
            print(f"❌ Error fetching metadata: {e}")
            return False
    
    def _parse_xml_metadata(self):
        """Parse XML metadata to extract entities and associations"""
        try:
            root = ET.fromstring(self.metadata)
            
            # Define namespaces
            namespaces = {
                'edmx': 'http://schemas.microsoft.com/ado/2007/06/edmx',
                'edm': 'http://schemas.microsoft.com/ado/2008/09/edm'
            }
            
            # Find the schema
            schema = root.find('.//edm:Schema', namespaces)
            if schema is None:
                print("❌ Could not find schema in metadata")
                return
            
            # Parse EntityTypes
            for entity_type in schema.findall('edm:EntityType', namespaces):
                entity_name = entity_type.get('Name')
                self.entities[entity_name] = {
                    'properties': [],
                    'navigation_properties': []
                }
                
                # Get properties
                for prop in entity_type.findall('edm:Property', namespaces):
                    prop_name = prop.get('Name')
                    prop_type = prop.get('Type')
                    self.entities[entity_name]['properties'].append({
                        'name': prop_name,
                        'type': prop_type
                    })
                
                # Get navigation properties
                for nav_prop in entity_type.findall('edm:NavigationProperty', namespaces):
                    nav_name = nav_prop.get('Name')
                    relationship = nav_prop.get('Relationship')
                    to_role = nav_prop.get('ToRole')
                    
                    self.entities[entity_name]['navigation_properties'].append({
                        'name': nav_name,
                        'relationship': relationship,
                        'to_role': to_role
                    })
                    
                    # Store for easy lookup
                    self.navigation_properties[f"{entity_name}.{nav_name}"] = {
                        'from_entity': entity_name,
                        'nav_property': nav_name,
                        'relationship': relationship,
                        'to_role': to_role
                    }
            
            # Parse Associations
            for association in schema.findall('edm:Association', namespaces):
                assoc_name = association.get('Name')
                self.associations[assoc_name] = {'ends': []}
                
                for end in association.findall('edm:End', namespaces):
                    role = end.get('Role')
                    entity_type = end.get('Type')
                    multiplicity = end.get('Multiplicity')
                    
                    self.associations[assoc_name]['ends'].append({
                        'role': role,
                        'entity_type': entity_type,
                        'multiplicity': multiplicity
                    })
            
            print(f"📊 Discovered entities: {list(self.entities.keys())}")
            print(f"🔗 Discovered navigation properties: {len(self.navigation_properties)}")
            
        except Exception as e:
            print(f"❌ Error parsing XML metadata: {e}")
            print(f"Metadata sample: {self.metadata[:1000]}...")
    
    def get_navigation_properties_for_entity(self, entity_name: str) -> List[Dict]:
        """Get all navigation properties for a specific entity"""
        if entity_name in self.entities:
            return self.entities[entity_name]['navigation_properties']
        return []
    
    def get_entity_properties(self, entity_name: str) -> List[Dict]:
        """Get all properties for a specific entity"""
        if entity_name in self.entities:
            return self.entities[entity_name]['properties']
        return []

class WorkingSAPService:
    """Working SAP OData service with metadata support"""
    
    def __init__(self, config: SAPConfig):
        self.config = config
        self.csrf_token = None
        self.cookies = None
        self.http = urllib3.PoolManager(cert_reqs='CERT_NONE')
        print(f"🔧 SAP Service initialized for {config.base_url}")
    
    def get_headers(self, include_csrf=False):
        """Get HTTP headers for SAP requests"""
        headers = urllib3.make_headers(basic_auth=f"{self.config.username}:{self.config.password}")
        headers['Content-Type'] = 'application/json'
        headers['Accept'] = 'application/json'
        
        if include_csrf and self.csrf_token:
            headers['x-csrf-token'] = self.csrf_token
            headers['Cookie'] = self.cookies
        
        return headers
    
    def get_csrf_token(self):
        """Get CSRF token for write operations"""
        try:
            headers = self.get_headers()
            headers['x-csrf-token'] = 'fetch'
            
            url = f"{self.config.base_url}/sap/opu/odata/sap/API_SALES_ORDER_SRV/?$format=json"
            response = self.http.request('GET', url, headers=headers)
            
            csrf_token = response.headers.get('x-csrf-token')
            if csrf_token:
                self.csrf_token = csrf_token
                cookies = response.headers.get_all('Set-Cookie')
                if cookies:
                    self.cookies = '; '.join([cookie.split(';')[0] for cookie in cookies])
                return True
            return False
            
        except Exception as e:
            print(f"❌ Error getting CSRF token: {e}")
            return False
    
    def test_connection(self):
        """Test connection to SAP system"""
        try:
            url = f"{self.config.base_url}/sap/opu/odata/sap/API_SALES_ORDER_SRV/?$format=json"
            headers = self.get_headers()
            response = self.http.request('GET', url, headers=headers)
            return response.status == 200
        except Exception as e:
            return False
    
    def execute_odata_query(self, entity_set: str, key_value: str = None, expand: List[str] = None, select: List[str] = None) -> Dict[str, Any]:
        """Execute OData query with dynamic expand and select"""
        try:
            # Build URL
            if key_value:
                url = f"{self.config.base_url}/sap/opu/odata/sap/API_SALES_ORDER_SRV/{entity_set}('{key_value}')"
            else:
                url = f"{self.config.base_url}/sap/opu/odata/sap/API_SALES_ORDER_SRV/{entity_set}"
            
            # Build query parameters
            params = []
            if expand:
                params.append(f"$expand={','.join(expand)}")
            if select:
                params.append(f"$select={','.join(select)}")
            params.append("$format=json")
            
            if params:
                url += "?" + "&".join(params)
            
            headers = self.get_headers()
            response = self.http.request('GET', url, headers=headers)
            
            if response.status == 200:
                data = json.loads(response.data.decode('utf-8'))
                return {
                    'success': True,
                    'data': data.get('d', {})
                }
            else:
                return {
                    'success': False,
                    'error': f"Query failed: {response.status}"
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def remove_delivery_block(self, order_id: str, reason: str = "Agent removal") -> Dict[str, Any]:
        """Remove delivery block from sales order with proper ETag handling"""
        try:
            clean_order_id = str(order_id).replace('SO', '').strip()
            
            # Step 1: Get CSRF token
            if not self.get_csrf_token():
                return {
                    'success': False,
                    'error': 'Failed to get CSRF token'
                }
            
            # Step 2: Get current order with ETag
            get_url = f"{self.config.base_url}/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder('{clean_order_id}')?$format=json"
            headers = self.get_headers()
            
            etag_response = self.http.request('GET', get_url, headers=headers)
            
            if etag_response.status != 200:
                return {
                    'success': False,
                    'error': f'Failed to get order for ETag: {etag_response.status}'
                }
            
            # Get ETag
            etag = (etag_response.headers.get('ETag') or 
                    etag_response.headers.get('etag') or 
                    etag_response.headers.get('Etag'))
            
            # Step 3: Update order
            patch_url = f"{self.config.base_url}/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder('{clean_order_id}')"
            
            update_data = {
                "DeliveryBlockReason": ""  # Correct field name
            }
            
            headers = self.get_headers(include_csrf=True)
            if etag:
                headers['If-Match'] = etag
            
            encoded_payload = json.dumps(update_data).encode('utf-8')
            response = self.http.request('PATCH', patch_url, body=encoded_payload, headers=headers)
            
            if response.status in [200, 204]:
                return {
                    'success': True,
                    'message': f'Delivery block removed from order {order_id}',
                    'reason': reason
                }
            else:
                response_text = response.data.decode('utf-8')
                return {
                    'success': False,
                    'error': f'Update failed: {response.status} - {response_text}'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

class MetadataDrivenSAPAgent:
    """SAP Agent that dynamically creates tools based on metadata"""
    
    def __init__(self, sap_service: WorkingSAPService):
        self.sap_service = sap_service
        self.metadata_parser = SAPMetadataParser(sap_service)
        
        # Fetch and parse metadata
        if not self.metadata_parser.fetch_metadata():
            raise Exception("Failed to fetch SAP metadata")
        
        # Create dynamic tools based on metadata
        self._create_dynamic_tools()
        
        # Create the Strands agent
        self._create_agent()
    
    def _create_dynamic_tools(self):
        """Create tools dynamically based on discovered metadata"""
        
        @tool
        def get_order_header(order_id: str) -> str:
            """
            Get sales order header information.
            
            Args:
                order_id: The sales order number (e.g., "4353")
            
            Returns:
                Order header details including customer, amounts, dates, and status
            """
            result = self.sap_service.execute_odata_query('A_SalesOrder', order_id)
            
            if not result['success']:
                return f"Error reading order {order_id}: {result['error']}"
            
            return json.dumps(result['data'], indent=2)
        
        @tool
        def get_order_items(order_id: str) -> str:
            """
            Get detailed item information for a sales order using to_Item association.
            
            Args:
                order_id: The sales order number (e.g., "4353")
            
            Returns:
                Detailed item information including materials, quantities, amounts
            """
            result = self.sap_service.execute_odata_query('A_SalesOrder', order_id, expand=['to_Item'])
            
            if not result['success']:
                return f"Error reading order items for {order_id}: {result['error']}"
            
            # Extract items from the expanded result
            order_data = result['data']
            items = order_data.get('to_Item', {}).get('results', [])
            
            items_info = {
                'order_id': order_id,
                'total_items': len(items),
                'items': []
            }
            
            for item in items:
                item_info = {
                    'material': item.get('Material', 'Unknown'),
                    'description': item.get('MaterialDescription', 'No description'),
                    'quantity': item.get('OrderQuantity', '0'),
                    'unit': item.get('OrderQuantityUnit', 'EA'),
                    'net_amount': item.get('NetAmount', '0'),
                    'item_number': item.get('SalesOrderItem', 'Unknown')
                }
                items_info['items'].append(item_info)
            
            return json.dumps(items_info, indent=2)
        
        @tool
        def get_order_with_associations(order_id: str, associations: str = "to_Item") -> str:
            """
            Get order data with specified associations expanded.
            
            Args:
                order_id: The sales order number (e.g., "4353")
                associations: Comma-separated list of associations to expand (e.g., "to_Item,to_Partner")
            
            Returns:
                Order data with expanded associations
            """
            expand_list = [assoc.strip() for assoc in associations.split(',')]
            result = self.sap_service.execute_odata_query('A_SalesOrder', order_id, expand=expand_list)
            
            if not result['success']:
                return f"Error reading order {order_id} with associations {associations}: {result['error']}"
            
            return json.dumps(result['data'], indent=2)
        
        @tool
        def remove_delivery_block(order_id: str, reason: str = "Approved by agent") -> str:
            """
            Remove delivery block from a sales order.
            
            Args:
                order_id: The sales order number (e.g., "4353")
                reason: Reason for removing the block (optional)
            
            Returns:
                Success or failure message with details
            """
            result = self.sap_service.remove_delivery_block(order_id, reason)
            
            if result['success']:
                return f"SUCCESS: Delivery block removed from order {order_id}. Reason: {reason}. Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            else:
                return f"FAILED: Could not remove delivery block from order {order_id}. Error: {result['error']}"
        
        @tool
        def test_connection() -> str:
            """
            Test the connection to the SAP system.
            
            Returns:
                Connection status message
            """
            if self.sap_service.test_connection():
                return f"SUCCESS: Connected to SAP system at {SAP_CONFIG.base_url}"
            else:
                return f"FAILED: Could not connect to SAP system at {SAP_CONFIG.base_url}"
        
        @tool
        def discover_metadata() -> str:
            """
            Show discovered SAP metadata including entities and associations.
            
            Returns:
                Summary of available entities and navigation properties
            """
            entities_info = {}
            for entity_name, entity_data in self.metadata_parser.entities.items():
                nav_props = [nav['name'] for nav in entity_data['navigation_properties']]
                entities_info[entity_name] = {
                    'navigation_properties': nav_props,
                    'property_count': len(entity_data['properties'])
                }
            
            return json.dumps(entities_info, indent=2)
        
        # Store tools for agent creation
        self.tools = [
            get_order_header,
            get_order_items,
            get_order_with_associations,
            remove_delivery_block,
            test_connection,
            discover_metadata
        ]
    
    def _create_agent(self):
        """Create the Strands agent with dynamic tools"""
        
        # Create Bedrock model
        bedrock_model = BedrockModel(
            model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
            temperature=0.3,
        )
        
        # Get available navigation properties for context
        sales_order_nav_props = self.metadata_parser.get_navigation_properties_for_entity('A_SalesOrderType')
        nav_props_list = [nav['name'] for nav in sales_order_nav_props]
        
        # Enhanced system prompt with metadata awareness
        system_prompt = f"""You are an intelligent SAP Sales Order Assistant with dynamic metadata-driven capabilities.

METADATA-DRIVEN CAPABILITIES:
I have analyzed the SAP OData metadata and discovered the following navigation properties for sales orders:
{', '.join(nav_props_list)}

AVAILABLE TOOLS:
1. get_order_header(order_id) - Get main order information
2. get_order_items(order_id) - Get item details using to_Item association
3. get_order_with_associations(order_id, associations) - Get order with any associations expanded
4. remove_delivery_block(order_id, reason) - Remove delivery blocks
5. test_connection() - Test SAP connectivity
6. discover_metadata() - Show available entities and associations

INTELLIGENT ROUTING:
- For item questions (quantities, materials, etc.) → use get_order_items()
- For partner/customer details → use get_order_with_associations(order_id, "to_Partner")
- For general order info → use get_order_header()
- For complex queries → use get_order_with_associations() with multiple associations

SAP SYSTEM INFO:
- Connected to: {SAP_CONFIG.base_url}
- Service: API_SALES_ORDER_SRV
- Available test order: 4353

CONVERSATION GUIDELINES:
1. Extract order numbers from user requests automatically
2. If no order number provided, ask the user to specify
3. Route questions to appropriate tools based on what information is needed
4. Interpret tool results and provide natural, business-friendly responses
5. For item-related questions, always use the to_Item association
6. Explain SAP data in business terms, not technical jargon

EXAMPLE ROUTING:
- "What items are in order 4353?" → get_order_items("4353")
- "Show me order 4353 details" → get_order_header("4353")
- "Get order 4353 with items and partners" → get_order_with_associations("4353", "to_Item,to_Partner")

Current date: {datetime.now().strftime('%Y-%m-%d')}
"""
        
        # Create the Strands agent
        self.agent = Agent(
            system_prompt=system_prompt,
            model=bedrock_model,
            tools=self.tools
        )
    
    def chat(self, message: str) -> str:
        """Process user message through metadata-driven agent"""
        try:
            response = self.agent(message)
            return response.message
        except Exception as e:
            return f"I encountered an error: {str(e)}. Please try again or contact support."

def main():
    """Main function to run the metadata-driven SAP agent"""
    print("🤖 Metadata-Driven SAP Agent with Dynamic Association Discovery")
    print("=" * 70)
    
    # Initialize SAP service
    print("🔧 Initializing SAP service...")
    sap_service = WorkingSAPService(SAP_CONFIG)
    
    # Test connection
    print("🧪 Testing SAP connection...")
    if not sap_service.test_connection():
        print("❌ Connection failed - check credentials")
        return
    
    print("✅ Connected to SAP system!")
    
    # Initialize metadata-driven agent
    print("🔍 Initializing metadata-driven agent...")
    try:
        agent = MetadataDrivenSAPAgent(sap_service)
        print("✅ Metadata-driven agent ready!")
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")
        return
    
    print("\\n🎉 Metadata-Driven SAP Agent is ready!")
    print("\\nThe agent has analyzed SAP metadata and can intelligently route your questions!")
    print("\\nTry asking:")
    print("• 'What items are in order 4353?'")
    print("• 'Show me the quantities for order 4353'")
    print("• 'Get order 4353 with items and partners'")
    print("• 'What associations are available?'")
    print("• 'Remove delivery block from order 4353'")
    print("\\nType 'quit' to exit.")
    print("-" * 70)
    
    # Main conversation loop
    while True:
        try:
            user_input = input("\\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'bye', 'goodbye']:
                print("\\n🤖 Assistant: Goodbye! Thanks for using the metadata-driven SAP agent!")
                break
            
            if not user_input:
                continue
            
            print("\\n🤖 Assistant: ", end="")
            response = agent.chat(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\\n\\n🤖 Assistant: Goodbye! Thanks for using the metadata-driven SAP agent!")
            break
        except Exception as e:
            print(f"\\n❌ Error: {e}")

if __name__ == "__main__":
    main()