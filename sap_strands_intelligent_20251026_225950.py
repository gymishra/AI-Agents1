"""
Memory-Enhanced SAP Sales Order Strands Agent (Lab 2 Style)
Uses Strands with AgentCore Memory hooks for conversation persistence
"""

import json
import urllib3
import base64
import os
import hashlib
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from strands import Agent, tool
from strands.hooks import AgentInitializedEvent, HookProvider, HookRegistry, MessageAddedEvent
from strands.models import BedrockModel
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from bedrock_agentcore_starter_toolkit.operations.memory.manager import MemoryManager
from bedrock_agentcore.memory.constants import ConversationalMessage, MessageRole
from bedrock_agentcore.memory.session import MemorySession, MemorySessionManager

# SAP Configuration
SAP_CONFIG = {
    'base_url': 'https://vhcals4hci.awspoc.club/sap/opu/odata/sap/API_SALES_ORDER_SRV/',
    'username': 'gyanmis',
    'password': 'Pass2025$',
    'client': '100'
}

# Memory Configuration - Runtime Configurable
MEMORY_ID = os.environ.get('SAP_AGENT_MEMORY_ID', "sap_strand_intelligent_agent_v1")
ACTOR_ID = os.environ.get('SAP_AGENT_ACTOR_ID', "sap_user_123")
SESSION_ID = os.environ.get('SAP_AGENT_SESSION_ID', "sap_session_001")

# Define message role constants
USER = MessageRole.USER
ASSISTANT = MessageRole.ASSISTANT

def generate_session_id(user_identifier: str = None) -> str:
    """Generate a unique session ID"""
    if user_identifier:
        return f"sap_session_{user_identifier}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    else:
        return f"sap_session_{str(uuid.uuid4())[:8]}"

def make_sap_request(entity_name, params=None):
    """Make SAP OData request with error handling"""
    try:
        http = urllib3.PoolManager()
        auth_b64 = base64.b64encode(f"{SAP_CONFIG['username']}:{SAP_CONFIG['password']}".encode('ascii')).decode('ascii')
        
        query_parts = []
        if params:
            for key, value in params.items():
                if value:
                    query_parts.append(f"${key}={value}")
        
        query_string = '&'.join(query_parts)
        url = f"{SAP_CONFIG['base_url']}{entity_name}"
        if query_string:
            url += f"?{query_string}"
        
        headers = {
            'Authorization': f'Basic {auth_b64}',
            'Accept': 'application/json',
            'sap-client': SAP_CONFIG['client']
        }
        
        response = http.request('GET', url, headers=headers)
        
        if response.status == 200:
            return json.loads(response.data.decode('utf-8'))
        else:
            return {"error": f"HTTP {response.status}: {response.data.decode('utf-8')}"}
            
    except Exception as e:
        return {"error": f"Request failed: {str(e)}"}

class SAPMemoryHookProvider(HookProvider):
    """Memory hook provider for SAP agent using MemorySession (Modern Pattern)"""
    
    def __init__(self, memory_session: MemorySession):
        self.memory_session = memory_session
    
    def on_agent_initialized(self, event: AgentInitializedEvent):
        """Load recent conversation history when agent starts using MemorySession"""
        try:
            # Use the pre-configured memory session (no need for actor_id/session_id)
            recent_turns = self.memory_session.get_last_k_turns(k=5)
            
            if recent_turns:
                # Format conversation history for context
                context_messages = []
                for turn in recent_turns:
                    for message in turn:
                        # Handle both EventMessage objects and dict formats
                        if hasattr(message, 'role') and hasattr(message, 'content'):
                            role = message['role']
                            content = message['content']
                        else:
                            role = message.get('role', 'unknown')
                            content = message.get('content', {}).get('text', '')
                        context_messages.append(f"{role}: {content}")
                
                context = "\n".join(context_messages)
                # Add context to agent's system prompt
                event.agent.system_prompt += f"\n\nRecent conversation:\n{context}"
                print(f"✅ Loaded {len(recent_turns)} conversation turns using MemorySession")
                
        except Exception as e:
            print(f"Memory load error: {e}")
    
    def on_message_added(self, event: MessageAddedEvent):
        """Store messages in memory using MemorySession"""
        messages = event.agent.messages
        try:
            if messages and len(messages) > 0 and messages[-1]["content"][0].get("text"):
                message_text = messages[-1]["content"][0]["text"]
                message_role = MessageRole.USER if messages[-1]["role"] == "user" else MessageRole.ASSISTANT
                
                # Use memory session instance (no need to pass actor_id/session_id)
                result = self.memory_session.add_turns(
                    messages=[ConversationalMessage(message_text, message_role)]
                )
                
                event_id = result['eventId']
                print(f"✅ Stored message with Event ID: {event_id}, Role: {message_role.value}")
                
        except Exception as e:
            print(f"Memory save error: {e}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
    
    def register_hooks(self, registry: HookRegistry):
        # Register memory hooks
        registry.add_callback(MessageAddedEvent, self.on_message_added)
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)
        print("✅ Memory hooks registered with MemorySession")



