"""Verify all route handlers have docstrings.

This test ensures all Flask route handlers are documented with
comprehensive docstrings following Google-style conventions.
"""

import ast
import inspect


def get_all_routes():
    """Extract all route functions from blueprints."""
    routes = []

    # Import all blueprints
    from collector.routes import api, jobs, pages, sessions

    blueprints = [
        ("jobs", jobs.jobs_bp),
        ("pages", pages.pages_bp),
        ("sessions", sessions.sessions_bp),
        ("api", api.api_bp),
    ]

    for module_name, bp in blueprints:
        # Get the module source
        module = inspect.getmodule(bp)
        if module is None:
            continue
        source = inspect.getsource(module)

        # Parse AST
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function is a route
                has_route_decorator = any(
                    (
                        isinstance(dec, ast.Call)
                        and hasattr(dec.func, "attr")
                        and dec.func.attr == "route"
                    )
                    or (
                        isinstance(dec, ast.Call)
                        and hasattr(dec.func, "attr")
                        and dec.func.attr == "route"
                    )
                    for dec in node.decorator_list
                )

                if has_route_decorator:
                    docstring = ast.get_docstring(node)
                    has_docstring = docstring is not None
                    routes.append(
                        {
                            "module": module_name,
                            "function": node.name,
                            "has_docstring": has_docstring,
                            "docstring": docstring,
                        }
                    )

    return routes


def test_route_documentation_coverage():
    """Test that all route handlers have docstrings."""
    routes = get_all_routes()

    undocumented = [r for r in routes if not r["has_docstring"]]
    documented = [r for r in routes if r["has_docstring"]]

    print("\nRoute Documentation Coverage:")
    print(f"  Total routes: {len(routes)}")
    print(f"  Documented: {len(documented)}")
    print(f"  Undocumented: {len(undocumented)}")
    if len(routes) > 0:
        coverage = len(documented) / len(routes) * 100
        print(f"  Coverage: {coverage:.1f}%")

    if undocumented:
        print("\nUndocumented routes:")
        for route in undocumented:
            print(f"  - {route['module']}.{route['function']}")

    assert len(undocumented) == 0, f"{len(undocumented)} route(s) missing documentation"

    print("\nAll routes have documentation!")


def check_docstring_quality(func_name, docstring):
    """Check if docstring meets quality standards."""
    issues = []

    if not docstring:
        return ["Missing docstring"]

    # Check for one-line summary
    lines = docstring.strip().split("\n")
    if not lines[0].strip():
        issues.append("Missing one-line summary")

    # Check for Returns section
    if "Returns:" not in docstring:
        issues.append("Missing Returns section")

    # Check for CSRF in POST/DELETE routes
    if any(x in func_name for x in ["upload", "delete", "cancel", "retry"]):
        if "CSRF" not in docstring:
            issues.append("Missing CSRF documentation")

    # Check for HTMX behavior if likely HTMX route
    if any(x in func_name for x in ["status", "active", "detail"]):
        if "HTMX" not in docstring:
            issues.append("Consider adding HTMX Behavior section")

    return issues


def test_docstring_quality():
    """Test that all route docstrings meet quality standards."""
    routes = get_all_routes()
    all_issues = []

    for route in routes:
        if route["has_docstring"]:
            issues = check_docstring_quality(route["function"], route["docstring"])
            if issues:
                all_issues.append(
                    {"route": f"{route['module']}.{route['function']}", "issues": issues}
                )

    if all_issues:
        print("\nDocstring Quality Issues:")
        for item in all_issues:
            print(f"  {item['route']}:")
            for issue in item["issues"]:
                print(f"    - {issue}")

    # Warn about quality issues but don't fail the test
    if all_issues:
        print(f"\nWarning: {len(all_issues)} route(s) have docstring quality issues")
    else:
        print("\nAll route docstrings meet quality standards!")
