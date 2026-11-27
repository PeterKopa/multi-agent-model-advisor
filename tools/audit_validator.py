#!/usr/bin/env python3
"""Static audit of the offline workflow validator.

The workflow validator is trusted by agents and automation decisions, so it is
audited before it is trusted. This module reads ``tools/workflow_check.py`` as
a Python AST and checks six properties without executing any of it:

1. imports stay inside a pinned read-only standard-library allowlist (plus the
   sibling ``audit_validator`` module that ``all`` loads at run time); a
   wildcard import (``from <module> import *``) is rejected outright, because
   a star binding cannot be resolved and would let the auditor lose track of
   what a name refers to;
2. no forbidden calls or attributes: ``eval``, ``exec``, ``compile``,
   ``__import__``, ``os.system``, ``os.popen``, and any ``subprocess`` call —
   under its own name, an ``import subprocess as <alias>`` alias, a chain of
   attribute segments such as ``import subprocess.subprocess`` followed by
   ``subprocess.subprocess.run``, or a ``from subprocess import <name>``
   binding (with or without ``as``) — with a ``shell`` keyword that is not
   literal ``False``. A subprocess spawn function (``run``, ``call``,
   ``check_call``, ``check_output``, ``Popen``, ``getoutput``,
   ``getstatusoutput``) may only appear as the callable of a direct
   ``subprocess.<name>(...)`` call: any other reference is rejected fail-closed,
   including rebinding it to another name (``runner = subprocess.run``, an
   annotated assignment or a walrus), storing it in a container or argument
   list and returning it, because the auditor cannot promise to track every
   later use of such a name;
3. every ``subprocess.*`` call site — plain, aliased, from-imported or
   reached through extra attribute segments — passes a list or tuple literal
   as its first positional argument whose first element is the constant string
   ``"git"`` and whose second element is a pinned read-only git verb; the
   dynamic ``*args`` passthrough of the local ``git()`` wrapper is the one
   accepted dynamic shape, because property 4
   pins every ``git()`` call site. The accepted argv shape is
   shape-based, not call-site based: any single call site whose argv is
   ``["git", <Starred>, …]`` is accepted by this property, so such a site's
   argv needs manual review;
4. git verbs stay in one pinned read-only set: the set is derived over all
   call sites (the literal first argument of every local ``git()`` helper
   call, and the constant second command element of every ``subprocess.*``
   command list) and must equal ``EXPECTED_GIT_VERBS`` exactly, in both
   directions, so a new git verb needs a conscious decision to update the
   pin;
5. no write access: no ``open()`` outside read-only modes (and no
   non-literal mode), the same mode check for ``.open(...)`` called on a
   receiver the Path dataflow recognises as Path-ish, no path-mutating
   method call (``write_text``, ``write_bytes``, ``unlink``, ``rename``,
   ``replace``, ``mkdir``, ``rmdir``, ``touch``, ``chmod``) and no
   ``shutil`` import;
6. no network-capable module import: ``socket``, ``ssl``, ``http``,
   ``urllib``, ``ftplib``, ``smtplib``, ``telnetlib``, ``xmlrpc``,
   ``requests`` and ``httpx``.

Each finding prints one ``FAIL audit:`` line to stderr and the exit code is 1.
On success one ``PASS audit:`` line with the checked property count is printed
and the exit code is 0.

Honest limit: this audit bounds constructs. It is a guardrail, not a sandbox.
It inspects a snapshot of the file and cannot prove runtime behaviour. Exactly
what it cannot see is named: dynamic-argument ``subprocess`` lists other than
the audited ``git(*args)`` wrapper shape, verbs or modes computed through
calls the AST cannot resolve (``getattr``, ``globals()``, builtins
manipulation), ``subprocess`` functions reached through a receiver the dataflow
cannot resolve to the module root (for example one produced by a call), and
``.open(...)`` on a receiver it cannot classify as Path-ish. A subprocess
alias built without an import or assignment statement — for example through
``getattr(subprocess, "run")`` — is equally outside the audit. It therefore
does not make the validator safe; reviewer judgement, the review gates and the
human-approved handover remain part of the control set.
"""

import ast
import sys
from pathlib import Path

AUDITED_MODULE = Path(__file__).resolve().parent / "workflow_check.py"

