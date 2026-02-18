"""Validate tree-sitter C# queries against real parse trees.

This test file verifies that the QUERY_STR_CSHARP, QUERY_STR_TYPES_CSHARP,
and QUERY_STR_CLASS_MEMBERS_CSHARP queries correctly match C# code patterns.
"""

from tree_sitter_language_pack import get_language, get_parser


# Sample C# code covering common patterns
SAMPLE_CSHARP_CODE = b"""
using System;
using System.Collections.Generic;
using static System.Math;

namespace MyApp.Models
{
    public interface IRepository<T>
    {
        T GetById(int id);
        void Save(T entity);
        List<T> GetAll();
    }

    public class UserService
    {
        private readonly string _connectionString;
        private int _retryCount;

        public UserService(string connectionString)
        {
            _connectionString = connectionString;
            _retryCount = 3;
        }

        public async Task<User> GetUserAsync(int userId)
        {
            return await _repository.GetByIdAsync(userId);
        }

        public void DeleteUser(int userId)
        {
            _repository.Delete(userId);
        }

        private static bool ValidateEmail(string email)
        {
            return email.Contains("@");
        }
    }

    public struct Point
    {
        public double X;
        public double Y;

        public double Distance()
        {
            return Sqrt(X * X + Y * Y);
        }
    }

    public enum Status
    {
        Active,
        Inactive,
        Pending
    }

    public record PersonRecord(string Name, int Age);
}
"""

# SharpFuzz harness patterns
SAMPLE_SHARPFUZZ_HARNESS = b"""
using System;
using SharpFuzz;

public class FuzzTarget
{
    public static void Main(string[] args)
    {
        Fuzzer.LibFuzzer.Run(span =>
        {
            var data = span.ToArray();
            ProcessInput(data);
        });
    }

    private static void ProcessInput(byte[] data)
    {
        if (data.Length > 4)
        {
            var str = System.Text.Encoding.UTF8.GetString(data);
            Parse(str);
        }
    }

    private static void Parse(string input)
    {
        // parsing logic
    }
}
"""


def _parse(code: bytes):
    parser = get_parser("csharp")
    return parser.parse(code)


def _print_tree(node, indent=0):
    """Debug helper: print parse tree structure."""
    text = ""
    if node.child_count == 0:
        text = f" = {repr(node.text.decode())}"
    line = f"{'  ' * indent}{node.type} [{node.start_point[0]}:{node.start_point[1]}-{node.end_point[0]}:{node.end_point[1]}]{text}"
    print(line)
    for child in node.children:
        _print_tree(child, indent + 1)


def test_csharp_parser_works():
    """Verify tree-sitter C# parser loads and parses without error."""
    tree = _parse(SAMPLE_CSHARP_CODE)
    root = tree.root_node
    assert root.type == "compilation_unit"
    assert not root.has_error, f"Parse tree has errors: {root.text.decode()[:200]}"


def test_query_str_csharp_methods():
    """Validate QUERY_STR_CSHARP matches method declarations."""
    from buttercup.program_model.api.tree_sitter import QUERY_STR_CSHARP

    tree = _parse(SAMPLE_CSHARP_CODE)
    lang = get_language("csharp")
    query = lang.query(QUERY_STR_CSHARP)
    matches = query.matches(tree.root_node)

    func_names = []
    for _match_id, capture_dict in matches:
        if "function.name" in capture_dict:
            for node in capture_dict["function.name"]:
                func_names.append(node.text.decode())

    print(f"Captured method names: {func_names}")

    # We expect these methods from SAMPLE_CSHARP_CODE
    expected_methods = {"GetUserAsync", "DeleteUser", "ValidateEmail", "Distance"}
    # Note: constructors are constructor_declaration, not method_declaration
    # Note: interface methods without bodies won't match (they need body: (block))

    for method in expected_methods:
        assert method in func_names, f"Expected method '{method}' not found in captures: {func_names}"

    # Verify constructors are NOT captured (they're a different node type)
    assert "UserService" not in func_names, "Constructor should not be captured as method_declaration"


def test_query_str_csharp_methods_sharpfuzz():
    """Validate QUERY_STR_CSHARP matches methods in a SharpFuzz harness."""
    from buttercup.program_model.api.tree_sitter import QUERY_STR_CSHARP

    tree = _parse(SAMPLE_SHARPFUZZ_HARNESS)
    lang = get_language("csharp")
    query = lang.query(QUERY_STR_CSHARP)
    matches = query.matches(tree.root_node)

    func_names = []
    for _match_id, capture_dict in matches:
        if "function.name" in capture_dict:
            for node in capture_dict["function.name"]:
                func_names.append(node.text.decode())

    print(f"SharpFuzz harness method names: {func_names}")

    assert "Main" in func_names, f"Main not found: {func_names}"
    assert "ProcessInput" in func_names, f"ProcessInput not found: {func_names}"
    assert "Parse" in func_names, f"Parse not found: {func_names}"