def create_intelligent_sap_agent():
    """Create intelligent SAP Strands Agent with MemoryManager and MemorySession"""
    
    # Setup AgentCore Memory with ganesh profile
    import boto3
    import os
    
    # Set AWS profile environment variable for MemoryManager
    os.environ['AWS_PROFILE'] = 'default'  # Use default profile
    
    # Initialize Memory Manager (Modern Pattern)
    memory_manager = MemoryManager(region_name="us-east-1")
    memory_name = "strands_claude_getting_started"
    
    print(f"✅ MemoryManager initialized for region: us-east-1")
    print(f"👤 Profile: default")
    
    # Create or get existing memory resource using MemoryManager
    try:
        memory = memory_manager.get_or_create_memory(
            name=memory_name,
            strategies=[],  # No strategies for short-term memory
            description="Memory for SAP Sales Order Intelligent Agent with conversation persistence",
            event_expiry_days=30,  # Keep conversations for 30 days
            memory_execution_role_arn=None,  # Optional for short-term memory
        )
        memory_id = memory.id
        print(f"✅ Successfully created/retrieved memory with MemoryManager:")
        print(f"   Memory ID: {memory_id}")
        print(f"   Memory Name: {memory.name}")
        print(f"   Memory Status: {memory.status}")
        
    except Exception as e:
        print(f"❌ Memory creation failed: {e}")
        # Fallback to predefined memory ID
        memory_id = MEMORY_ID
        print(f"🔄 Using fallback Memory ID: {memory_id}")
    
    # Initialize the session memory manager
    session_manager = MemorySessionManager(memory_id=memory_id, region_name="us-east-1")
    
    # Create a memory session for the specific actor/session combination
    user_session = session_manager.create_memory_session(
        actor_id=ACTOR_ID, 
        session_id=SESSION_ID
    )
    
    print(f"✅ Session manager initialized for memory: {memory_id}")
    print(f"✅ Memory session created for actor: {ACTOR_ID}, session: {SESSION_ID}")

    # Create Bedrock model
    bedrock_model = BedrockModel(
        model_id="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        temperature=0.3,
    )
    
    @tool
    def get_sales_order_details(order_number: str) -> str:
        """Get complete details for a specific sales order number"""
        params = {"filter": f"SalesOrder eq '{order_number}'"}
        result = make_sap_request("A_SalesOrder", params)
        
        if 'error' in result:
            return f"Error: {result['error']}"
        
        records = result.get('d', {}).get('results', [])
        if not records:
            return f"Sales order {order_number} not found"
        
        order = records[0]
        return f"""Sales Order {order_number}:
• Value: {order.get('TotalNetAmount', 'N/A')} {order.get('TransactionCurrency', 'USD')}
• Customer: {order.get('SoldToParty', 'N/A')}
• Type: {order.get('SalesOrderType', 'N/A')}
• Status: {order.get('OverallSDProcessStatus', 'N/A')}
• Created: {order.get('CreationDate', 'N/A')}"""
    
    @tool
    def search_recent_orders(limit: int = 5) -> str:
        """Get recent sales orders"""
        params = {"top": str(limit), "orderby": "CreationDate desc"}
        result = make_sap_request("A_SalesOrder", params)
        
        if 'error' in result:
            return f"Error: {result['error']}"
        
        records = result.get('d', {}).get('results', [])
        if not records:
            return "No sales orders found"
        
        orders = []
        for order in records:
            orders.append(f"• Order {order.get('SalesOrder', 'N/A')}: {order.get('TotalNetAmount', 'N/A')} {order.get('TransactionCurrency', 'USD')}")
        
        return "Recent Sales Orders:\n" + "\n".join(orders)
    
    @tool
    def search_orders_by_customer(customer_id: str, limit: int = 5) -> str:
        """Search sales orders by customer ID"""
        params = {
            "filter": f"SoldToParty eq '{customer_id}'",
            "top": str(limit)
        }
        result = make_sap_request("A_SalesOrder", params)
        
        if 'error' in result:
            return f"Error: {result['error']}"
        
        records = result.get('d', {}).get('results', [])
        if not records:
            return f"No orders found for customer {customer_id}"
        
        orders = []
        for order in records:
            orders.append(f"• Order {order.get('SalesOrder', 'N/A')}: {order.get('TotalNetAmount', 'N/A')} {order.get('TransactionCurrency', 'USD')}")
        
        return f"Orders for Customer {customer_id}:\n" + "\n".join(orders)
    
    @tool
    def get_order_value_range(min_value: float = None, max_value: float = None) -> str:
        """Find orders within a value range"""
        filter_parts = []
        if min_value:
            filter_parts.append(f"TotalNetAmount ge {min_value}")
        if max_value:
            filter_parts.append(f"TotalNetAmount le {max_value}")
        
        params = {"top": "10"}
        if filter_parts:
            params["filter"] = " and ".join(filter_parts)
        
        result = make_sap_request("A_SalesOrder", params)
        
        if 'error' in result:
            return f"Error: {result['error']}"
        
        records = result.get('d', {}).get('results', [])
        if not records:
            return "No orders found in specified range"
        
        orders = []
        for order in records:
            orders.append(f"• Order {order.get('SalesOrder', 'N/A')}: {order.get('TotalNetAmount', 'N/A')} {order.get('TransactionCurrency', 'USD')}")
        
        return "Orders in Range:\n" + "\n".join(orders)
    
    # SAP-focused system prompt (Lab 2 style)
    sap_system_prompt = f"""You are a SAP Sales Order Agent with memory capabilities. You can remember previous conversations and help with:

1. Get specific sales order details by order number
2. Search recent sales orders
3. Find orders by customer ID
4. Search orders by value range

Choose the most appropriate tool based on the user's request:
- For specific order numbers (like "5051", "4062") → use get_sales_order_details
- For "recent orders" or "latest orders" → use search_recent_orders  
- For customer-specific queries → use search_orders_by_customer
- For value/amount queries → use get_order_value_range

Always be professional and reference previous conversations when relevant.
Today's date: {datetime.now().strftime('%Y-%m-%d')}
"""
    
    # Create Strands Agent with MemorySession hooks (Modern Pattern)
    agent = Agent(
        name="MemoryEnabledSAPAgent",
        model=bedrock_model,
        system_prompt=sap_system_prompt,
        hooks=[SAPMemoryHookProvider(user_session)],  # Pass MemorySession instead
        tools=[get_sales_order_details, search_recent_orders, search_orders_by_customer, get_order_value_range],
        state={"actor_id": ACTOR_ID, "session_id": SESSION_ID}
    )
    
    return agent, user_session  # Return both agent and session for runtime use