# Property 1: pinned import allowlist. The module under audit may import
# exactly these standard-library roots, plus this sibling audit module, which
# check_self_audit() loads at run time.
ALLOWED_IMPORT_ROOTS = {
    "argparse",
    "ast",
    "fnmatch",
    "hashlib",
    "json",
    "re",
    "subprocess",
    "sys",
    "pathlib",
    "typing",
    "__future__",
}
ALLOWED_SIBLING_IMPORTS = {"audit_validator"}

# Property 6: network-capable modules are denied by name.
NETWORK_MODULE_ROOTS = {
    "socket",
    "ssl",
    "http",
    "urllib",
    "ftplib",
    "smtplib",
    "telnetlib",
    "xmlrpc",
    "requests",
    "httpx",
}

# Property 5: file-mutating modules are denied by name.
WRITE_MODULE_ROOTS = {"shutil"}

# Property 2: forbidden built-in calls and forbidden os attributes.
FORBIDDEN_BUILTIN_CALLS = {"eval", "exec", "compile", "__import__"}
FORBIDDEN_OS_METHODS = {"system", "popen"}

# Property 3/4: subprocess entry points. The module may spawn git only,
# through a list or tuple literal whose first element is the constant string
# "git" and whose second element pins a read-only verb (property 4), with the
# local git() wrapper's *args passthrough as the one accepted dynamic shape.
# A name may reference one of these functions only as the callable of a
# direct call (property 2); any other reference is rejected.
SUBPROCESS_FUNCTIONS = {
    "run",
    "call",
    "check_call",
    "check_output",
    "Popen",
    "getoutput",
    "getstatusoutput",
}

# Property 4: pinned read-only git verbs. The audit derives the actual set
# over all call sites — git() helper arguments and constant verb elements at
# subprocess command lists — and requires exact equality, in both directions.
EXPECTED_GIT_VERBS = {"rev-parse", "ls-tree", "show"}

# Property 5: path-mutating method calls. ``replace`` needs a Path-like
# receiver (plain str.replace is read-only and stays allowed).
UNCONDITIONAL_WRITE_METHODS = {
    "write_text",
    "write_bytes",
    "unlink",
    "rename",
    "mkdir",
    "rmdir",
    "touch",
    "chmod",
}

# Property 5: open() modes with any of these characters can write.
WRITE_MODE_CHARS = "wax+"

CHECKED_PROPERTIES = 6


def _finding(findings, message):
    findings.append(message)
    print("FAIL audit: " + message, file=sys.stderr)


def _import_roots(tree, findings):
    """Collect the root modules of every import; relative and star imports fail."""
    roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module:
                roots.add(node.module.split(".")[0])
            else:
                _finding(
                    findings,
                    "relative import at line %d cannot be allowed" % node.lineno,
                )
            for alias in node.names:
                if alias.name == "*":
                    _finding(
                        findings,
                        "wildcard import 'from %s import *' at line %d is "
                        "rejected: a star binding cannot be resolved, so "
                        "import the needed names explicitly"
                        % (node.module or "<relative>", node.lineno),
                    )
    return roots


def _subprocess_import_bindings(tree):
    """Resolve how the audited module reaches ``subprocess``.

    Returns ``(module_aliases, function_bindings)``: ``module_aliases`` maps
    every bound name to its imported module root for plain ``import``
    statements (``import subprocess`` -> ``subprocess``,
    ``import subprocess as sp`` -> ``sp`` -> ``subprocess``; the dotted
    ``import subprocess.subprocess`` still binds the module root under the
    name ``subprocess``); ``function_bindings`` maps every bound name from
    ``from subprocess import <name>`` (with or without ``as``) to the
    subprocess function it stands for. Star aliases are skipped: a wildcard
    import is rejected outright.
    """
    module_aliases = {}
    function_bindings = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                module_aliases[alias.asname or root] = root
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0 and node.module == "subprocess":
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    function_bindings[alias.asname or alias.name] = alias.name
    return module_aliases, function_bindings


def _resolve_dotted_name(node, module_aliases):
    """Module root and attribute path behind a dotted expression, else None.

    A chain such as ``subprocess.subprocess.run`` unwraps to the root Name
    whose import binding gives the module root; the attribute segments are
    returned in order. Returns ``(root, segments)`` — ``segments`` is empty
    for a bare Name — or ``None`` when the chain does not end in a plain
    Name (for example one produced by a call), which the dataflow cannot
    resolve.
    """
    segments = []
    current = node
    while isinstance(current, ast.Attribute):
        segments.append(current.attr)
        current = current.value
    if not isinstance(current, ast.Name):
        return None
    root = module_aliases.get(current.id, current.id)
    segments.reverse()
    return root, segments


