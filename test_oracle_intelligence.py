#!/usr/bin/env python3
"""
Test The Oracle's Enhanced Intelligence with MCP Prompt Discovery
Demonstrates how The Oracle automatically discovers and uses sophisticated MCP prompts
"""

import asyncio
import sys
import os

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'conductor_project'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'mcp_server_project'))

async def test_oracle_intelligence():
    """Test The Oracle's enhanced intelligence with various query types"""
    
    print("🔮 **TESTING THE ORACLE'S ENHANCED INTELLIGENCE** 🔮")
    print("=" * 60)
    
    # Import services
    from conductor_project.app.services.llm_service_v2 import LLMServiceV2
    from conductor_project.app.services.mcp_service_v2 import MCPServiceV2
    
    # Initialize services
    mcp_service = MCPServiceV2()
    llm_service = LLMServiceV2()
    
    # Test queries that should trigger different MCP prompts
    test_queries = [
        {
            "query": "I need a comprehensive health analysis of the system",
            "expected_prompt": "system_analysis",
            "expected_intent": "health_analysis"
        },
        {
            "query": "The system is broken and I need urgent troubleshooting help",
            "expected_prompt": "troubleshooting", 
            "expected_intent": "troubleshooting"
        },
        {
            "query": "Can you provide detailed technical analysis of performance bottlenecks?",
            "expected_prompt": "expert_consultation",
            "expected_intent": "expert_consultation"
        },
        {
            "query": "What will the system performance look like in the future?",
            "expected_prompt": "predictive_analysis",
            "expected_intent": "predictive_analysis"
        },
        {
            "query": "What's the current status of all components?",
            "expected_prompt": "intelligent_assistant",
            "expected_intent": "status_inquiry"
        }
    ]
    
    print("🧠 **INTENT ANALYSIS TESTING**")
    print("-" * 40)
    
    for i, test in enumerate(test_queries, 1):
        print(f"\n**Test {i}**: {test['query']}")
        
        # Test advanced intent analysis
        intent_analysis = await llm_service._advanced_intent_analysis(test['query'])
        
        print(f"✅ **Detected Intent**: {intent_analysis['primary_intent']}")
        print(f"✅ **Selected MCP Prompt**: {intent_analysis['optimal_prompt_name']}")
        print(f"✅ **Complexity Level**: {intent_analysis['complexity']}")
        print(f"✅ **Urgency Level**: {intent_analysis['urgency']}")
        
        # Verify correct prompt selection
        if intent_analysis['optimal_prompt_name'] == test['expected_prompt']:
            print("🎯 **PROMPT SELECTION**: ✅ CORRECT")
        else:
            print(f"❌ **PROMPT SELECTION**: Expected {test['expected_prompt']}, got {intent_analysis['optimal_prompt_name']}")
        
        # Verify correct intent detection
        if intent_analysis['primary_intent'] == test['expected_intent']:
            print("🎯 **INTENT DETECTION**: ✅ CORRECT")
        else:
            print(f"❌ **INTENT DETECTION**: Expected {test['expected_intent']}, got {intent_analysis['primary_intent']}")
    
    print("\n" + "=" * 60)
    print("🔮 **MCP PROMPT DISCOVERY TESTING**")
    print("-" * 40)
    
    # Test MCP capabilities discovery
    try:
        capabilities = await mcp_service.discover_capabilities()
        print(f"✅ **MCP Connection**: Successfully discovered {len(capabilities.get('tools', []))} tools")
        print(f"✅ **Available Tools**: {', '.join(capabilities.get('tools', []))}")
        print(f"✅ **Available Prompts**: {', '.join(capabilities.get('prompts', []))}")
    except Exception as e:
        print(f"❌ **MCP Connection**: Failed - {e}")
        print("ℹ️  **Note**: Start MCP server with: docker-compose -f docker-compose.mcp.yml up -d")
        return
    
    # Test prompt retrieval
    print(f"\n🧠 **TESTING MCP PROMPT RETRIEVAL**")
    print("-" * 40)
    
    for prompt_name in ["intelligent_assistant", "system_analysis", "troubleshooting"]:
        try:
            prompt_args = {
                "user_query": "Test query",
                "analysis_type": "health_analysis",
                "issue_description": "Test issue"
            }
            
            prompt_result = await mcp_service.get_prompt_template(prompt_name, prompt_args)
            
            if "error" not in prompt_result and "messages" in prompt_result:
                prompt_content = prompt_result["messages"][0]["content"]["text"]
                print(f"✅ **{prompt_name}**: Retrieved ({len(prompt_content)} chars)")
                
                # Show a sample of the sophisticated prompt
                sample = prompt_content[:200] + "..." if len(prompt_content) > 200 else prompt_content
                print(f"   📋 Sample: {sample}")
            else:
                print(f"❌ **{prompt_name}**: Failed - {prompt_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ **{prompt_name}**: Exception - {e}")
    
    print("\n" + "=" * 60)
    print("🚀 **END-TO-END ORACLE INTELLIGENCE TEST**")
    print("-" * 40)
    
    # Test full Oracle intelligence with one sophisticated query
    sophisticated_query = "I need an urgent comprehensive diagnostic analysis of system health with detailed technical recommendations"
    
    print(f"**Query**: {sophisticated_query}")
    print("\n🔮 **The Oracle is thinking...**")
    
    try:
        # This should trigger the advanced MCP prompt discovery
        response = await llm_service.interpret_user_request_with_mcp(sophisticated_query)
        
        print(f"\n✅ **Response Generated**: {len(response.get('response', ''))} characters")
        print(f"✅ **Intelligence Mode**: {response.get('intelligence_mode', 'unknown')}")
        
        if "mcp_prompt_used" in response:
            print(f"✅ **MCP Prompt Used**: {response['mcp_prompt_used']}")
        
        if "intelligence_level" in response:
            print(f"✅ **Intelligence Level**: {response['intelligence_level']}")
        
        # Show a sample of the Oracle's sophisticated response
        oracle_response = response.get('response', '')
        if oracle_response:
            sample = oracle_response[:500] + "..." if len(oracle_response) > 500 else oracle_response
            print(f"\n📝 **Oracle Response Sample**:")
            print("-" * 30)
            print(sample)
        
    except Exception as e:
        print(f"❌ **Oracle Intelligence Test Failed**: {e}")
        print("ℹ️  **Note**: Ensure both MCP server and Ollama are running")
    
    print("\n" + "=" * 60)
    print("🎉 **ORACLE INTELLIGENCE TESTING COMPLETE** 🎉")
    
    # Cleanup
    try:
        await mcp_service.disconnect()
        print("✅ MCP connections cleaned up")
    except:
        pass

if __name__ == "__main__":
    asyncio.run(test_oracle_intelligence())