# Create the agent instance with MemorySession
sap_agent, memory_session = create_intelligent_sap_agent()

# AgentCore Runtime App
app = BedrockAgentCoreApp()

def process_message_with_memory(message: str, session_id: str = None, actor_id: str = None) -> str:
    """Process a user message with memory capabilities using MemorySession"""
    try:
        # Update session and actor if provided using proper AgentState methods
        if session_id:
            sap_agent.state.set("session_id", session_id)
        if actor_id:
            sap_agent.state.set("actor_id", actor_id)
        
        # If different session/actor provided, create new memory session
        if (session_id and session_id != SESSION_ID) or (actor_id and actor_id != ACTOR_ID):
            print(f"🔄 Creating new memory session for actor: {actor_id}, session: {session_id}")
            # Note: In production, you'd want to manage multiple sessions
            # For now, we'll use the existing session
        
        response = sap_agent(message)
        return response.message
        
    except Exception as e:
        return f"Error processing message with memory: {str(e)}"

@app.entrypoint
def handler(payload):
    """AgentCore entrypoint - lets AgentCore manage sessions automatically"""
    try:
        prompt = payload.get("prompt", "")
        
        # Runtime memory configuration - can be overridden per request
        runtime_memory_id = payload.get("memory_id", MEMORY_ID)
        if runtime_memory_id != MEMORY_ID:
            print(f"🔄 Using runtime memory ID: {runtime_memory_id}")
        
        # AgentCore session management:
        # - First call: no session_id → AgentCore creates new session and returns it
        # - Subsequent calls: include session_id → AgentCore continues existing session
        session_id = payload.get("session_id")
        actor_id = payload.get("actor_id", "user")
        
        if session_id:
            print(f"🔄 Continuing AgentCore session: {session_id}")
        else:
            print(f"🆕 New session (AgentCore will create and return session_id)")
        
        print(f"🔍 Processing request:")
        print(f"   📝 Prompt: {prompt[:50]}...")
        print(f"   � Acotor: {actor_id}")
        print(f"   🧠 Memory: {MEMORY_ID}")
        
        # Use session_id for memory continuity
        # If no session_id provided, use a default (AgentCore will manage the real session)
        memory_session_id = session_id or "agentcore_managed_session"
        
        # Process with memory-enhanced agent
        response = process_message_with_memory(
            message=prompt,
            session_id=memory_session_id,
            actor_id=actor_id
        )
        
        # Return simple response - AgentCore handles session management
        # Client should extract session_id from AgentCore's response envelope
        return {"response": response}
        
    except Exception as e:
        return {"response": f"Error: {str(e)}"}