def _is_subprocess_call(node, module_aliases, function_bindings):
    """Whether one Call node spawns through ``subprocess`` in any binding."""
    func = node.func
    if isinstance(func, ast.Name):
        return func.id in function_bindings
    if isinstance(func, ast.Attribute):
        resolved = _resolve_dotted_name(func, module_aliases)
        if not resolved:
            return False
        root, segments = resolved
        if not segments:
            return False
        return root == "subprocess" and segments[-1] in SUBPROCESS_FUNCTIONS
    return False


def _subprocess_call_label(func, module_aliases, function_bindings):
    """Human-readable label for one resolved subprocess call target."""
    if isinstance(func, ast.Name):
        return "subprocess.%s" % function_bindings[func.id]
    resolved = _resolve_dotted_name(func, module_aliases)
    if resolved:
        return "subprocess.%s" % ".".join(resolved[1])
    return "subprocess.<unresolved>"


def _is_pathish(node, path_names):
    """Whether the expression looks like a pathlib Path value."""
    if isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id == "Path":
            return True
        # Method chains such as Path(__file__).resolve().parents[1] end in a
        # Path() call, so walk the receiver of the call itself.
        return _is_pathish(node.func, path_names)
    if isinstance(node, ast.Attribute):
        return _is_pathish(node.value, path_names)
    if isinstance(node, ast.Subscript):
        # Path(__file__).resolve().parents[1] and similar chains end in a Path.
        return _is_pathish(node.value, path_names)
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
        # Path / str joins stay Path values; str / str is never valid.
        return _is_pathish(node.left, path_names) or _is_pathish(node.right, path_names)
    if isinstance(node, ast.Name):
        return node.id in path_names
    return False


def _module_level_path_names(tree):
    """Module-level names assigned a Path-like value."""
    names = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and _is_pathish(node.value, names):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)
    return names


def _check_imports(roots, findings):
    outside = roots - ALLOWED_IMPORT_ROOTS - ALLOWED_SIBLING_IMPORTS
    if outside:
        _finding(
            findings,
            "import roots outside the pinned allowlist: %s" % sorted(outside),
        )
    network = roots & NETWORK_MODULE_ROOTS
    if network:
        _finding(findings, "network-capable module import: %s" % sorted(network))
    write_modules = roots & WRITE_MODULE_ROOTS
    if write_modules:
        _finding(findings, "file-mutating module import: %s" % sorted(write_modules))


def _check_open_call(node, findings, label="open()", mode_index=1):
    """Property 5: reject write-capable or un-auditable open() modes.

    ``mode_index`` is the positional mode slot: 1 for the builtin ``open()``
    (``open(path, mode)``) and 0 for ``Path.open()`` (``path.open(mode)``).
    Without an explicit mode both default to reading.
    """
    mode = None
    if len(node.args) > mode_index:
        mode = node.args[mode_index]
    for keyword in node.keywords:
        if keyword.arg == "mode":
            mode = keyword.value
    if mode is None:
        if any(isinstance(argument, ast.Starred) for argument in node.args):
            _finding(
                findings,
                "%s at line %d takes *args, so the mode cannot be audited"
                % (label, node.lineno),
            )
        return
    if not isinstance(mode, ast.Constant) or not isinstance(mode.value, str):
        _finding(
            findings,
            "%s at line %d has a non-literal mode and cannot be audited"
            % (label, node.lineno),
        )
        return
    if any(character in mode.value for character in WRITE_MODE_CHARS):
        _finding(
            findings,
            "%s at line %d uses mode %r, which can write"
            % (label, node.lineno, mode.value),
        )


