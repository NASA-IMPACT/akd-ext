"""
CMR Care Agent Test Script

This script tests the CMR Care Agent implementation to verify it works correctly
with the OpenAI Agent Builder SDK.
"""

import asyncio
import os
from akd_ext.agents.cmr_care_agent import (
    CMRCareAgent,
    CMRCareAgentConfig,
    CMRCareInputSchema,
    CMRCareOutputSchema
)


async def test_agent():
    """Run comprehensive tests on the CMR Care Agent."""
    
    print("="*80)
    print("CMR CARE AGENT TEST SUITE")
    print("="*80)
    
    # Check API key
    if 'OPENAI_API_KEY' not in os.environ:
        print("\nWarning: OPENAI_API_KEY not found in environment variables")
        print("Please set it using: export OPENAI_API_KEY='your-api-key'")
        return
    else:
        print("\nOpenAI API key is set")
    
    # Initialize agent
    print("\n" + "-"*80)
    print("INITIALIZING AGENT")
    print("-"*80)
    
    config = CMRCareAgentConfig()
    agent = CMRCareAgent(config=config, debug=True)
    print("CMR Care Agent initialized successfully")
    
    # Test cases
    test_cases = [
        {
            "name": "Sea Surface Temperature",
            "query": "Find datasets related to sea surface temperature in the Pacific Ocean"
        },
        {
            "name": "Atmospheric CO2",
            "query": "Find atmospheric CO2 concentration datasets from satellite observations"
        },
        {
            "name": "MODIS Vegetation",
            "query": "Find MODIS vegetation index datasets for monitoring forest health"
        }
    ]
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print("\n" + "="*80)
        print(f"TEST CASE {i}: {test_case['name']}")
        print("="*80)
        print(f"Query: {test_case['query']}")
        print("\nRunning agent...")
        
        try:
            # Create input
            test_input = CMRCareInputSchema(input_as_text=test_case['query'])
            
            # Run agent
            result = await agent.arun(test_input)

            # Display results
            print("\n" + "-"*80)
            print("RESULTS")
            print("-"*80)
            print(f"\nFound {len(result.dataset_concept_ids)} dataset(s):\n")
            
            for j, concept_id in enumerate(result.dataset_concept_ids, 1):
                print(f"{j}. {concept_id}")
            
            # Display report
            print("\n" + "-"*80)
            print("REPORT")
            print("-"*80)
            print(result.report)

            results.append({
                "test_case": test_case['name'],
                "success": True,
                "count": len(result.dataset_concept_ids),
                "result": result
            })
            
        except Exception as e:
            print(f"\nError: {str(e)}")
            results.append({
                "test_case": test_case['name'],
                "success": False,
                "error": str(e)
            })
    
    # Validation
    print("\n" + "="*80)
    print("VALIDATION TESTS")
    print("="*80)
    
    if results and results[0]["success"]:
        result_obj = results[0]["result"]
        print(f"Result is CMRCareOutputSchema: {isinstance(result_obj, CMRCareOutputSchema)}")
        print(f"dataset_concept_ids is list: {isinstance(result_obj.dataset_concept_ids, list)}")
        print(f"All items are strings: {all(isinstance(id, str) for id in result_obj.dataset_concept_ids)}")
        
        if result_obj.dataset_concept_ids:
            valid_format = all(id.startswith('C') and '-' in id for id in result_obj.dataset_concept_ids)
            print(f"✓ Concept IDs have valid format: {valid_format}")
            print(f"\nExample Concept ID: {result_obj.dataset_concept_ids[0]}")
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    total_datasets = 0
    for result in results:
        if result["success"]:
            print(f"\n{result['test_case']}: {result['count']} datasets")
            total_datasets += result['count']
        else:
            print(f"\n{result['test_case']}: Failed - {result.get('error', 'Unknown error')}")
    
    print(f"\nTotal datasets found: {total_datasets}")
    
    successful_tests = sum(1 for r in results if r["success"])
    print(f"\nTests passed: {successful_tests}/{len(results)}")
    
    if successful_tests == len(results):
        print("\nAll tests completed successfully!")
    else:
        print(f"\n{len(results) - successful_tests} test(s) failed")


if __name__ == "__main__":
    asyncio.run(test_agent())