def test_session_management():
    """Test session management workflow"""
    print("=" * 70)
    print("🚀 Testing Session Management with Memory")
    print("=" * 70)
    
    # Simulate first invocation (no session ID provided)
    print("\n📋 Test 1: First Invocation (No Session ID)")
    print("-" * 50)
    
    payload1 = {
        "prompt": "Can you get details for order 4062?",
        "actor_id": "john_acme"
        # No session_id provided - should generate new one
    }
    
    print(f"� Request  1: {payload1}")
    result1 = handler(payload1)
    session_id = result1.get("session_id")  # Save session ID for next call
    
    print(f"� Respsonse 1:")
    print(f"   🆔 Session ID: {session_id}")
    print(f"   👤 Actor ID: {result1.get('actor_id')}")
    print(f"   📝 Response: {result1.get('response')[:100]}...")
    
    # Simulate second invocation (with session ID from first call)
    print("\n📋 Test 2: Second Invocation (With Session ID)")
    print("-" * 50)
    
    payload2 = {
        "prompt": "What is the Order type of that Sales Order?",
        "actor_id": "john_acme",
        "session_id": session_id  # Use session ID from first call
    }
    
    print(f"📤 Request 2: {payload2}")
    result2 = handler(payload2)
    
    print(f"📥 Response 2:")
    print(f"   🆔 Session ID: {result2.get('session_id')}")
    print(f"   👤 Actor ID: {result2.get('actor_id')}")
    print(f"   📝 Response: {result2.get('response')[:100]}...")
    
    # Simulate third invocation (continuing same session)
    print("\n📋 Test 3: Third Invocation (Same Session)")
    print("-" * 50)
    
    payload3 = {
        "prompt": "What was the total value of that order?",
        "actor_id": "john_acme",
        "session_id": session_id  # Continue same session
    }
    
    print(f"📤 Request 3: {payload3}")
    result3 = handler(payload3)
    
    print(f"📥 Response 3:")
    print(f"   🆔 Session ID: {result3.get('session_id')}")
    print(f"   👤 Actor ID: {result3.get('actor_id')}")
    print(f"   📝 Response: {result3.get('response')[:100]}...")
    
    # Test with new user (different actor, no session)
    print("\n📋 Test 4: New User (Different Actor)")
    print("-" * 50)
    
    payload4 = {
        "prompt": "Show me recent sales orders",
        "actor_id": "sarah_corp"
        # No session_id - should generate new session for new user
    }
    
    print(f"📤 Request 4: {payload4}")
    result4 = handler(payload4)
    
    print(f"📥 Response 4:")
    print(f"   🆔 Session ID: {result4.get('session_id')}")
    print(f"   👤 Actor ID: {result4.get('actor_id')}")
    print(f"   📝 Response: {result4.get('response')[:100]}...")
    
    print("\n✅ Session management test completed!")
    print(f"🧠 All conversations stored in Memory: {MEMORY_ID}")
    
    return {
        "john_session": session_id,
        "sarah_session": result4.get('session_id')
    }