def _check_calls(
    call_nodes, path_names, function_bindings, module_aliases, findings
):
    """Properties 2 and 3, plus the method part of property 5."""
    for node in call_nodes:
        func = node.func
        if isinstance(func, ast.Name):
            if func.id in FORBIDDEN_BUILTIN_CALLS:
                _finding(
                    findings,
                    "forbidden call %s() at line %d" % (func.id, node.lineno),
                )
            if func.id == "open":
                _check_open_call(node, findings)
            if func.id in function_bindings:
                _check_subprocess_call(
                    node,
                    _subprocess_call_label(func, module_aliases, function_bindings),
                    findings,
                )
        elif isinstance(func, ast.Attribute):
            attr = func.attr
            receiver = func.value
            receiver_root = _resolve_receiver_root(receiver, module_aliases)
            if receiver_root == "os" and attr in FORBIDDEN_OS_METHODS:
                _finding(
                    findings,
                    "forbidden attribute call os.%s() at line %d"
                    % (attr, node.lineno),
                )
            resolved = _resolve_dotted_name(func, module_aliases)
            if (
                resolved
                and resolved[0] == "subprocess"
                and resolved[1]
                and resolved[1][-1] in SUBPROCESS_FUNCTIONS
            ):
                _check_subprocess_call(
                    node,
                    _subprocess_call_label(func, module_aliases, function_bindings),
                    findings,
                )
            if attr in UNCONDITIONAL_WRITE_METHODS:
                _finding(
                    findings,
                    "path-mutating method call .%s() at line %d"
                    % (attr, node.lineno),
                )
            elif attr == "replace" and _is_pathish(receiver, path_names):
                _finding(
                    findings,
                    "Path.replace() call at line %d mutates the file system"
                    % node.lineno,
                )
            elif attr == "open" and _is_pathish(receiver, path_names):
                _check_open_call(node, findings, label="path .open()", mode_index=0)


def _resolve_receiver_root(receiver, module_aliases):
    """Module root behind a call receiver that is a plain Name, else None."""
    if isinstance(receiver, ast.Name):
        return module_aliases.get(receiver.id, receiver.id)
    return None


def _check_spawn_references(
    call_nodes, tree, module_aliases, function_bindings, findings
):
    """Property 2: a spawn function may only be referenced to call it.

    Every ``subprocess.<name>`` reference whose final attribute resolves to a
    spawn function (through any number of attribute segments) and every
    from-imported spawn name must be the callable of a direct call. Any other
    appearance — a rebinding such as ``runner = subprocess.run`` or
    ``runner = run`` (plain, annotated or walrus), an element or argument
    inside a container or call, or a returned reference — is rejected
    fail-closed: the auditor cannot promise to track every later use of such
    a name, so the shape is refused instead of followed.
    """
    allowed_callable_ids = set()
    for node in call_nodes:
        func = node.func
        if _is_subprocess_call(node, module_aliases, function_bindings):
            allowed_callable_ids.add(id(func))
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            resolved = _resolve_dotted_name(node, module_aliases)
            if not resolved:
                continue
            root, segments = resolved
            if root != "subprocess" or not segments:
                continue
            final = segments[-1]
            if final not in SUBPROCESS_FUNCTIONS:
                continue
            if id(node) in allowed_callable_ids:
                continue
            _finding(
                findings,
                "subprocess spawn function '%s' is referenced without being "
                "called at line %d; a rebound or aliased reference (for "
                "example `runner = subprocess.run`) cannot be tracked, so "
                "the function must be called directly as subprocess.%s(...)"
                % (".".join(segments), node.lineno, final),
            )
        elif isinstance(node, ast.Name):
            if node.id in function_bindings and id(node) not in allowed_callable_ids:
                _finding(
                    findings,
                    "subprocess spawn function '%s' (from-imported as '%s') "
                    "is referenced without being called at line %d; the "
                    "function must be called directly as %s(...)"
                    % (
                        function_bindings[node.id],
                        node.id,
                        node.lineno,
                        node.id,
                    ),
                )


def _check_subprocess_call(node, label, findings):
    """Property 3: a literal list or tuple starting with "git" pinning a verb."""
    for keyword in node.keywords:
        if keyword.arg == "shell":
            if not (
                isinstance(keyword.value, ast.Constant)
                and keyword.value.value is False
            ):
                _finding(
                    findings,
                    "%s at line %d passes a shell keyword that is not literal "
                    "False" % (label, node.lineno),
                )
    if not node.args:
        uses_args_keyword = any(keyword.arg == "args" for keyword in node.keywords)
        _finding(
            findings,
            "%s at line %d passes %s; only a list or tuple literal whose "
            "first element is 'git' and whose second element pins a "
            "read-only verb is audited"
            % (label, node.lineno, "args=" if uses_args_keyword else "no command"),
        )
        return
    first = node.args[0]
    if not isinstance(first, (ast.List, ast.Tuple)):
        _finding(
            findings,
            "%s at line %d passes a non-literal command; the first positional "
            "argument must be a list or tuple literal starting with 'git' and "
            "pinning a verb" % (label, node.lineno),
        )
        return
    if not (
        first.elts
        and isinstance(first.elts[0], ast.Constant)
        and first.elts[0].value == "git"
    ):
        _finding(
            findings,
            "%s at line %d must start its command list with the constant "
            "string 'git'" % (label, node.lineno),
        )
        return
    if len(first.elts) < 2:
        _finding(
            findings,
            "%s at line %d must pass the git verb as the second command "
            "element" % (label, node.lineno),
        )
        return
    second = first.elts[1]
    if isinstance(second, ast.Starred):
        # The audited git() wrapper's dynamic passthrough: its verbs are
        # pinned at every git() call site by property 4. The carve-out is
        # shape-based, not call-site based, so any argv of this shape passes
        # here and such a site's argv needs manual review.
        return
    if not (isinstance(second, ast.Constant) and isinstance(second.value, str)):
        _finding(
            findings,
            "%s at line %d must pin the git verb as a constant second command "
            "element" % (label, node.lineno),
        )
        return
    if second.value not in EXPECTED_GIT_VERBS:
        _finding(
            findings,
            "%s at line %d runs subprocess verb %r, which is outside the "
            "pinned read-only git verb set %s"
            % (label, node.lineno, second.value, sorted(EXPECTED_GIT_VERBS)),
        )


