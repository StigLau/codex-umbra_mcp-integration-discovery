#!/usr/bin/env python3
"""
Comprehensive Natural Language Integration Test for Codex Umbra
Tests the full pipeline from frontend to backend with realistic natural language queries
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any
import aiohttp
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CodexUmbraTestSuite:
    def __init__(self):
        self.conductor_url = "http://localhost:8000"
        self.sentinel_url = "http://localhost:8001"
        self.frontend_url = "http://localhost:5173"
        self.results = []
        
    async def check_service_health(self, session: aiohttp.ClientSession) -> Dict[str, bool]:
        """Check if all services are running"""
        services = {
            'conductor': f"{self.conductor_url}/health",
            'sentinel': f"{self.conductor_url}/api/v1/sentinel/health",
        }
        
        health_status = {}
        for service, url in services.items():
            try:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        health_status[service] = data.get('status') == 'healthy'
                        logger.info(f"✅ {service.title()} service is healthy")
                    else:
                        health_status[service] = False
                        logger.error(f"❌ {service.title()} service returned {response.status}")
            except Exception as e:
                health_status[service] = False
                logger.error(f"❌ {service.title()} service is not accessible: {e}")
        
        return health_status
    
    async def test_natural_language_queries(self, session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
        """Test various natural language queries"""
        test_queries = [
            {
                "query": "Hello, can you help me understand what this system does?",
                "expected_keywords": ["system", "help", "codex", "umbra"],
                "category": "introduction"
            },
            {
                "query": "What is the weather like today?",
                "expected_keywords": ["weather", "today", "temperature"],
                "category": "general_query"
            },
            {
                "query": "Can you solve this math problem: what is 15 + 27?",
                "expected_keywords": ["42", "math", "addition"],
                "category": "calculation"
            },
            {
                "query": "Tell me a short joke about programming",
                "expected_keywords": ["programming", "code", "joke"],
                "category": "creative"
            },
            {
                "query": "Explain quantum computing in simple terms",
                "expected_keywords": ["quantum", "computing", "simple"],
                "category": "educational"
            },
            {
                "query": "What are the main components of this Codex Umbra system?",
                "expected_keywords": ["conductor", "sentinel", "oracle", "visage"],
                "category": "system_specific"
            }
        ]
        
        results = []
        for i, test_case in enumerate(test_queries):
            logger.info(f"Testing query {i+1}/{len(test_queries)}: {test_case['category']}")
            
            start_time = time.time()
            try:
                payload = {
                    "message": test_case["query"],
                    "user_id": f"test_user_{i}"
                }
                
                async with session.post(
                    f"{self.conductor_url}/api/v1/chat",
                    json=payload,
                    timeout=30
                ) as response:
                    end_time = time.time()
                    response_time = end_time - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        response_text = data.get('response', '').lower()
                        
                        # Check for expected keywords
                        keywords_found = [
                            keyword for keyword in test_case["expected_keywords"]
                            if keyword.lower() in response_text
                        ]
                        
                        result = {
                            "query": test_case["query"],
                            "category": test_case["category"],
                            "status": "success",
                            "response_time": response_time,
                            "response_length": len(data.get('response', '')),
                            "keywords_found": keywords_found,
                            "keywords_expected": test_case["expected_keywords"],
                            "response_preview": data.get('response', '')[:200] + "..." if len(data.get('response', '')) > 200 else data.get('response', '')
                        }
                        
                        if keywords_found:
                            logger.info(f"✅ Query successful - found keywords: {keywords_found}")
                        else:
                            logger.warning(f"⚠️  Query successful but no expected keywords found")
                            
                    else:
                        result = {
                            "query": test_case["query"],
                            "category": test_case["category"],
                            "status": "failed",
                            "error": f"HTTP {response.status}",
                            "response_time": response_time
                        }
                        logger.error(f"❌ Query failed with status {response.status}")
                        
            except asyncio.TimeoutError:
                result = {
                    "query": test_case["query"],
                    "category": test_case["category"],
                    "status": "timeout",
                    "response_time": 30.0
                }
                logger.error(f"❌ Query timed out after 30 seconds")
                
            except Exception as e:
                result = {
                    "query": test_case["query"],
                    "category": test_case["category"],
                    "status": "error",
                    "error": str(e),
                    "response_time": time.time() - start_time
                }
                logger.error(f"❌ Query failed with error: {e}")
            
            results.append(result)
            
            # Brief pause between queries
            await asyncio.sleep(1)
        
        return results
    
    async def test_llm_providers(self, session: aiohttp.ClientSession) -> Dict[str, Any]:
        """Test available LLM providers"""
        try:
            async with session.get(f"{self.conductor_url}/api/v1/llm/providers", timeout=10) as response:
                if response.status == 200:
                    providers = await response.json()
                    logger.info(f"✅ Available LLM providers: {providers}")
                    return {"status": "success", "providers": providers}
                else:
                    logger.error(f"❌ Failed to get LLM providers: {response.status}")
                    return {"status": "failed", "error": f"HTTP {response.status}"}
        except Exception as e:
            logger.error(f"❌ Error getting LLM providers: {e}")
            return {"status": "error", "error": str(e)}
    
    async def run_full_test_suite(self) -> Dict[str, Any]:
        """Run the complete test suite"""
        logger.info("🚀 Starting Codex Umbra Natural Language Integration Test Suite")
        
        async with aiohttp.ClientSession() as session:
            # Check service health
            logger.info("📋 Checking service health...")
            health_status = await self.check_service_health(session)
            
            if not all(health_status.values()):
                logger.error("❌ Not all services are healthy. Aborting tests.")
                return {
                    "status": "aborted",
                    "health_status": health_status,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Test LLM providers
            logger.info("🔍 Testing LLM providers...")
            provider_test = await self.test_llm_providers(session)
            
            # Test natural language queries
            logger.info("💬 Testing natural language queries...")
            query_results = await self.test_natural_language_queries(session)
            
            # Compile results
            successful_queries = [r for r in query_results if r["status"] == "success"]
            failed_queries = [r for r in query_results if r["status"] != "success"]
            
            avg_response_time = sum(r.get("response_time", 0) for r in successful_queries) / len(successful_queries) if successful_queries else 0
            
            final_results = {
                "status": "completed",
                "timestamp": datetime.now().isoformat(),
                "health_status": health_status,
                "provider_test": provider_test,
                "query_results": {
                    "total": len(query_results),
                    "successful": len(successful_queries),
                    "failed": len(failed_queries),
                    "success_rate": len(successful_queries) / len(query_results) * 100 if query_results else 0,
                    "average_response_time": avg_response_time
                },
                "detailed_results": query_results
            }
            
            return final_results
    
    def print_summary(self, results: Dict[str, Any]):
        """Print a summary of test results"""
        print("\n" + "="*60)
        print("🎯 CODEX UMBRA TEST SUMMARY")
        print("="*60)
        
        if results["status"] == "aborted":
            print("❌ Tests were aborted due to service health issues")
            return
        
        # Health status
        print(f"🏥 Service Health:")
        for service, healthy in results["health_status"].items():
            status = "✅ Healthy" if healthy else "❌ Unhealthy"
            print(f"   {service.title()}: {status}")
        
        # Provider test
        print(f"\n🔧 LLM Provider Test:")
        provider_status = results["provider_test"]["status"]
        if provider_status == "success":
            providers = results["provider_test"]["providers"]
            print(f"   ✅ Available providers: {providers}")
        else:
            print(f"   ❌ Failed: {results['provider_test'].get('error', 'Unknown error')}")
        
        # Query results
        query_results = results["query_results"]
        print(f"\n💬 Natural Language Query Results:")
        print(f"   Total queries: {query_results['total']}")
        print(f"   Successful: {query_results['successful']}")
        print(f"   Failed: {query_results['failed']}")
        print(f"   Success rate: {query_results['success_rate']:.1f}%")
        print(f"   Average response time: {query_results['average_response_time']:.2f}s")
        
        # Detailed results
        print(f"\n📊 Detailed Query Results:")
        for result in results["detailed_results"]:
            status_emoji = "✅" if result["status"] == "success" else "❌"
            print(f"   {status_emoji} {result['category']}: {result['query'][:50]}...")
            if result["status"] == "success":
                print(f"      Response time: {result['response_time']:.2f}s")
                print(f"      Keywords found: {result['keywords_found']}")
        
        # Overall assessment
        success_rate = query_results['success_rate']
        if success_rate >= 80:
            print(f"\n🎉 OVERALL: EXCELLENT - {success_rate:.1f}% success rate")
        elif success_rate >= 60:
            print(f"\n👍 OVERALL: GOOD - {success_rate:.1f}% success rate")
        elif success_rate >= 40:
            print(f"\n⚠️  OVERALL: NEEDS IMPROVEMENT - {success_rate:.1f}% success rate")
        else:
            print(f"\n❌ OVERALL: POOR - {success_rate:.1f}% success rate")
        
        print("="*60)

async def main():
    """Main test runner"""
    test_suite = CodexUmbraTestSuite()
    
    try:
        results = await test_suite.run_full_test_suite()
        
        # Save results to file
        with open('test_results_natural_language.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Print summary
        test_suite.print_summary(results)
        
        # Exit with appropriate code
        if results["status"] == "completed" and results["query_results"]["success_rate"] >= 80:
            logger.info("🎉 All tests passed successfully!")
            sys.exit(0)
        else:
            logger.warning("⚠️  Some tests failed or didn't meet success criteria")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Test suite failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())