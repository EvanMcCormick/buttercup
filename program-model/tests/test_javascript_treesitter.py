"""Validate tree-sitter JavaScript/TypeScript queries against real parse trees.

This test file verifies that the QUERY_STR_JAVASCRIPT, QUERY_STR_TYPES_JAVASCRIPT,
and QUERY_STR_CLASS_MEMBERS_JAVASCRIPT queries correctly match JS/TS code patterns.
"""

from tree_sitter_language_pack import get_language, get_parser


# Sample TypeScript code covering common patterns
SAMPLE_TYPESCRIPT_CODE = b"""
import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
const fs = require('fs');

interface UserRepository {
    getById(id: number): User;
    save(entity: User): void;
    getAll(): User[];
}

class UserService {
    private connectionString: string;
    private retryCount: number;

    constructor(connectionString: string) {
        this.connectionString = connectionString;
        this.retryCount = 3;
    }

    async getUserAsync(userId: number): Promise<User> {
        return await this.repository.getByIdAsync(userId);
    }

    deleteUser(userId: number): void {
        this.repository.delete(userId);
    }

    private static validateEmail(email: string): boolean {
        return email.includes("@");
    }
}

enum Status {
    Active = "active",
    Inactive = "inactive",
    Pending = "pending",
}

type UserRole = "admin" | "user" | "guest";

function freeStandingFunction(x: number): number {
    return x * 2;
}

const arrowFunction = (x: number): number => {
    return x + 1;
};
"""

# Jazzer.js harness patterns
SAMPLE_JAZZERJS_HARNESS = b"""
const { fuzz } = require('@jazzer.js/core');

function processInput(data) {
    if (data.length > 4) {
        const str = Buffer.from(data).toString('utf-8');
        parse(str);
    }
}

function parse(input) {
    // parsing logic
    JSON.parse(input);
}

module.exports.fuzz = function(data) {
    processInput(data);
};
"""

# ES module harness
SAMPLE_ES_MODULE_HARNESS = b"""
import { someLibrary } from 'some-library';

function processData(data) {
    return someLibrary.process(Buffer.from(data).toString());
}

export async function fuzz(data) {
    processData(data);
}
"""


def _parse(code: bytes):
    parser = get_parser("typescript")
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


def test_typescript_parser_works():
    """Verify tree-sitter TypeScript parser loads and parses without error."""
    tree = _parse(SAMPLE_TYPESCRIPT_CODE)
    root = tree.root_node
    assert root.type == "program"
    assert not root.has_error, f"Parse tree has errors: {root.text.decode()[:200]}"


def test_query_str_javascript_methods():
    """Validate QUERY_STR_JAVASCRIPT matches function/method declarations."""
    from buttercup.program_model.api.tree_sitter import QUERY_STR_JAVASCRIPT

    tree = _parse(SAMPLE_TYPESCRIPT_CODE)
    lang = get_language("typescript")
    query = lang.query(QUERY_STR_JAVASCRIPT)
    matches = query.matches(tree.root_node)

    func_names = []
    for _match_id, capture_dict in matches:
        if "function.name" in capture_dict:
            for node in capture_dict["function.name"]:
                func_names.append(node.text.decode())

    print(f"Captured function/method names: {func_names}")

    # Methods inside the class
    expected_methods = {"getUserAsync", "deleteUser", "validateEmail"}
    for method in expected_methods:
        assert method in func_names, f"Expected method '{method}' not found in captures: {func_names}"

    # Free-standing function
    assert "freeStandingFunction" in func_names, f"freeStandingFunction not found: {func_names}"


def test_query_str_javascript_methods_jazzerjs():
    """Validate QUERY_STR_JAVASCRIPT matches functions in a Jazzer.js harness."""
    from buttercup.program_model.api.tree_sitter import QUERY_STR_JAVASCRIPT

    tree = _parse(SAMPLE_JAZZERJS_HARNESS)
    lang = get_language("typescript")
    query = lang.query(QUERY_STR_JAVASCRIPT)
    matches = query.matches(tree.root_node)

    func_names = []
    for _match_id, capture_dict in matches:
        if "function.name" in capture_dict:
            for node in capture_dict["function.name"]:
                func_names.append(node.text.decode())

    print(f"Jazzer.js harness function names: {func_names}")

    assert "processInput" in func_names, f"processInput not found: {func_names}"
    assert "parse" in func_names, f"parse not found: {func_names}"


