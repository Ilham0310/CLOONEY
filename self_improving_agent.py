"""
Self-Improving Agent Loop
Iteratively refines API specs, models, and tests based on comparison with expected specs
derived from captured network traffic.
"""

import json
import os
from typing import Dict, Any, List
from network_parser import NetworkParser
from openapi_generator import OpenAPIGenerator
from schema_generator import SchemaGenerator
from fastapi_generator import FastAPIGenerator
from test_generator import TestGenerator
from refinement_engine import RefinementEngine
from datetime import datetime
import httpx
from fastapi.testclient import TestClient


class SelfImprovingAgent:
    """Agent that iteratively improves API clone based on expected vs actual comparison."""
    
    def __init__(
        self,
        network_capture_path: str = "network_capture.json",
        max_iterations: int = 10,
        quality_threshold: float = 0.95,
        clone_api_base: str = "http://localhost:8000"
    ):
        self.network_capture_path = network_capture_path
        self.max_iterations = max_iterations
        self.quality_threshold = quality_threshold
        self.clone_api_base = clone_api_base
        self.iteration = 0
        self.history: List[Dict[str, Any]] = []
        self.refinement_engine = RefinementEngine()
    
    def _test_clone_endpoint(
        self, 
        method: str, 
        path: str, 
        json_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Test a single endpoint on the clone API."""
        try:
            # Try to use TestClient if FastAPI app is importable
            try:
                from fastapi_app.main import app
                client = TestClient(app)
                
                if method.upper() == "GET":
                    response = client.get(path)
                elif method.upper() == "POST":
                    response = client.post(path, json=json_data or {})
                elif method.upper() == "PUT":
                    response = client.put(path, json=json_data or {})
                elif method.upper() == "DELETE":
                    response = client.delete(path)
                else:
                    return {"error": f"Unsupported method: {method}"}
                
                return {
                    "status_code": response.status_code,
                    "body": response.json() if response.status_code < 400 else response.text
                }
            except ImportError:
                # Fallback to HTTP client if app not importable
                with httpx.Client(timeout=5.0) as client:
                    if method.upper() == "GET":
                        response = client.get(f"{self.clone_api_base}{path}")
                    elif method.upper() == "POST":
                        response = client.post(f"{self.clone_api_base}{path}", json=json_data or {})
                    elif method.upper() == "PUT":
                        response = client.put(f"{self.clone_api_base}{path}", json=json_data or {})
                    elif method.upper() == "DELETE":
                        response = client.delete(f"{self.clone_api_base}{path}")
                    else:
                        return {"error": f"Unsupported method: {method}"}
                    
                    return {
                        "status_code": response.status_code,
                        "body": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text
                    }
        except Exception as e:
            return {"error": str(e), "status_code": 0}
    
    def _calculate_quality_score(
        self, 
        expected: Dict[str, Any], 
        actual: Dict[str, Any]
    ) -> float:
        """Calculate quality score (0-1) based on how well actual matches expected."""
        if not isinstance(expected, dict) or not isinstance(actual, dict):
            return 0.0
        
        differences = self.refinement_engine._compare_responses(expected, actual)
        
        if not differences:
            return 1.0
        
        # Count differences
        total_diffs = 0
        for key, value in differences.items():
            if isinstance(value, (list, dict)):
                total_diffs += len(value) if isinstance(value, list) else len(value.keys())
            else:
                total_diffs += 1
        
        # Count total expected fields
        def count_fields(obj):
            if isinstance(obj, dict):
                return sum(1 + count_fields(v) for v in obj.values())
            elif isinstance(value, list):
                return sum(count_fields(item) for item in obj)
            return 1
        
        total_fields = count_fields(expected)
        if total_fields == 0:
            return 1.0
        
        quality = max(0.0, 1.0 - (total_diffs / max(total_fields, 1)))
        return quality
    
    async def run_iteration(self) -> Dict[str, Any]:
        """Run one iteration of the improvement loop."""
        self.iteration += 1
        print(f"\n{'='*60}")
        print(f"Iteration {self.iteration}/{self.max_iterations}")
        print(f"{'='*60}\n")
        
        iteration_result = {
            'iteration': self.iteration,
            'timestamp': datetime.utcnow().isoformat(),
            'steps': {}
        }
        
        # Step 1: Load or parse network data
        print("Step 1: Loading parsed data...")
        if os.path.exists('parsed_endpoints.json'):
            with open('parsed_endpoints.json', 'r') as f:
                parsed_data = json.load(f)
        else:
            print("  Parsing network capture...")
            # Try to use AI-enhanced parser if available
            try:
                from ai_enhanced_parser import AIEnhancedParser
                parser = AIEnhancedParser(self.network_capture_path)
                print("  Using AI-enhanced parser (if AI is enabled)")
            except ImportError:
                parser = NetworkParser(self.network_capture_path)
                print("  Using standard parser")
            
            parsed_data = parser.analyze()
            with open('parsed_endpoints.json', 'w') as f:
                json.dump(parsed_data, f, indent=2)
        
        iteration_result['steps']['parsing'] = {
            'endpoints_found': len(parsed_data.get('endpoints', {}))
        }
        
        # Step 2: Generate artifacts
        print("\nStep 2: Generating artifacts...")
        try:
            # Generate OpenAPI spec
            openapi_gen = OpenAPIGenerator(parsed_data)
            openapi_gen.save('api.yml')
            
            # Generate SQL schema
            schema_gen = SchemaGenerator(parsed_data)
            schema_gen.save('schema.sql')
            
            # Generate FastAPI code
            fastapi_gen = FastAPIGenerator(parsed_data)
            fastapi_gen.save('fastapi_app')
            
            iteration_result['steps']['generation'] = {'success': True}
        except Exception as e:
            iteration_result['steps']['generation'] = {'error': str(e)}
            return iteration_result
        
        # Step 3: Extract expected specs and test clone
        print("\nStep 3: Comparing clone with expected specs...")
        try:
            # Extract expected response schemas from captured data
            expected_responses = self.refinement_engine.extract_expected_from_capture(parsed_data)
            print(f"  Found {len(expected_responses)} expected response schemas")
            
            # Test clone endpoints
            actual_responses = {}
            quality_scores = []
            
            # Test a sample of endpoints - try both captured endpoints and CRUD endpoints
            test_endpoints = [
                {"name": "list_workspaces", "method": "GET", "path": "/api/1.0/workspaces"},
                {"name": "list_projects", "method": "GET", "path": "/api/1.0/projects"},
                {"name": "list_tasks", "method": "GET", "path": "/api/1.0/tasks"},
            ]
            
            # Also try testing some endpoints from the parsed data
            parsed_endpoint_keys = list(parsed_data.get('endpoints', {}).keys())[:3]
            for ep_key in parsed_endpoint_keys:
                ep_info = parsed_data['endpoints'][ep_key]
                methods = ep_info.get('methods', [])
                if methods:
                    method = list(methods)[0] if isinstance(methods, (list, set)) else methods[0] if isinstance(methods, dict) else 'GET'
                    path = ep_info.get('path', ep_key)
                    test_endpoints.append({
                        "name": ep_key.replace(' ', '_').replace('/', '_'),
                        "method": method,
                        "path": path
                    })
            
            print(f"  Testing {len(test_endpoints)} endpoints...")
            tested_count = 0
            
            for test_case in test_endpoints:
                endpoint_name = test_case["name"]
                expected = expected_responses.get(test_case["path"], {})
                
                if expected:
                    actual = self._test_clone_endpoint(
                        test_case["method"], 
                        test_case["path"]
                    )
                    
                    if "error" not in actual and "body" in actual:
                        actual_responses[endpoint_name] = actual.get("body", {})
                        
                        # Calculate quality score
                        quality = self._calculate_quality_score(expected, actual.get("body", {}))
                        quality_scores.append(quality)
                        tested_count += 1
                else:
                    # Try testing the endpoint anyway to see if it exists
                    actual = self._test_clone_endpoint(
                        test_case["method"], 
                        test_case["path"]
                    )
                    if "error" not in actual and "body" in actual:
                        # Endpoint exists but no expected response - give it a default quality
                        quality_scores.append(0.5)  # Partial credit for existing
                        tested_count += 1
            
            print(f"  Successfully tested {tested_count} endpoints")
            avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.0
            print(f"  Average quality score: {avg_quality:.2%}")
            
            iteration_result['steps']['testing'] = {
                'endpoints_tested': len(actual_responses),
                'average_quality': avg_quality,
                'quality_scores': quality_scores
            }
            
            # Step 4: Analyze and refine
            if avg_quality < self.quality_threshold:
                print("\nStep 4: Analyzing differences and generating improvements...")
                suggestions = self.refinement_engine.analyze_differences(
                    expected_responses, 
                    actual_responses
                )
                patches = self.refinement_engine.generate_schema_patches(suggestions)
                
                iteration_result['steps']['refinement'] = {
                    'suggestions_count': len(suggestions),
                    'patches_generated': len(patches.get('openapi_changes', []))
                }
                
                # Apply patches to parsed_data for next iteration
                if patches.get('openapi_changes'):
                    parsed_data = self.refinement_engine.apply_patches(patches, parsed_data)
                    with open('parsed_endpoints.json', 'w') as f:
                        json.dump(parsed_data, f, indent=2)
                    print(f"  Applied {len(patches['openapi_changes'])} patches")
            else:
                iteration_result['steps']['refinement'] = {'skipped': 'threshold_met'}
                iteration_result['converged'] = True
                print(f"\n✓ Target quality threshold ({self.quality_threshold}) reached!")
                return iteration_result
            
        except Exception as e:
            print(f"Error in testing/refinement: {e}")
            import traceback
            traceback.print_exc()
            iteration_result['steps']['testing'] = {'error': str(e)}
        
        iteration_result['converged'] = False
        return iteration_result
    
    async def run(self) -> Dict[str, Any]:
        """Run the complete improvement loop."""
        print("="*60)
        print("SELF-IMPROVING AGENT - Starting Improvement Loop")
        print("="*60)
        
        for i in range(self.max_iterations):
            result = await self.run_iteration()
            self.history.append(result)
            
            if result.get('converged', False):
                print(f"\n✓ Converged after {self.iteration} iterations!")
                break
            
            # Wait a bit before next iteration
            if i < self.max_iterations - 1:
                print("\nWaiting before next iteration...")
                import asyncio
                await asyncio.sleep(2)
        
        # Generate final report
        final_report = self._generate_final_report()
        
        # Save history
        with open('agent_history.json', 'w') as f:
            json.dump({
                'history': self.history,
                'final_report': final_report
            }, f, indent=2, default=str)
        
        return final_report
    
    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate final report from all iterations."""
        if not self.history:
            return {"error": "No iterations completed"}
        
        final_iteration = self.history[-1]
        testing = final_iteration.get('steps', {}).get('testing', {})
        
        return {
            'total_iterations': len(self.history),
            'converged': final_iteration.get('converged', False),
            'final_quality': testing.get('average_quality', 0),
            'improvement_trajectory': [
                {
                    'iteration': h['iteration'],
                    'quality': h.get('steps', {}).get('testing', {}).get('average_quality', 0)
                }
                for h in self.history
                if 'testing' in h.get('steps', {})
            ]
        }


async def main():
    """Example usage."""
    agent = SelfImprovingAgent(
        network_capture_path="network_capture.json",
        max_iterations=5,
        quality_threshold=0.90
    )
    
    final_report = await agent.run()
    print("\n" + "="*60)
    print("FINAL REPORT")
    print("="*60)
    print(json.dumps(final_report, indent=2))


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
