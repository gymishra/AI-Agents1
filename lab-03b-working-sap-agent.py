#!/usr/bin/env python3
"""
Lab 3B: Working SAP Agent with Real Integration
This is the working version with all the fixes applied
"""

import json
import urllib3
from typing import Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

# Disable SSL warnings for demo
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass
class SAPConfig:
    base_url: str
    username: str
    password: str
    verify_ssl: bool = False

# SAP Configuration - Update with your credentials
SAP_CONFIG = SAPConfig(
    base_url="https://beydev.ramadokr.people.aws.dev:8443",
    username="ACCAPI",  # Replace with your SAP username
    password="aws4sapD"   # Replace with your SAP password
)

class WorkingSAPService:
    """Working SAP OData service with all fixes applied"""
    
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
                print("✅ CSRF token obtained")
                return True
            
            print("❌ No CSRF token received")
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
            
            if response.status == 200:
                print("✅ SAP connection successful")
                return True
            else:
                print(f"❌ SAP connection failed: {response.status}")
                return False
                
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def read_sales_order(self, order_id: str) -> Dict[str, Any]:
        """Read sales order details from SAP"""
        try:
            clean_order_id = str(order_id).replace('SO', '').strip()
            
            url = f"{self.config.base_url}/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder('{clean_order_id}')"
            params = "$expand=to_Item&$format=json"
            full_url = f"{url}?{params}"
            
            headers = self.get_headers()
            response = self.http.request('GET', full_url, headers=headers)
            
            if response.status == 200:
                data = json.loads(response.data.decode('utf-8'))
                order_data = data.get('d', {})
                print(f"✅ Order {order_id} retrieved successfully")
                return {
                    'success': True,
                    'order_data': order_data
                }
            else:
                print(f"❌ Order {order_id} not found: {response.status}")
                return {
                    'success': False,
                    'error': f"Order not found: {response.status}"
                }
                
        except Exception as e:
            print(f"❌ Error reading order {order_id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def remove_delivery_block(self, order_id: str, reason: str = "Agent removal") -> Dict[str, Any]:
        """Remove delivery block from sales order with proper ETag handling"""
        try:
            clean_order_id = str(order_id).replace('SO', '').strip()
            
            print(f"🔧 Removing delivery block from order {order_id}...")
            
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
            
            print(f"ETag: {etag}")
            
            # Step 3: Update order - use correct field name from discovery
            patch_url = f"{self.config.base_url}/sap/opu/odata/sap/API_SALES_ORDER_SRV/A_SalesOrder('{clean_order_id}')"
            
            # FIXED: Use correct field name discovered from SAP system
            update_data = {
                "DeliveryBlockReason": ""  # This is the correct field name
            }
            
            headers = self.get_headers(include_csrf=True)
            if etag:
                headers['If-Match'] = etag
            
            encoded_payload = json.dumps(update_data).encode('utf-8')
            
            print(f"Updating with payload: {update_data}")
            
            response = self.http.request('PATCH', patch_url, body=encoded_payload, headers=headers)
            
            if response.status in [200, 204]:
                print(f"✅ Delivery block removed from order {order_id}")
                return {
                    'success': True,
                    'message': f'Delivery block removed from order {order_id}',
                    'reason': reason
                }
            else:
                response_text = response.data.decode('utf-8')
                print(f"❌ Failed to remove delivery block: {response.status}")
                return {
                    'success': False,
                    'error': f'Update failed: {response.status} - {response_text}'
                }
                
        except Exception as e:
            print(f"❌ Error removing delivery block: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Strands Agent Integration
from strands import Agent, tool
from strands.models import BedrockModel

class WorkingRealSAPAgent:
    """Working Strands Agent with real SAP integration"""
    
    def __init__(self, sap_service):
        self.sap_service = sap_service
        
        # Create SAP tools that work with real system
        @tool
        def read_and_summarize_order(order_id: str) -> str:
            """Read a sales order from SAP and provide a summary"""
            result = self.sap_service.read_sales_order(order_id)
            
            if not result['success']:
                return f"❌ Could not read order {order_id}: {result['error']}"
            
            order_data = result['order_data']
            
            # Extract key information using correct field names
            order_num = order_data.get('SalesOrder', 'Unknown')
            customer = order_data.get('SoldToParty', 'Unknown')
            total_amount = order_data.get('TotalNetAmount', '0')
            currency = order_data.get('TransactionCurrency', 'USD')
            order_date = order_data.get('SalesOrderDate', 'Unknown')
            
            # Use correct field name from discovery
            delivery_block_reason = order_data.get('DeliveryBlockReason', '')
            
            # Create summary
            summary = f"📦 **Sales Order Summary for {order_num}**\\n\\n"
            summary += f"🏢 Customer: {customer}\\n"
            summary += f"💰 Total Value: {currency} {total_amount}\\n"
            summary += f"📅 Order Date: {order_date}\\n"
            
            if delivery_block_reason:
                summary += f"🚫 **Delivery Block**: Reason code '{delivery_block_reason}'\\n"
            else:
                summary += f"✅ **No Delivery Blocks** - Order ready for processing\\n"
            
            # Add items if available
            items = order_data.get('to_Item', {}).get('results', [])
            if items:
                summary += f"\\n📦 **Items**: {len(items)} line items\\n"
                for i, item in enumerate(items[:3], 1):
                    material = item.get('Material', 'Unknown')
                    quantity = item.get('OrderQuantity', '0')
                    summary += f"   {i}. Material {material} (Qty: {quantity})\\n"
            
            return summary
        
        @tool
        def remove_delivery_block(order_id: str, reason: str = "Approved by agent") -> str:
            """Remove delivery block from a sales order"""
            result = self.sap_service.remove_delivery_block(order_id, reason)
            
            if result['success']:
                response = f"✅ **Delivery Block Removed Successfully!**\\n\\n"
                response += f"📋 Order: {order_id}\\n"
                response += f"📝 Reason: {reason}\\n"
                response += f"⏰ Removed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n\\n"
                response += f"🚀 The order is now released for delivery processing."
                return response
            else:
                return f"❌ Failed to remove delivery block from order {order_id}: {result['error']}"
        
        @tool
        def test_sap_connection() -> str:
            """Test the connection to the SAP system"""
            if self.sap_service.test_connection():
                return "✅ **SAP Connection Test Successful!**\\n\\nThe agent is connected to the SAP system and ready for operations."
            else:
                return "❌ **SAP Connection Test Failed!**\\n\\nPlease check SAP credentials and network connectivity."
        
        # Create Bedrock model
        bedrock_model = BedrockModel(
            model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
            temperature=0.3,
        )
        
        # System prompt for SAP agent
        system_prompt = f"""You are a helpful SAP Sales Order Agent with real SAP system integration.

You can:
- Read and summarize sales orders from the real SAP system
- Remove delivery blocks from orders with proper validation
- Test SAP system connectivity

You are connected to: {SAP_CONFIG.base_url}
Test order available: 4353

Always:
- Extract order numbers from user requests (e.g., "order 4353" → order_id="4353")
- Provide clear, business-friendly explanations
- Confirm actions before making changes
- Handle errors gracefully

Current date: {datetime.now().strftime('%Y-%m-%d')}
"""
        
        # Create agent
        self.agent = Agent(
            system_prompt=system_prompt,
            model=bedrock_model,
            tools=[
                read_and_summarize_order,
                remove_delivery_block,
                test_sap_connection
            ]
        )
    
    def process_message(self, message: str) -> str:
        """Process user message with SAP integration"""
        try:
            response = self.agent(message)
            return response.message
        except Exception as e:
            return f"Error processing message: {str(e)}"

def main():
    """Main function to test the working SAP agent"""
    
    print("🚀 Working SAP Agent - Lab 3B")
    print("="*50)
    
    if SAP_CONFIG.username == "your_username":
        print("⚠️  Please update SAP_USERNAME and SAP_PASSWORD in SAP_CONFIG")
        return
    
    # Initialize services
    print("🔧 Initializing SAP service...")
    sap_service = WorkingSAPService(SAP_CONFIG)
    
    # Test connection
    print("\\n🧪 Testing SAP connection...")
    if not sap_service.test_connection():
        print("❌ Connection failed - check credentials")
        return
    
    # Initialize agent
    print("\\n🤖 Initializing SAP Agent...")
    agent = WorkingRealSAPAgent(sap_service)
    print("✅ Agent ready!")
    
    # Test scenarios
    test_queries = [
        "Test our SAP connection",
        "Tell me about order 4353",
        "Remove the delivery block from order 4353 because it was approved",
        "Check order 4353 again to confirm the block is removed"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\\n{'='*60}")
        print(f"TEST {i}: {query}")
        print("="*60)
        
        try:
            response = agent.process_message(query)
            print(response)
        except Exception as e:
            print(f"❌ Test failed: {e}")
        
        input("\\nPress Enter to continue to next test...")
    
    print("\\n🎉 All tests completed!")

if __name__ == "__main__":
    main()