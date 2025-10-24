# SAP Sales Order Agent - Workshop Tutorials

Welcome to the SAP Sales Order Agent workshop! This comprehensive tutorial series will guide you through building a production-ready SAP sales order management agent using Amazon Bedrock AgentCore.

## 🎯 What You'll Build

A complete SAP sales order management system that evolves from a simple prototype to a scalable, secure production application. Your final system will handle real SAP operations with memory, secure integrations, and multiple user interfaces.

> [!IMPORTANT]
> These examples are for educational and workshop purposes. They demonstrate AgentCore concepts and techniques but should be adapted for production use with proper security, error handling, and SAP system integration.

## 🏗️ Architecture Journey

**Journey Overview:**
- **Lab 1:** Basic SAP agent prototype (30 mins)
- **Lab 2:** Add conversation memory (25 mins) 
- **Lab 3:** Integrate with SAP via Gateway (35 mins)
- **Lab 4:** Deploy to production runtime (30 mins)
- **Lab 5:** Build user interfaces (25 mins)
- **Lab 6:** Add observability and monitoring (20 mins)

## 📋 Prerequisites

### Required
- AWS account with Bedrock access
- Python 3.10+
- AWS CLI configured (`aws configure`)
- AgentCore CLI installed (`pip install bedrock-agentcore-starter-toolkit`)

### AWS Permissions
- `BedrockAgentCoreFullAccess` managed policy
- `AmazonBedrockFullAccess` managed policy
- Custom policy for SAP integration (provided in Lab 3)

### Model Access
Enable these models in Amazon Bedrock console:
- Anthropic Claude 3.5 Sonnet
- Anthropic Claude 3.5 Haiku

## 🧪 Labs Overview

### Lab 1: Create SAP Agent Prototype
Build a basic SAP sales order agent with core capabilities:
- Sales order inquiry
- Delivery block management
- Email notifications
- Troubleshooting support

**What you'll learn:** Basic agent creation with Strands Agents and mock SAP data

### Lab 2: Add Memory & Context
Transform your agent to remember conversations and customer context:
- Persistent conversation history
- Customer preference tracking
- Cross-session context awareness
- Order history tracking

**What you'll learn:** AgentCore Memory for conversation persistence

### Lab 3: Integrate with SAP Systems
Connect to real SAP systems via AgentCore Gateway:
- SAP OData API integration
- Secure credential management
- Email service integration
- Knowledge base integration

**What you'll learn:** AgentCore Gateway for secure external integrations

### Lab 4: Deploy to Production
Deploy your agent to handle production traffic:
- AgentCore Runtime deployment
- Session management
- Error handling and resilience
- Performance optimization

**What you'll learn:** AgentCore Runtime with production-grade deployment

### Lab 5: Build User Interfaces
Create multiple interfaces for different user types:
- Streamlit chatbot for end users
- FastAPI server for system integration
- REST API documentation

**What you'll learn:** Multi-interface agent deployment patterns

### Lab 6: Add Observability
Monitor and optimize your production agent:
- CloudWatch integration
- Performance metrics
- Error tracking
- Usage analytics

**What you'll learn:** AgentCore Observability for production monitoring

## 🏛️ Architecture Evolution

Watch your architecture grow from prototype to production:

```
Lab 1: Basic Agent
┌─────────────────┐
│   SAP Agent     │
│   (Mock Data)   │
└─────────────────┘

Lab 2: Agent + Memory
┌─────────────────┐    ┌─────────────────┐
│   SAP Agent     │───▶│ AgentCore       │
│                 │    │ Memory          │
└─────────────────┘    └─────────────────┘

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

Lab 5: Multi-Interface
┌─────────────────┐    ┌─────────────────┐
│ Streamlit UI    │───▶│                 │
├─────────────────┤    │ AgentCore       │
│ FastAPI Server  │───▶│ Runtime         │
├─────────────────┤    │                 │
│ Direct API      │───▶│                 │
└─────────────────┘    └─────────────────┘
```