def _git_verb_from_subprocess_call(node):
    """Constant verb element at a subprocess call site, for the derived set."""
    if not node.args:
        return None
    first = node.args[0]
    if not isinstance(first, (ast.List, ast.Tuple)) or len(first.elts) < 2:
        return None
    second = first.elts[1]
    if isinstance(second, ast.Constant) and isinstance(second.value, str):
        return second.value
    return None


def _check_git_verbs(call_nodes, subprocess_nodes, findings):
    """Property 4: derive the git verbs over all call sites; pin the set exactly.

    Verbs are collected from the local ``git()`` helper call sites (the
    literal first argument is the verb) and from ``subprocess`` call sites
    (the constant second command element after the ``"git"`` head). The
    dynamic ``*args`` passthrough of the ``git()`` wrapper contributes no
    verb itself: each of its call sites is pinned instead.
    """
    verbs = set()
    for node in call_nodes:
        if isinstance(node.func, ast.Name) and node.func.id == "git":
            if not node.args:
                _finding(
                    findings,
                    "git() call at line %d without a verb argument" % node.lineno,
                )
                continue
            first = node.args[0]
            if (
                isinstance(first, ast.Starred)
                or not isinstance(first, ast.Constant)
                or not isinstance(first.value, str)
            ):
                _finding(
                    findings,
                    "git() first argument at line %d must be a constant verb "
                    "string" % node.lineno,
                )
                continue
            verbs.add(first.value)
    for node in subprocess_nodes:
        verb = _git_verb_from_subprocess_call(node)
        if verb is not None:
            verbs.add(verb)
    missing = EXPECTED_GIT_VERBS - verbs
    unexpected = verbs - EXPECTED_GIT_VERBS
    if missing or unexpected:
        _finding(
            findings,
            "git verb set differs from the pinned read-only set: "
            "missing=%s unexpected=%s; update EXPECTED_GIT_VERBS only after "
            "an explicit review of the new verb"
            % (sorted(missing), sorted(unexpected)),
        )
    return verbs


def audit_module(path):
    """Audit one Python module statically; return the number of findings."""
    findings = []
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    import_nodes = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
    ]
    call_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    roots = _import_roots(tree, findings)
    _check_imports(roots, findings)
    module_aliases, function_bindings = _subprocess_import_bindings(tree)
    subprocess_nodes = [
        node
        for node in call_nodes
        if _is_subprocess_call(node, module_aliases, function_bindings)
    ]
    path_names = _module_level_path_names(tree)
    _check_spawn_references(
        call_nodes, tree, module_aliases, function_bindings, findings
    )
    _check_calls(
        call_nodes, path_names, function_bindings, module_aliases, findings
    )
    verbs = _check_git_verbs(call_nodes, subprocess_nodes, findings)
    if findings:
        print(
            "FAIL audit: %s with %d finding(s)" % (path.name, len(findings)),
            file=sys.stderr,
        )
        return len(findings)
    print(
        "PASS audit: %s passed %d static properties (imports and wildcard "
        "rejection, network modules, forbidden calls and spawn references, "
        "subprocess shape and verb pin, git verb pin, write access) across "
        "%d imports, %d call sites, %d subprocess sites and %d git verbs"
        % (
            path.name,
            CHECKED_PROPERTIES,
            len(import_nodes),
            len(call_nodes),
            len(subprocess_nodes),
            len(verbs),
        )
    )
    return 0


def main():
    return audit_module(AUDITED_MODULE)


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