def test_agentcore_session_workflow():
    """Test AgentCore session management workflow"""
    print("=" * 70)
    print("🚀 Testing AgentCore Session Management Workflow")
    print("=" * 70)
    
    # Simulate client workflow with AgentCore
    print("\n📋 Client Workflow Simulation:")
    print("1. First call: No session_id → AgentCore creates session")
    print("2. Extract session_id from AgentCore response")
    print("3. Subsequent calls: Use extracted session_id")
    print("-" * 50)
    
    # Test 1: First call (no session_id)
    print("\n📋 Test 1: First Call (No Session ID)")
    print("-" * 30)
    
    payload1 = {
        "prompt": "Can you get details for order 4062?",
        "actor_id": "john_acme"
        # No session_id - AgentCore will create one
    }
    
    print(f"📤 Request: {payload1}")
    result1 = handler(payload1)
    response1 = result1.get('response', '')
    print(f"📥 Agent Response: {str(response1)[:100] if response1 else 'No response'}...")
    print("📝 Note: AgentCore runtime will wrap this with session_id")
    
    # Test 2: Simulate extracted session_id from AgentCore
    print("\n📋 Test 2: Follow-up with Session ID")
    print("-" * 30)
    
    # Simulate session_id extracted from AgentCore response
    extracted_session_id = "agentcore_session_12345"  # This would come from AgentCore
    
    payload2 = {
        "prompt": "What is the Order type of that Sales Order?",
        "actor_id": "john_acme",
        "session_id": extracted_session_id  # Use extracted session_id
    }
    
    print(f"📤 Request: {payload2}")
    result2 = handler(payload2)
    response2 = result2.get('response', '')
    print(f"📥 Agent Response: {str(response2)[:100] if response2 else 'No response'}...")
    
    # Test 3: Continue conversation
    print("\n📋 Test 3: Continue Conversation")
    print("-" * 30)
    
    payload3 = {
        "prompt": "What was the total value of that order?",
        "actor_id": "john_acme",
        "session_id": extracted_session_id  # Same session
    }
    
    print(f"📤 Request: {payload3}")
    result3 = handler(payload3)
    response3 = result3.get('response', '')
    print(f"📥 Agent Response: {str(response3)[:100] if response3 else 'No response'}...")
    
    print("\n✅ AgentCore session workflow test completed!")
    print(f"🧠 Memory ID: {MEMORY_ID}")
    print("📝 AgentCore manages sessions - client extracts session_id from responses")

def view_stored_memory():
    """View stored memory contents using MemorySession"""
    print("=" * 70)
    print("🧠 Viewing Stored Memory Contents")
    print("=" * 70)
    
    try:
        # Check what's stored in memory using MemorySession
        recent_turns = memory_session.get_last_k_turns(k=3) 
        
        if recent_turns:
            for i, turn in enumerate(recent_turns, 1):
                print(f"Turn {i}:")
                for message in turn:
                    role = message['role']
                    content = message['content']['text'][:100] + "..." if len(message['content']['text']) > 100 else message['content']['text']
                    print(f"  {role}: {content}")
                print()
        else:
            print("No conversation history found in memory")
            
    except Exception as e:
        print(f"❌ Error viewing memory: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    # Test AgentCore session workflow
    test_agentcore_session_workflow()
    
    # View stored memory contents
    view_stored_memory()
    
    # Run the AgentCore app
    print("\n🚀 Starting AgentCore Runtime...")
    print("📝 Session Management:")
    print("   - First call: AgentCore creates session_id")
    print("   - Client extracts session_id from response")
    print("   - Subsequent calls: Client includes session_id")
    print(f"🧠 Using MemoryManager with MemorySession")
    print(f"🆔 Memory ID: {MEMORY_ID}")
    app.run()