## 🚀 Getting Started

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd sap-sales-order-agent-workshop
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure AWS**
   ```bash
   aws configure
   # Verify access
   aws bedrock list-foundation-models --region us-east-1
   ```

3. **Start with Lab 1**
   ```bash
   jupyter lab
   # Open lab-01-create-sap-agent.ipynb
   ```

## 📁 Workshop Structure

```
01-tutorials/
├── README.md                           # This file
├── requirements.txt                    # Workshop dependencies
├── utils.py                           # Shared utilities
├── lab-01-create-sap-agent.ipynb     # Basic agent creation
├── lab-02-add-memory.ipynb           # Memory integration
├── lab-03-sap-gateway.ipynb          # SAP system integration
├── lab-04-production-runtime.ipynb   # Runtime deployment
├── lab-05-user-interfaces.ipynb      # UI development
├── lab-06-observability.ipynb        # Monitoring setup
├── lab-07-cleanup.ipynb              # Resource cleanup
├── images/                            # Architecture diagrams
├── lab_helpers/                       # Helper modules
│   ├── sap_agent.py                  # Core agent logic
│   ├── mock_sap_data.py              # Mock SAP data
│   └── ui_components.py              # UI helpers
└── scripts/                           # Deployment scripts
    ├── setup_infrastructure.sh       # AWS resource setup
    └── cleanup_resources.sh          # Resource cleanup
```

## 🎮 Example Scenarios

Throughout the workshop, you'll work with these realistic SAP scenarios:

### Sales Order Management
- "Show me all sales orders with delivery blocks"
- "Tell me about order SO001234"
- "Remove the delivery block from order SO001235"

### Customer Service
- "Send the blocked orders list to manager@company.com"
- "What's causing the delay in order SO001236?"
- "How do I resolve credit limit issues?"

### Troubleshooting
- "Why is order SO001237 stuck in processing?"
- "What are the common causes of delivery blocks?"
- "How do I expedite an urgent order?"

## 🔧 Workshop Tips

### For Instructors
- Each lab includes instructor notes and timing guidance
- All code is tested and includes error handling
- Mock data is provided for offline demonstration
- Architecture diagrams explain each step

### For Participants
- Labs build incrementally - complete them in order
- Each lab has checkpoints to verify progress
- Code snippets are copy-paste ready
- Troubleshooting sections address common issues

## 🆘 Troubleshooting

### Common Issues
1. **AWS Credentials**: Ensure `aws configure` is set up correctly
2. **Model Access**: Enable required models in Bedrock console
3. **Permissions**: Check IAM policies for AgentCore access
4. **Dependencies**: Run `pip install -r requirements.txt`

### Getting Help
- Check the troubleshooting section in each lab
- Review AWS CloudWatch logs for runtime issues
- Use the provided diagnostic scripts

## 🎓 Learning Outcomes

By completing this workshop, you'll understand:

- **AgentCore Fundamentals**: Runtime, Memory, Gateway, Observability
- **SAP Integration Patterns**: Secure API access, data transformation
- **Production Deployment**: Scalability, monitoring, error handling
- **Multi-Interface Design**: Chat, API, and web interfaces
- **Enterprise Security**: Authentication, authorization, audit trails

## 📚 Additional Resources

- [AWS Bedrock AgentCore Documentation](https://docs.aws.amazon.com/bedrock-agentcore/)
- [Strands Agents Documentation](https://strandsagents.com/latest/)
- [SAP OData API Reference](https://help.sap.com/docs/SAP_NETWEAVER_AS_ABAP_FOR_SOH_740/68bf513362174d54b58cddec28794093/59283fc4528f486b83b1a58a4f1063c0.html)

Ready to build your SAP agent? **[Start with Lab 1 →](lab-01-create-sap-agent.ipynb)**