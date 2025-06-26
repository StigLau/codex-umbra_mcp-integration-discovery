#!/usr/bin/env python3
"""
Test script for MCP Server improvements
Validates Oracle-requested enhancements: structured JSON, async operations, enhanced tooling
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, List
import aiohttp
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MCPImprovementTester:
    def __init__(self):
        self.conductor_url = "http://localhost:8090"
        self.test_results = []
        
    async def test_structured_json_responses(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test the new structured JSON response format"""
        logger.info("🧪 Testing Structured JSON Responses")
        
        test_cases = [
            {
                "name": "system_health_json_format",
                "payload": {
                    "message": "Test system health with JSON response format",
                    "user_id": "test_structured_json",
                    "function_calls": [{
                        "name": "system_health",
                        "arguments": {
                            "component": "all",
                            "detail_level": "detailed",
                            "response_format": "json"
                        }
                    }]
                },
                "expected_response_type": "json"
            },
            {
                "name": "system_status_both_format",
                "payload": {
                    "message": "Test system status with both formats",
                    "user_id": "test_both_format",
                    "function_calls": [{
                        "name": "system_status",
                        "arguments": {
                            "component": "sentinel",
                            "format": "detailed",
                            "response_format": "both"
                        }
                    }]
                },
                "expected_response_type": "both"
            }
        ]
        
        results = []
        for test_case in test_cases:
            try:
                start_time = time.time()
                async with session.post(
                    f"{self.conductor_url}/api/v1/chat",
                    json=test_case["payload"],
                    timeout=15
                ) as response:
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        
                        result = {
                            "test_name": test_case["name"],
                            "status": "success",
                            "response_time": response_time,
                            "response_format_tested": test_case["expected_response_type"],
                            "oracle_response_preview": data.get('response', '')[:200] + "..." if len(data.get('response', '')) > 200 else data.get('response', '')
                        }
                        
                        # Check if Oracle mentions structured data
                        if "json" in data.get('response', '').lower() or "structured" in data.get('response', '').lower():
                            result["oracle_structured_recognition"] = True
                            logger.info(f"✅ {test_case['name']} - Oracle recognized structured response")
                        else:
                            result["oracle_structured_recognition"] = False
                            logger.warning(f"⚠️  {test_case['name']} - Oracle may not have recognized structured format")
                    else:
                        result = {
                            "test_name": test_case["name"],
                            "status": "failed",
                            "error": f"HTTP {response.status}",
                            "response_time": response_time
                        }
                        logger.error(f"❌ {test_case['name']} failed with status {response.status}")
                        
            except Exception as e:
                result = {
                    "test_name": test_case["name"],
                    "status": "error",
                    "error": str(e),
                    "response_time": time.time() - start_time
                }
                logger.error(f"❌ {test_case['name']} failed with error: {e}")
            
            results.append(result)
            await asyncio.sleep(1)  # Brief pause between tests
        
        return {
            "category": "structured_json_responses",
            "tests": results,
            "summary": {
                "total": len(results),
                "successful": len([r for r in results if r["status"] == "success"]),
                "oracle_recognition_rate": len([r for r in results if r.get("oracle_structured_recognition", False)]) / len(results) * 100
            }
        }
    
    async def test_async_operations(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test async operation support"""
        logger.info("⚡ Testing Async Operations")
        
        # Test async operation initiation
        async_test_payload = {
            "message": "Start an async system health check and track its progress",
            "user_id": "test_async_ops",
            "function_calls": [{
                "name": "system_health",
                "arguments": {
                    "component": "all",
                    "detail_level": "diagnostic",
                    "async_mode": True,
                    "response_format": "json"
                }
            }]
        }
        
        results = []
        operation_id = None
        
        try:
            # Start async operation
            start_time = time.time()
            logger.info("🚀 Starting async operation...")
            
            async with session.post(
                f"{self.conductor_url}/api/v1/chat",
                json=async_test_payload,
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    oracle_response = data.get('response', '')
                    
                    # Try to extract operation ID from Oracle's response
                    # Oracle should mention the operation ID in its response
                    if "operation" in oracle_response.lower() and ("id" in oracle_response.lower() or "started" in oracle_response.lower()):
                        result = {
                            "test_name": "async_operation_start",
                            "status": "success",
                            "oracle_async_recognition": True,
                            "response_time": time.time() - start_time,
                            "oracle_response_preview": oracle_response[:300] + "..." if len(oracle_response) > 300 else oracle_response
                        }
                        logger.info("✅ Async operation started - Oracle recognized async mode")
                    else:
                        result = {
                            "test_name": "async_operation_start",
                            "status": "partial",
                            "oracle_async_recognition": False,
                            "response_time": time.time() - start_time,
                            "oracle_response_preview": oracle_response[:300] + "..." if len(oracle_response) > 300 else oracle_response
                        }
                        logger.warning("⚠️  Async operation may have started but Oracle didn't clearly recognize it")
                else:
                    result = {
                        "test_name": "async_operation_start",
                        "status": "failed",
                        "error": f"HTTP {response.status}",
                        "response_time": time.time() - start_time
                    }
                    logger.error(f"❌ Async operation start failed with status {response.status}")
                
                results.append(result)
                
        except Exception as e:
            results.append({
                "test_name": "async_operation_start",
                "status": "error",
                "error": str(e),
                "response_time": time.time() - start_time
            })
            logger.error(f"❌ Async operation test failed: {e}")
        
        # Test operation listing
        try:
            list_ops_payload = {
                "message": "List all current operations and their status",
                "user_id": "test_list_ops",
                "function_calls": [{
                    "name": "list_operations",
                    "arguments": {
                        "status_filter": "all",
                        "response_format": "json"
                    }
                }]
            }
            
            start_time = time.time()
            logger.info("📋 Testing operation listing...")
            
            async with session.post(
                f"{self.conductor_url}/api/v1/chat",
                json=list_ops_payload,
                timeout=10
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    oracle_response = data.get('response', '')
                    
                    if "operations" in oracle_response.lower() or "status" in oracle_response.lower():
                        result = {
                            "test_name": "list_operations",
                            "status": "success",
                            "oracle_ops_recognition": True,
                            "response_time": time.time() - start_time,
                            "oracle_response_preview": oracle_response[:300] + "..." if len(oracle_response) > 300 else oracle_response
                        }
                        logger.info("✅ Operation listing successful - Oracle processed operations data")
                    else:
                        result = {
                            "test_name": "list_operations",
                            "status": "partial",
                            "oracle_ops_recognition": False,
                            "response_time": time.time() - start_time
                        }
                        logger.warning("⚠️  Operation listing may have worked but Oracle didn't recognize operations data")
                else:
                    result = {
                        "test_name": "list_operations",
                        "status": "failed",
                        "error": f"HTTP {response.status}",
                        "response_time": time.time() - start_time
                    }
                    logger.error(f"❌ Operation listing failed with status {response.status}")
                
                results.append(result)
                
        except Exception as e:
            results.append({
                "test_name": "list_operations",
                "status": "error",
                "error": str(e),
                "response_time": time.time() - start_time
            })
            logger.error(f"❌ Operation listing test failed: {e}")
        
        return {
            "category": "async_operations",
            "tests": results,
            "summary": {
                "total": len(results),
                "successful": len([r for r in results if r["status"] == "success"]),
                "oracle_async_understanding": len([r for r in results if r.get("oracle_async_recognition", False) or r.get("oracle_ops_recognition", False)]) / len(results) * 100
            }
        }
    
    async def test_enhanced_tooling(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test the new enhanced tools (search_logs, get_config)"""
        logger.info("🔧 Testing Enhanced Tooling")
        
        test_cases = [
            {
                "name": "search_logs_functionality",
                "payload": {
                    "message": "Search for errors in the system logs",
                    "user_id": "test_search_logs",
                    "function_calls": [{
                        "name": "search_logs",
                        "arguments": {
                            "keyword": "error",
                            "severity": "error",
                            "time_range": "last_day",
                            "max_results": 10,
                            "response_format": "json"
                        }
                    }]
                },
                "expected_capability": "log_search"
            },
            {
                "name": "get_config_granular",
                "payload": {
                    "message": "Get the MCP protocol version configuration",
                    "user_id": "test_get_config",
                    "function_calls": [{
                        "name": "get_config",
                        "arguments": {
                            "parameter": "mcp.protocol_version",
                            "include_metadata": True,
                            "response_format": "json"
                        }
                    }]
                },
                "expected_capability": "config_access"
            },
            {
                "name": "get_config_partial_match",
                "payload": {
                    "message": "Find all sentinel-related configuration parameters",
                    "user_id": "test_config_partial",
                    "function_calls": [{
                        "name": "get_config",
                        "arguments": {
                            "parameter": "sentinel",
                            "component": "system",
                            "response_format": "json"
                        }
                    }]
                },
                "expected_capability": "config_search"
            }
        ]
        
        results = []
        for test_case in test_cases:
            try:
                start_time = time.time()
                async with session.post(
                    f"{self.conductor_url}/api/v1/chat",
                    json=test_case["payload"],
                    timeout=15
                ) as response:
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        oracle_response = data.get('response', '')
                        
                        # Check if Oracle understood and used the enhanced tool
                        capability_indicators = {
                            "log_search": ["log", "search", "error", "found"],
                            "config_access": ["config", "version", "protocol", "parameter"],
                            "config_search": ["sentinel", "configuration", "parameters", "matches"]
                        }
                        
                        expected_cap = test_case["expected_capability"]
                        indicators_found = sum(1 for indicator in capability_indicators[expected_cap] 
                                             if indicator.lower() in oracle_response.lower())
                        
                        result = {
                            "test_name": test_case["name"],
                            "status": "success",
                            "response_time": response_time,
                            "expected_capability": expected_cap,
                            "capability_indicators_found": indicators_found,
                            "capability_recognition_score": indicators_found / len(capability_indicators[expected_cap]) * 100,
                            "oracle_response_preview": oracle_response[:250] + "..." if len(oracle_response) > 250 else oracle_response
                        }
                        
                        if indicators_found >= 2:
                            logger.info(f"✅ {test_case['name']} - Oracle effectively used enhanced tool")
                        else:
                            logger.warning(f"⚠️  {test_case['name']} - Oracle may not have fully utilized enhanced tool")
                    else:
                        result = {
                            "test_name": test_case["name"],
                            "status": "failed",
                            "error": f"HTTP {response.status}",
                            "response_time": response_time
                        }
                        logger.error(f"❌ {test_case['name']} failed with status {response.status}")
                        
            except Exception as e:
                result = {
                    "test_name": test_case["name"],
                    "status": "error",
                    "error": str(e),
                    "response_time": time.time() - start_time
                }
                logger.error(f"❌ {test_case['name']} failed with error: {e}")
            
            results.append(result)
            await asyncio.sleep(1)
        
        return {
            "category": "enhanced_tooling",
            "tests": results,
            "summary": {
                "total": len(results),
                "successful": len([r for r in results if r["status"] == "success"]),
                "average_capability_recognition": sum(r.get("capability_recognition_score", 0) for r in results) / len(results) if results else 0
            }
        }
    
    async def test_performance_improvements(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test performance improvements with Oracle"""
        logger.info("⚡ Testing Performance Improvements")
        
        # Test response time with structured JSON vs text
        json_payload = {
            "message": "Perform a comprehensive system health check with JSON format",
            "user_id": "test_json_performance",
            "function_calls": [{
                "name": "system_health",
                "arguments": {
                    "component": "all",
                    "detail_level": "diagnostic",
                    "include_logs": True,
                    "response_format": "json"
                }
            }]
        }
        
        text_payload = {
            "message": "Perform a comprehensive system health check with text format",
            "user_id": "test_text_performance",
            "function_calls": [{
                "name": "system_health",
                "arguments": {
                    "component": "all",
                    "detail_level": "diagnostic",
                    "include_logs": True,
                    "response_format": "text"
                }
            }]
        }
        
        results = []
        
        # Test JSON format performance
        try:
            start_time = time.time()
            async with session.post(
                f"{self.conductor_url}/api/v1/chat",
                json=json_payload,
                timeout=20
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    json_response_time = time.time() - start_time
                    
                    results.append({
                        "test_name": "json_format_performance",
                        "status": "success",
                        "response_time": json_response_time,
                        "format": "json",
                        "response_length": len(data.get('response', ''))
                    })
                    logger.info(f"✅ JSON format test completed in {json_response_time:.2f}s")
                else:
                    results.append({
                        "test_name": "json_format_performance",
                        "status": "failed",
                        "error": f"HTTP {response.status}",
                        "format": "json"
                    })
        except Exception as e:
            results.append({
                "test_name": "json_format_performance",
                "status": "error",
                "error": str(e),
                "format": "json"
            })
        
        await asyncio.sleep(2)  # Brief pause between performance tests
        
        # Test text format performance
        try:
            start_time = time.time()
            async with session.post(
                f"{self.conductor_url}/api/v1/chat",
                json=text_payload,
                timeout=20
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    text_response_time = time.time() - start_time
                    
                    results.append({
                        "test_name": "text_format_performance",
                        "status": "success",
                        "response_time": text_response_time,
                        "format": "text",
                        "response_length": len(data.get('response', ''))
                    })
                    logger.info(f"✅ Text format test completed in {text_response_time:.2f}s")
                else:
                    results.append({
                        "test_name": "text_format_performance",
                        "status": "failed",
                        "error": f"HTTP {response.status}",
                        "format": "text"
                    })
        except Exception as e:
            results.append({
                "test_name": "text_format_performance",
                "status": "error",
                "error": str(e),
                "format": "text"
            })
        
        # Calculate performance comparison
        json_times = [r["response_time"] for r in results if r.get("format") == "json" and r["status"] == "success"]
        text_times = [r["response_time"] for r in results if r.get("format") == "text" and r["status"] == "success"]
        
        performance_improvement = None
        if json_times and text_times:
            avg_json_time = sum(json_times) / len(json_times)
            avg_text_time = sum(text_times) / len(text_times)
            performance_improvement = ((avg_text_time - avg_json_time) / avg_text_time) * 100
        
        return {
            "category": "performance_improvements",
            "tests": results,
            "summary": {
                "total": len(results),
                "successful": len([r for r in results if r["status"] == "success"]),
                "average_json_time": sum(json_times) / len(json_times) if json_times else None,
                "average_text_time": sum(text_times) / len(text_times) if text_times else None,
                "performance_improvement_percent": performance_improvement
            }
        }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all MCP improvement tests"""
        logger.info("🚀 Starting Comprehensive MCP Improvement Test Suite")
        
        async with aiohttp.ClientSession() as session:
            # Check basic connectivity
            try:
                async with session.get(f"{self.conductor_url}/health", timeout=5) as response:
                    if response.status != 200:
                        logger.error("❌ Conductor service not healthy")
                        return {"status": "aborted", "error": "Conductor service not healthy"}
            except Exception as e:
                logger.error(f"❌ Cannot connect to Conductor: {e}")
                return {"status": "aborted", "error": f"Cannot connect to Conductor: {e}"}
            
            # Run all test categories
            test_results = {}
            
            test_results["structured_json"] = await self.test_structured_json_responses(session)
            await asyncio.sleep(2)
            
            test_results["async_operations"] = await self.test_async_operations(session)
            await asyncio.sleep(2)
            
            test_results["enhanced_tooling"] = await self.test_enhanced_tooling(session)
            await asyncio.sleep(2)
            
            test_results["performance"] = await self.test_performance_improvements(session)
            
            # Compile overall results
            overall_results = {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "test_categories": test_results,
                "overall_summary": self._compile_overall_summary(test_results)
            }
            
            return overall_results
    
    def _compile_overall_summary(self, test_results: Dict[str, Any]) -> Dict[str, Any]:
        """Compile overall test summary"""
        total_tests = sum(tr["summary"]["total"] for tr in test_results.values())
        total_successful = sum(tr["summary"]["successful"] for tr in test_results.values())
        success_rate = (total_successful / total_tests * 100) if total_tests > 0 else 0
        
        return {
            "total_tests": total_tests,
            "successful_tests": total_successful,
            "overall_success_rate": success_rate,
            "oracle_improvements_validated": success_rate >= 75,
            "performance_improvement": test_results.get("performance", {}).get("summary", {}).get("performance_improvement_percent"),
            "ready_for_production": success_rate >= 80
        }
    
    def print_summary(self, results: Dict[str, Any]):
        """Print comprehensive test summary"""
        print("\n" + "="*70)
        print("🎯 MCP SERVER IMPROVEMENTS TEST SUMMARY")
        print("="*70)
        
        if results["status"] == "aborted":
            print("❌ Tests were aborted:", results.get("error", "Unknown error"))
            return
        
        overall = results["overall_summary"]
        
        print(f"\n📊 Overall Results:")
        print(f"   Total Tests: {overall['total_tests']}")
        print(f"   Successful: {overall['successful_tests']}")
        print(f"   Success Rate: {overall['overall_success_rate']:.1f}%")
        
        print(f"\n🔧 Category Results:")
        for category, data in results["test_categories"].items():
            summary = data["summary"]
            success_rate = (summary["successful"] / summary["total"] * 100) if summary["total"] > 0 else 0
            status_emoji = "✅" if success_rate >= 75 else "⚠️" if success_rate >= 50 else "❌"
            print(f"   {status_emoji} {category.replace('_', ' ').title()}: {success_rate:.1f}% ({summary['successful']}/{summary['total']})")
        
        if overall.get("performance_improvement"):
            print(f"\n⚡ Performance Improvement: {overall['performance_improvement']:.1f}%")
        
        print(f"\n🧠 Oracle Integration Assessment:")
        oracle_validated = overall['oracle_improvements_validated']
        oracle_emoji = "✅" if oracle_validated else "⚠️"
        print(f"   {oracle_emoji} Oracle Improvements Validated: {'Yes' if oracle_validated else 'Needs Review'}")
        
        production_ready = overall['ready_for_production']
        prod_emoji = "🚀" if production_ready else "🔧"
        print(f"   {prod_emoji} Production Ready: {'Yes' if production_ready else 'Needs Work'}")
        
        print("\n" + "="*70)

async def main():
    """Main test runner"""
    tester = MCPImprovementTester()
    
    try:
        results = await tester.run_comprehensive_test()
        
        # Save results to file
        with open('mcp_improvement_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        tester.print_summary(results)
        
        # Exit with appropriate code
        if results.get("overall_summary", {}).get("ready_for_production", False):
            logger.info("🎉 All MCP improvements validated successfully!")
            sys.exit(0)
        else:
            logger.warning("⚠️  Some improvements need attention")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Test suite failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())