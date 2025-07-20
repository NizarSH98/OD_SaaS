#!/usr/bin/env python3
"""
Main entry point for the Video Labeling Tool application.

This script uses Poetry to run the Flask application for creating
labeled datasets from videos, and includes comprehensive testing capabilities.
"""

import os
import sys
import subprocess
import argparse
from typing import List, Optional

def run_tests(test_args: Optional[List[str]] = None, coverage: bool = False, verbose: bool = False) -> int:
    """
    Run the comprehensive test suite using pytest.
    
    Args:
        test_args: Additional pytest arguments
        coverage: Whether to run with coverage reporting
        verbose: Whether to use verbose output
        
    Returns:
        Exit code from pytest
    """
    try:
        print("🧪 Running VisionLabel Pro Test Suite...")
        print("📁 Project directory:", os.getcwd())
        print("🔧 Using Poetry virtual environment")
        print("-" * 60)
        
        # Base pytest command
        cmd = ["poetry", "run", "pytest"]
        
        # Add verbosity
        if verbose:
            cmd.extend(["-v", "--tb=short"])
        else:
            cmd.append("-q")
        
        # Add coverage if requested (requires pytest-cov)
        if coverage:
            try:
                cmd.extend([
                    "--cov=modules",
                    "--cov=app", 
                    "--cov=config",
                    "--cov-report=term-missing",
                    "--cov-report=html:htmlcov"
                ])
                print("📊 Coverage reporting enabled")
            except Exception:
                print("⚠️  Coverage reporting unavailable (pytest-cov not installed)")
                print("   Install with: poetry add --group dev pytest-cov")
                print("   Continuing without coverage...")
        
        # Add test directory
        cmd.append("tests/")
        
        # Add any additional arguments
        if test_args:
            cmd.extend(test_args)
        
        print(f"🏃 Running command: {' '.join(cmd[2:])}")  # Skip 'poetry run'
        print("-" * 60)
        
        # Run tests
        result = subprocess.run(cmd, check=False)
        
        print("-" * 60)
        if result.returncode == 0:
            print("✅ All tests passed successfully!")
            if coverage:
                print("📊 Coverage report generated in 'htmlcov/' directory")
        else:
            print("❌ Some tests failed. See output above for details.")
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n⏹️  Test execution interrupted by user")
        return 1
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running tests: {e}")
        print("💡 Make sure Poetry is installed and dependencies are available")
        return 1
    except FileNotFoundError:
        print("❌ Poetry not found. Please install Poetry first:")
        print("   curl -sSL https://install.python-poetry.org | python3 -")
        print("   or visit: https://python-poetry.org/docs/#installation")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

def run_specific_tests(test_pattern: str, verbose: bool = False) -> int:
    """
    Run specific tests matching a pattern.
    
    Args:
        test_pattern: Pattern to match test files or functions
        verbose: Whether to use verbose output
        
    Returns:
        Exit code from pytest
    """
    print(f"🎯 Running tests matching pattern: {test_pattern}")
    return run_tests(["-k", test_pattern], verbose=verbose)

def run_test_categories(categories: List[str], verbose: bool = False) -> int:
    """
    Run tests by category (unit, integration, slow).
    
    Args:
        categories: List of test categories to run
        verbose: Whether to use verbose output
        
    Returns:
        Exit code from pytest
    """
    marker_args = []
    for category in categories:
        if category in ['unit', 'integration', 'slow']:
            marker_args.extend(["-m", category])
        else:
            print(f"⚠️  Unknown test category: {category}")
            print("   Available categories: unit, integration, slow")
            return 1
    
    if marker_args:
        print(f"📂 Running {', '.join(categories)} tests...")
        return run_tests(marker_args, verbose=verbose)
    else:
        print("❌ No valid test categories specified")
        return 1

def show_test_info() -> None:
    """Display information about available tests and categories."""
    print("🧪 VisionLabel Pro Test Suite Information")
    print("=" * 50)
    print()
    
    print("📁 Test Structure:")
    print("  tests/")
    print("  ├── conftest.py              # Shared fixtures and configuration")
    print("  ├── test_auth.py            # Authentication system tests")
    print("  ├── test_models.py          # User model tests")  
    print("  ├── test_video_processor.py # Video processing tests")
    print("  ├── test_data_storage.py    # Annotation storage tests")
    print("  ├── test_routes.py          # API endpoint tests")
    print("  └── test_integration.py     # End-to-end integration tests")
    print()
    
    print("🏷️  Test Categories:")
    print("  unit        - Fast unit tests for individual components")
    print("  integration - Integration tests for component interaction")  
    print("  slow        - Longer-running tests and performance tests")
    print()
    
    print("🎯 Example Usage:")
    print("  python main.py --test                    # Run all tests")
    print("  python main.py --test --coverage         # Run with coverage")
    print("  python main.py --test --verbose          # Verbose output")
    print("  python main.py --test-unit               # Run only unit tests")
    print("  python main.py --test-integration        # Run only integration tests")
    print("  python main.py --test-pattern auth       # Run auth-related tests")
    print("  python main.py --test-info               # Show this information")
    print()
    
    print("📊 Coverage Reports:")
    print("  Terminal output shows line-by-line coverage")
    print("  HTML report generated in 'htmlcov/' directory")
    print("  Open 'htmlcov/index.html' in browser for detailed view")

