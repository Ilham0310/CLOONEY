#!/usr/bin/env python3
"""
Complete Pipeline Runner
Runs the entire Clooney pipeline: capture -> parse -> generate -> test -> improve
"""

import argparse
import asyncio
import sys
from pathlib import Path

from network_parser import NetworkParser
from openapi_generator import OpenAPIGenerator
from schema_generator import SchemaGenerator
from fastapi_generator import FastAPIGenerator
from test_generator import TestGenerator
from self_improving_agent import SelfImprovingAgent


async def run_pipeline(
    network_capture: str = "network_capture.json",
    mode: str = "all",
    max_iterations: int = 5,
    quality_threshold: float = 0.95
):
    """Run the complete pipeline."""
    
    print("="*80)
    print("CLOONEY PROJECT - Complete Pipeline")
    print("="*80)
    print()
    
    if mode in ["parse", "all"]:
        print("STEP 1: Parsing Network Capture")
        print("-" * 80)
        if not Path(network_capture).exists():
            print(f"⚠️  Network capture file not found: {network_capture}")
            print("   Skipping parsing step. Using existing parsed_endpoints.json if available.")
        else:
            # Try to use AI-enhanced parser if available
            try:
                from ai_enhanced_parser import AIEnhancedParser
                parser = AIEnhancedParser(network_capture)
                print("  Using AI-enhanced parser (if AI is enabled)")
            except ImportError:
                parser = NetworkParser(network_capture)
                print("  Using standard parser")
            
            parsed_data = parser.analyze()
            
            with open('parsed_endpoints.json', 'w') as f:
                import json
                json.dump(parsed_data, f, indent=2)
            
            print(f"✅ Parsed {len(parsed_data.get('endpoints', {}))} endpoints")
        print()
    
    if mode in ["generate", "all"]:
        print("STEP 2: Generating Artifacts")
        print("-" * 80)
        
        import json
        with open('parsed_endpoints.json', 'r') as f:
            parsed_data = json.load(f)
        
        # Generate OpenAPI
        print("  Generating OpenAPI specification...")
        openapi_gen = OpenAPIGenerator(parsed_data)
        openapi_gen.save('api.yml')
        print("  ✅ api.yml generated")
        
        # Generate SQL schema
        print("  Generating SQL schema...")
        schema_gen = SchemaGenerator(parsed_data)
        schema_gen.save('schema.sql')
        print("  ✅ schema.sql generated")
        
        # Generate FastAPI
        print("  Generating FastAPI application...")
        fastapi_gen = FastAPIGenerator(parsed_data)
        fastapi_gen.save('fastapi_app')
        print("  ✅ FastAPI app generated")
        
        # Generate tests
        print("  Generating test cases...")
        test_gen = TestGenerator(parsed_data)
        test_gen.save('tests/test_api.py')
        print("  ✅ Test cases generated")
        print()
    
    if mode in ["test", "all"]:
        print("STEP 3: Running Tests")
        print("-" * 80)
        print("  Running pytest...")
        import subprocess
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_api.py", "-v"],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            print(result.stderr)
        print()
    
    if mode in ["improve", "all"]:
        print("STEP 4: Self-Improvement Loop")
        print("-" * 80)
        print(f"  Running up to {max_iterations} iterations...")
        print(f"  Target quality: {quality_threshold}")
        print()
        
        agent = SelfImprovingAgent(
            network_capture_path=network_capture,
            max_iterations=max_iterations,
            quality_threshold=quality_threshold
        )
        
        final_report = await agent.run()
        
        print()
        print("FINAL RESULTS:")
        print(f"  Iterations: {final_report.get('total_iterations', 0)}")
        print(f"  Converged: {final_report.get('converged', False)}")
        print(f"  Final Quality: {final_report.get('final_quality', 0):.2%}")
        print()
    
    print("="*80)
    print("Pipeline Complete!")
    print("="*80)


def main():
    parser = argparse.ArgumentParser(description='Clooney Project Pipeline')
    parser.add_argument('--network-capture', default='network_capture.json',
                       help='Path to network capture JSON file')
    parser.add_argument('--mode', choices=['parse', 'generate', 'test', 'improve', 'all'],
                       default='all', help='Pipeline mode')
    parser.add_argument('--iterations', type=int, default=5,
                       help='Number of improvement iterations')
    parser.add_argument('--threshold', type=float, default=0.95,
                       help='Quality threshold for convergence (0-1)')
    
    args = parser.parse_args()
    
    asyncio.run(run_pipeline(
        network_capture=args.network_capture,
        mode=args.mode,
        max_iterations=args.iterations,
        quality_threshold=args.threshold
    ))


if __name__ == "__main__":
    main()

