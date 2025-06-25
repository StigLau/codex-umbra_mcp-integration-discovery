#!/usr/bin/env python3
"""
Comprehensive Web Interface and MCP Operations Test Suite
Test the Codex Umbra system's web interface and MCP function calling capabilities
"""

import requests
import json
import time
import sys
from typing import Dict, Any, List, Optional

class CodexUmbraWebTester:
    def __init__(self, base_url: str = "http://localhost:8000", visage_url: str = "http://localhost:5173", mcp_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.visage_url = visage_url
        self.mcp_url = mcp_url
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   Details: {details}")
        if response_data and not success:
            print(f"   Response: {json.dumps(response_data, indent=2)[:200]}...")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details,
            "response": response_data
        })
        print()

    def test_service_health(self) -> bool:
        """Test all service health endpoints"""
        print("🏥 Testing Service Health")
        print("=" * 50)
        
        services = [
            ("Conductor", f"{self.base_url}/health"),
            ("MCP Sentinel", f"{self.mcp_url}/health"),
            ("Visage Frontend", f"{self.visage_url}")
        ]
        
        all_healthy = True
        for service_name, url in services:
            try:
                response = requests.get(url, timeout=5)
                success = response.status_code in [200, 301, 302]
                self.log_test(f"{service_name} Health", success, 
                            f"Status: {response.status_code}", response.json() if success and 'json' in response.headers.get('content-type', '') else None)
                all_healthy &= success
            except Exception as e:
                self.log_test(f"{service_name} Health", False, f"Error: {str(e)}")
                all_healthy = False
        
        return all_healthy

    def test_llm_providers(self) -> bool:
        """Test LLM provider availability"""
        print("🤖 Testing LLM Providers")
        print("=" * 50)
        
        try:
            response = requests.get(f"{self.base_url}/api/v1/llm/providers", timeout=10)
            if response.status_code == 200:
                providers = response.json().get("providers", [])
                self.log_test("LLM Providers Discovery", True, f"Found {len(providers)} providers", providers)
                
                # Test each available provider
                all_providers_working = True
                for provider in providers:
                    if provider.get("available", False):
                        success = self.test_provider_chat(provider["provider"])
                        all_providers_working &= success
                
                return all_providers_working
            else:
                self.log_test("LLM Providers Discovery", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("LLM Providers Discovery", False, f"Error: {str(e)}")
            return False

    def test_provider_chat(self, provider: str) -> bool:
        """Test chat with specific provider"""
        try:
            payload = {
                "message": f"Hello from {provider} test - please respond briefly",
                "user_id": f"test_{provider}_{int(time.time())}"
            }
            
            endpoint = f"{self.base_url}/api/v1/chat/{provider}" if provider != "default" else f"{self.base_url}/api/v1/chat"
            response = requests.post(endpoint, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                has_response = bool(data.get("response", "").strip())
                self.log_test(f"{provider.title()} Chat", has_response, 
                            f"Provider: {data.get('provider_used', 'unknown')}")
                return has_response
            else:
                self.log_test(f"{provider.title()} Chat", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test(f"{provider.title()} Chat", False, f"Error: {str(e)}")
            return False

    def test_mcp_tool_discovery(self) -> bool:
        """Test MCP tool discovery through natural language"""
        print("🔧 Testing MCP Tool Discovery")
        print("=" * 50)
        
        test_queries = [
            "What MCP tools do you have available?",
            "List your available functions and capabilities",
            "Show me what tools I can use with you"
        ]
        
        all_successful = True
        for query in test_queries:
            try:
                payload = {
                    "message": query,
                    "user_id": f"mcp_test_{int(time.time())}"
                }
                
                response = requests.post(f"{self.base_url}/api/v1/chat", json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get("response", "").lower()
                    
                    # Check if response mentions MCP tools
                    has_tools = any(keyword in response_text for keyword in [
                        "system_health", "system_status", "system_config", "add_numbers",
                        "tool", "function", "mcp", "capability"
                    ])
                    
                    self.log_test(f"Tool Discovery Query", has_tools, 
                                f"Query: '{query[:30]}...'")
                    all_successful &= has_tools
                else:
                    self.log_test(f"Tool Discovery Query", False, f"Status: {response.status_code}")
                    all_successful = False
            except Exception as e:
                self.log_test(f"Tool Discovery Query", False, f"Error: {str(e)}")
                all_successful = False
        
        return all_successful

    def test_mcp_function_calling(self) -> bool:
        """Test MCP function calling through natural language"""
        print("⚙️ Testing MCP Function Calling")
        print("=" * 50)
        
        function_tests = [
            {
                "query": "Add the numbers 42 and 58 using your tools",
                "expected_keywords": ["100", "add", "42", "58"],
                "function_name": "add_numbers"
            },
            {
                "query": "Check system health status",
                "expected_keywords": ["health", "status", "system"],
                "function_name": "system_health"
            },
            {
                "query": "Get the current system configuration",
                "expected_keywords": ["config", "system", "configuration"],
                "function_name": "system_config"
            }
        ]
        
        all_successful = True
        for test in function_tests:
            try:
                payload = {
                    "message": test["query"],
                    "user_id": f"func_test_{int(time.time())}",
                    "enable_function_calling": True
                }
                
                response = requests.post(f"{self.base_url}/api/v1/chat", json=payload, timeout=45)
                
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get("response", "").lower()
                    
                    # Check if response contains expected keywords
                    keyword_matches = sum(1 for keyword in test["expected_keywords"] 
                                        if keyword.lower() in response_text)
                    
                    # Check if function calling was enabled
                    function_calling_enabled = data.get("function_calling_enabled", False)
                    
                    success = keyword_matches >= 1 or function_calling_enabled
                    
                    self.log_test(f"Function Call: {test['function_name']}", success,
                                f"Keywords found: {keyword_matches}/{len(test['expected_keywords'])}, "
                                f"Function calling: {function_calling_enabled}")
                    
                    all_successful &= success
                else:
                    self.log_test(f"Function Call: {test['function_name']}", False, 
                                f"Status: {response.status_code}")
                    all_successful = False
            except Exception as e:
                self.log_test(f"Function Call: {test['function_name']}", False, f"Error: {str(e)}")
                all_successful = False
        
        return all_successful

    def test_web_interface_accessibility(self) -> bool:
        """Test web interface accessibility"""
        print("🌐 Testing Web Interface Accessibility")
        print("=" * 50)
        
        try:
            response = requests.get(self.visage_url, timeout=10)
            success = response.status_code == 200
            
            if success:
                # Check for React/Vite indicators
                content = response.text
                has_react = "react" in content.lower() or "vite" in content.lower()
                has_root_div = 'id="root"' in content
                
                self.log_test("Visage Interface Loading", success and has_root_div, 
                            f"React/Vite: {has_react}, Root div: {has_root_div}")
                return success and has_root_div
            else:
                self.log_test("Visage Interface Loading", False, f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Visage Interface Loading", False, f"Error: {str(e)}")
            return False

    def test_end_to_end_conversation(self) -> bool:
        """Test end-to-end conversation flow"""
        print("🔄 Testing End-to-End Conversation Flow")
        print("=" * 50)
        
        conversation_steps = [
            "Hello, I'm testing the system",
            "What can you do?",
            "Add 10 and 20 for me",
            "Check system status",
            "Thank you"
        ]
        
        conversation_id = f"e2e_test_{int(time.time())}"
        all_successful = True
        
        for i, message in enumerate(conversation_steps, 1):
            try:
                payload = {
                    "message": message,
                    "user_id": conversation_id,
                    "conversation_id": conversation_id
                }
                
                response = requests.post(f"{self.base_url}/api/v1/chat", json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    has_response = bool(data.get("response", "").strip())
                    
                    self.log_test(f"Conversation Step {i}", has_response, f"Message: '{message}'")
                    all_successful &= has_response
                else:
                    self.log_test(f"Conversation Step {i}", False, f"Status: {response.status_code}")
                    all_successful = False
                
                # Small delay between messages
                time.sleep(1)
                
            except Exception as e:
                self.log_test(f"Conversation Step {i}", False, f"Error: {str(e)}")
                all_successful = False
        
        return all_successful

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return summary"""
        print("🚀 Starting Codex Umbra Web & MCP Integration Tests")
        print("=" * 60)
        print()
        
        start_time = time.time()
        
        # Run test suites
        tests = [
            ("Service Health", self.test_service_health),
            ("LLM Providers", self.test_llm_providers),
            ("MCP Tool Discovery", self.test_mcp_tool_discovery),
            ("MCP Function Calling", self.test_mcp_function_calling),
            ("Web Interface", self.test_web_interface_accessibility),
            ("End-to-End Flow", self.test_end_to_end_conversation)
        ]
        
        suite_results = {}
        for suite_name, test_func in tests:
            print(f"\n🧪 Running {suite_name} Tests...")
            suite_results[suite_name] = test_func()
        
        # Calculate summary
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        duration = time.time() - start_time
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        print()
        
        for suite_name, passed in suite_results.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"{status} {suite_name}")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "duration": duration,
            "suite_results": suite_results,
            "detailed_results": self.test_results
        }

    def save_results(self, filename: str = "test_results.json"):
        """Save test results to file"""
        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "test_results": self.test_results,
            "summary": {
                "total": len(self.test_results),
                "passed": sum(1 for r in self.test_results if r["success"]),
                "failed": sum(1 for r in self.test_results if not r["success"])
            }
        }
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"📁 Test results saved to {filename}")

def main():
    """Main test runner"""
    if len(sys.argv) > 1 and sys.argv[1] in ["-h", "--help"]:
        print("Usage: python test_web_mcp_integration.py [base_url] [visage_url] [mcp_url]")
        print("Default URLs:")
        print("  base_url: http://localhost:8000")
        print("  visage_url: http://localhost:5173") 
        print("  mcp_url: http://localhost:8001")
        return
    
    # Allow custom URLs via command line
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    visage_url = sys.argv[2] if len(sys.argv) > 2 else "http://localhost:5173"
    mcp_url = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8001"
    
    tester = CodexUmbraWebTester(base_url, visage_url, mcp_url)
    results = tester.run_all_tests()
    tester.save_results()
    
    # Exit with appropriate code
    sys.exit(0 if results["failed_tests"] == 0 else 1)

if __name__ == "__main__":
    main()