def main():
    """Main function to start the Flask application or run tests."""
    parser = argparse.ArgumentParser(
        description="VisionLabel Pro - Professional Video Annotation Platform",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Start the application
  python main.py --test                    # Run all tests  
  python main.py --test --coverage         # Run tests with coverage
  python main.py --test-unit               # Run unit tests only
  python main.py --test-integration        # Run integration tests only
  python main.py --test-pattern auth       # Run auth-related tests
  python main.py --test-info               # Show test information
        """
    )
    
    # Test-related arguments
    test_group = parser.add_argument_group('Testing Options')
    test_group.add_argument('--test', action='store_true',
                           help='Run the complete test suite')
    test_group.add_argument('--test-unit', action='store_true',
                           help='Run unit tests only')
    test_group.add_argument('--test-integration', action='store_true', 
                           help='Run integration tests only')
    test_group.add_argument('--test-slow', action='store_true',
                           help='Run slow/performance tests only')
    test_group.add_argument('--test-pattern', type=str,
                           help='Run tests matching pattern (e.g., "auth" or "video")')
    test_group.add_argument('--test-info', action='store_true',
                           help='Show test suite information and exit')
    test_group.add_argument('--coverage', action='store_true',
                           help='Generate coverage report when running tests')
    test_group.add_argument('--verbose', '-v', action='store_true',
                           help='Use verbose output for tests')
    
    # Application arguments  
    app_group = parser.add_argument_group('Application Options')
    app_group.add_argument('--host', default='localhost', 
                          help='Host to bind the application to')
    app_group.add_argument('--port', type=int, default=5000,
                          help='Port to bind the application to')
    app_group.add_argument('--debug', action='store_true',
                          help='Run application in debug mode')
    
    args = parser.parse_args()
    
    # Handle test information request
    if args.test_info:
        show_test_info()
        return 0
    
    # Handle test execution
    if args.test:
        return run_tests(coverage=args.coverage, verbose=args.verbose)
    elif args.test_unit:
        return run_test_categories(['unit'], verbose=args.verbose)
    elif args.test_integration:
        return run_test_categories(['integration'], verbose=args.verbose)
    elif args.test_slow:
        return run_test_categories(['slow'], verbose=args.verbose)
    elif args.test_pattern:
        return run_specific_tests(args.test_pattern, verbose=args.verbose)
    
    # Run the Flask application
    try:
        print("🚀 Starting VisionLabel Pro with Poetry...")
        print("📁 Project directory:", os.getcwd())
        print("🔧 Using Poetry virtual environment")
        print("🎥 Running full application with OpenCV support")
        
        if args.debug:
            print("🐛 Debug mode enabled")
        
        print("-" * 50)
        
        # Build Flask app command
        cmd = ["poetry", "run", "python", "app.py"]
        
        # Set environment variables for Flask configuration
        env = os.environ.copy()
        env['FLASK_HOST'] = args.host
        env['FLASK_PORT'] = str(args.port)
        if args.debug:
            env['FLASK_DEBUG'] = '1'
        
        print(f"🌐 Starting server on http://{args.host}:{args.port}")
        if args.debug:
            print("🔍 Debug mode: Detailed error pages and auto-reload enabled")
        
        print("🔗 Access the application at the URL above")
        print("⏹️  Press Ctrl+C to stop the server")
        print("-" * 50)
        
        # Start the application
        subprocess.run(cmd, check=True, env=env)
        
    except KeyboardInterrupt:
        print("\n👋 Application stopped by user")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running application: {e}")
        print("💡 Make sure Poetry is installed and dependencies are available")
        print("🧪 Try running tests first: python main.py --test")
        return 1
    except FileNotFoundError:
        print("❌ Poetry not found. Please install Poetry first:")
        print("   curl -sSL https://install.python-poetry.org | python3 -")
        print("   or visit: https://python-poetry.org/docs/#installation")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())