def test_query_str_types_csharp():
    """Validate QUERY_STR_TYPES_CSHARP matches type definitions."""
    from buttercup.program_model.api.tree_sitter import QUERY_STR_TYPES_CSHARP

    tree = _parse(SAMPLE_CSHARP_CODE)
    lang = get_language("csharp")
    query = lang.query(QUERY_STR_TYPES_CSHARP)
    matches = query.matches(tree.root_node)

    type_names = []
    for _match_id, capture_dict in matches:
        if "type.name" in capture_dict:
            for node in capture_dict["type.name"]:
                type_names.append(node.text.decode())

    print(f"Captured type names: {type_names}")

    expected_types = {"IRepository", "UserService", "Point", "Status", "PersonRecord"}
    for t in expected_types:
        assert t in type_names, f"Expected type '{t}' not found in captures: {type_names}"


def test_query_str_class_members_csharp():
    """Validate QUERY_STR_CLASS_MEMBERS_CSHARP matches fields and methods."""
    from buttercup.program_model.api.tree_sitter import QUERY_STR_CLASS_MEMBERS_CSHARP

    tree = _parse(SAMPLE_CSHARP_CODE)
    lang = get_language("csharp")
    query = lang.query(QUERY_STR_CLASS_MEMBERS_CSHARP)
    matches = query.matches(tree.root_node)

    # Collect all captures by name
    results: dict[str, list[str]] = {}
    for _match_id, capture_dict in matches:
        for capture_name, nodes in capture_dict.items():
            for node in nodes:
                results.setdefault(capture_name, []).append(node.text.decode())

    print(f"Class member captures: {results}")

    # Check field names captured
    assert "name" in results, f"No 'name' captures found. Available: {list(results.keys())}"
    field_names = results["name"]
    print(f"Field names: {field_names}")
    assert "_connectionString" in field_names or "_retryCount" in field_names, \
        f"Expected field names not found: {field_names}"

    # Check method names captured
    assert "method_name" in results, f"No 'method_name' captures found. Available: {list(results.keys())}"
    method_names = results["method_name"]
    print(f"Method names in classes: {method_names}")
    assert "GetUserAsync" in method_names or "DeleteUser" in method_names, \
        f"Expected method names not found: {method_names}"


def test_parse_tree_node_types():
    """Verify key node types match our assumptions."""
    code = b"""
public class Foo
{
    private int _bar;

    public void DoSomething(string input)
    {
        Console.WriteLine(input);
    }
}
"""
    tree = _parse(code)
    print("\n=== Parse tree for minimal C# class ===")
    _print_tree(tree.root_node)

    root = tree.root_node
    class_node = None
    for child in root.children:
        if child.type == "class_declaration":
            class_node = child
            break

    assert class_node is not None, "class_declaration node not found"

    # Check that the class body is declaration_list (not class_body like Java)
    body_node = None
    for child in class_node.children:
        if child.type == "declaration_list":
            body_node = child
            break

    assert body_node is not None, \
        f"declaration_list not found in class_declaration. Children: {[c.type for c in class_node.children]}"

    child_types = [c.type for c in body_node.children]
    print(f"declaration_list children types: {child_types}")
    assert "field_declaration" in child_types, f"field_declaration not found: {child_types}"
    assert "method_declaration" in child_types, f"method_declaration not found: {child_types}"


def test_method_declaration_fields():
    """Verify that method_declaration has the expected field names."""
    code = b"""
public class Foo
{
    public int Calculate(int x, int y)
    {
        return x + y;
    }
}
"""
    tree = _parse(code)
    root = tree.root_node

    method_node = None

    def find_method(node):
        nonlocal method_node
        if node.type == "method_declaration":
            method_node = node
            return
        for child in node.children:
            find_method(child)

    find_method(root)
    assert method_node is not None, "method_declaration not found"

    field_names = set()
    for i in range(method_node.child_count):
        fn = method_node.field_name_for_child(i)
        if fn:
            field_names.add(fn)

    print(f"method_declaration field names: {field_names}")
    print(f"method_declaration children: {[(c.type, method_node.field_name_for_child(i)) for i, c in enumerate(method_node.children)]}")

    # Our query uses: returns, name, parameters, body
    assert "name" in field_names, f"'name' field not found: {field_names}"
    assert "parameters" in field_names, f"'parameters' field not found: {field_names}"
    assert "body" in field_names, f"'body' field not found: {field_names}"
    assert "returns" in field_names, f"'returns' field not found: {field_names}"