def test_query_str_javascript_es_module_harness():
    """Validate QUERY_STR_JAVASCRIPT matches export async function in ES module harness."""
    from buttercup.program_model.api.tree_sitter import QUERY_STR_JAVASCRIPT

    tree = _parse(SAMPLE_ES_MODULE_HARNESS)
    lang = get_language("typescript")
    query = lang.query(QUERY_STR_JAVASCRIPT)
    matches = query.matches(tree.root_node)

    func_names = []
    for _match_id, capture_dict in matches:
        if "function.name" in capture_dict:
            for node in capture_dict["function.name"]:
                func_names.append(node.text.decode())

    print(f"ES module harness function names: {func_names}")

    assert "processData" in func_names, f"processData not found: {func_names}"
    assert "fuzz" in func_names, f"fuzz not found: {func_names}"


def test_query_str_types_javascript():
    """Validate QUERY_STR_TYPES_JAVASCRIPT matches type definitions."""
    from buttercup.program_model.api.tree_sitter import QUERY_STR_TYPES_JAVASCRIPT

    tree = _parse(SAMPLE_TYPESCRIPT_CODE)
    lang = get_language("typescript")
    query = lang.query(QUERY_STR_TYPES_JAVASCRIPT)
    matches = query.matches(tree.root_node)

    type_names = []
    for _match_id, capture_dict in matches:
        if "type.name" in capture_dict:
            for node in capture_dict["type.name"]:
                type_names.append(node.text.decode())

    print(f"Captured type names: {type_names}")

    expected_types = {"UserRepository", "UserService", "Status", "UserRole"}
    for t in expected_types:
        assert t in type_names, f"Expected type '{t}' not found in captures: {type_names}"


def test_query_str_class_members_javascript():
    """Validate QUERY_STR_CLASS_MEMBERS_JAVASCRIPT matches fields and methods."""
    from buttercup.program_model.api.tree_sitter import QUERY_STR_CLASS_MEMBERS_JAVASCRIPT

    tree = _parse(SAMPLE_TYPESCRIPT_CODE)
    lang = get_language("typescript")
    query = lang.query(QUERY_STR_CLASS_MEMBERS_JAVASCRIPT)
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
    assert "connectionString" in field_names or "retryCount" in field_names, \
        f"Expected field names not found: {field_names}"

    # Check method names captured
    assert "method_name" in results, f"No 'method_name' captures found. Available: {list(results.keys())}"
    method_names = results["method_name"]
    print(f"Method names in classes: {method_names}")
    assert "getUserAsync" in method_names or "deleteUser" in method_names, \
        f"Expected method names not found: {method_names}"


def test_parse_tree_node_types():
    """Verify key TypeScript node types match our assumptions."""
    code = b"""
class Foo {
    private bar: number;

    doSomething(input: string): void {
        console.log(input);
    }
}
"""
    tree = _parse(code)
    print("\n=== Parse tree for minimal TS class ===")
    _print_tree(tree.root_node)

    root = tree.root_node
    class_node = None
    for child in root.children:
        if child.type == "class_declaration":
            class_node = child
            break

    assert class_node is not None, "class_declaration node not found"

    # Check that the class body is class_body (not declaration_list like C#)
    body_node = None
    for child in class_node.children:
        if child.type == "class_body":
            body_node = child
            break

    assert body_node is not None, \
        f"class_body not found in class_declaration. Children: {[c.type for c in class_node.children]}"

    child_types = [c.type for c in body_node.children]
    print(f"class_body children types: {child_types}")
    assert "public_field_definition" in child_types, f"public_field_definition not found: {child_types}"
    assert "method_definition" in child_types, f"method_definition not found: {child_types}"


def test_method_definition_fields():
    """Verify that method_definition has the expected field names."""
    code = b"""
class Foo {
    calculate(x: number, y: number): number {
        return x + y;
    }
}
"""
    tree = _parse(code)
    root = tree.root_node

    method_node = None

    def find_method(node):
        nonlocal method_node
        if node.type == "method_definition":
            method_node = node
            return
        for child in node.children:
            find_method(child)

    find_method(root)
    assert method_node is not None, "method_definition not found"

    field_names = set()
    for i in range(method_node.child_count):
        fn = method_node.field_name_for_child(i)
        if fn:
            field_names.add(fn)

    print(f"method_definition field names: {field_names}")
    print(f"method_definition children: {[(c.type, method_node.field_name_for_child(i)) for i, c in enumerate(method_node.children)]}")

    # Our query uses: name, parameters, body
    assert "name" in field_names, f"'name' field not found: {field_names}"
    assert "parameters" in field_names, f"'parameters' field not found: {field_names}"
    assert "body" in field_names, f"'body' field not found: {field_names}"
    # return_type is available for TypeScript
    assert "return_type" in field_names, f"'return_type' field not found: {field_names}"
