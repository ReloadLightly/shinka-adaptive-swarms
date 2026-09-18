"""Prospective scientific policy boundary, independent of the frozen reference engine.

Inspect compiled Java17 class files without loading or executing candidate code.
This is a deliberately small allowed language, not a general-purpose JVM sandbox.
The caller must run this after compilation and on cached classes before execution,
and include the guard identity in future candidate/cache receipts. Existing
reference results and their immutable engine identity are not changed here.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
import struct

SCHEMA = "paper-policy-compiled-guard-v1"
POLICY_CLASS = "CandidatePolicy"
_LOADED_SOURCE_SHA256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


class PolicyValidationError(ValueError):
    """Compiled code exceeds the declared scientific policy capabilities."""


def guard_identity():
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != _LOADED_SOURCE_SHA256:
        raise PolicyValidationError("Policy guard changed after import; restart before validating code")
    return {"schema": SCHEMA, "source_sha256": _LOADED_SOURCE_SHA256}


def _methods():
    allowed = {
        ("java/lang/Object", "<init>", "()V"),
        ("paper/Memory", "get", "(I)D"),
        ("paper/Memory", "set", "(ID)V"),
        ("paper/Memory", "size", "()I"),
        ("paper/Offer", "observation", "()Lpaper/Observation;"),
        ("paper/Offer", "proposer", "()I"),
        ("paper/Offer", "layer", "()I"),
        ("paper/Offer", "utilityIfAccepted", "()D"),
        ("paper/Offer", "gain", "()D"),
        ("paper/Offer", "originalAcceptance", "()Lpaper/Decision;"),
        ("paper/Decision", "<init>", "(ZD)V"),
        ("paper/Decision", "yes", "()Lpaper/Decision;"),
        ("paper/Decision", "no", "()Lpaper/Decision;"),
        ("paper/Decision", "random", "(D)Lpaper/Decision;"),
        ("paper/Decision", "stochastic", "()Z"),
        ("paper/Decision", "probability", "()D"),
    }
    turn = {
        "observation": "()Lpaper/Observation;", "neighbors": "(I)[I",
        "neighborsOfNeighbor": "(II)[I", "randomActor": "()I", "randomUnit": "()D",
        "inspectAdd": "(II)D", "inspectDrop": "(II)D", "inspectRewire": "(IIII)D",
        "add": "(II)Z", "drop": "(II)V", "rewire": "(IIII)Z",
        "noOp": "()V", "originalTurn": "()V",
    }
    allowed.update(("paper/Turn", name, descriptor) for name, descriptor in turn.items())
    observation = {
        "I": "actor population ownTurns degree0 degree1 triangles0 triangles1 overlap searchSize previousPartner previousLayer",
        "J": "eventId activationId microstep previousEventId",
        "D": "time utility utilityChange cost0 cost1 triangleBenefit spilloverBenefit configuredNoise",
        "Ljava/lang/String;": "interpretation previousOutcome",
    }
    for result, names in observation.items():
        allowed.update(("paper/Observation", name, "()" + result) for name in names.split())
    pure_math = {
        "(D)D": "sin cos tan asin acos atan sinh cosh tanh sqrt cbrt exp expm1 log log10 log1p ceil floor rint signum ulp nextUp nextDown toDegrees toRadians abs",
        "(DD)D": "atan2 pow hypot IEEEremainder copySign nextAfter max min",
        "(DDD)D": "fma",
        "(F)F": "abs signum ulp nextUp nextDown", "(FF)F": "copySign max min",
        "(FFF)F": "fma", "(FD)F": "nextAfter",
        "(I)I": "abs absExact incrementExact decrementExact negateExact",
        "(J)J": "abs absExact incrementExact decrementExact negateExact",
        "(II)I": "min max addExact subtractExact multiplyExact floorDiv floorMod",
        "(JJ)J": "min max addExact subtractExact multiplyExact floorDiv floorMod",
        "(JI)J": "multiplyExact floorDiv", "(JI)I": "floorMod",
        "(J)I": "toIntExact", "(D)J": "round", "(F)I": "round getExponent",
        "(D)I": "getExponent", "(DI)D": "scalb", "(FI)F": "scalb",
    }
    for owner in ("java/lang/Math", "java/lang/StrictMath"):
        for descriptor, names in pure_math.items():
            allowed.update((owner, name, descriptor) for name in names.split())
    for owner, argument in (("java/lang/Double", "D"), ("java/lang/Float", "F")):
        allowed.update((owner, name, "(" + argument + ")Z") for name in ("isFinite", "isNaN", "isInfinite"))
        allowed.add((owner, "compare", "(" + argument * 2 + ")I"))
    strings = {
        "equals": "(Ljava/lang/Object;)Z", "equalsIgnoreCase": "(Ljava/lang/String;)Z",
        "length": "()I", "isEmpty": "()Z", "charAt": "(I)C",
        "startsWith": "(Ljava/lang/String;)Z", "endsWith": "(Ljava/lang/String;)Z",
        "compareTo": "(Ljava/lang/String;)I",
    }
    allowed.update(("java/lang/String", name, descriptor) for name, descriptor in strings.items())
    return frozenset(allowed)


ALLOWED_METHODS = _methods()
ALLOWED_CLASSES = frozenset({POLICY_CLASS, "paper/ActorPolicy"} | {owner for owner, _, _ in ALLOWED_METHODS})
REQUIRED_METHODS = {
    ("act", "(Lpaper/Turn;Lpaper/Memory;)V"),
    ("accept", "(Lpaper/Offer;Lpaper/Memory;)Lpaper/Decision;"),
}


class _Reader:
    def __init__(self, data):
        self.data, self.position = data, 0

    def take(self, count):
        if count < 0 or self.position + count > len(self.data):
            raise PolicyValidationError("Truncated or malformed class file")
        result = self.data[self.position:self.position + count]
        self.position += count
        return result

    def u1(self):
        return self.take(1)[0]

    def u2(self):
        return struct.unpack(">H", self.take(2))[0]

    def u4(self):
        return struct.unpack(">I", self.take(4))[0]

    def end(self):
        if self.position != len(self.data):
            raise PolicyValidationError("Unexpected trailing class-file data")


class _Class:
    def __init__(self, data):
        reader = _Reader(data)
        if reader.u4() != 0xCAFEBABE:
            raise PolicyValidationError("Invalid Java class-file magic")
        minor, major = reader.u2(), reader.u2()
        if (minor, major) != (0, 61):
            raise PolicyValidationError("Require ordinary Java17 release class files (no preview)")
        self.pool = [None] * reader.u2()
        index = 1
        while index < len(self.pool):
            tag = reader.u1()
            if tag == 1:
                raw = reader.take(reader.u2())
                try:
                    value = raw.replace(b"\xc0\x80", b"\x00").decode("utf-8", "surrogatepass")
                except UnicodeDecodeError as error:
                    raise PolicyValidationError("Invalid constant-pool UTF8") from error
            elif tag in (3, 4):
                value = reader.take(4)
            elif tag in (5, 6):
                value = reader.take(8)
            elif tag in (7, 8, 16, 19, 20):
                value = reader.u2()
            elif tag in (9, 10, 11, 12, 17, 18):
                value = (reader.u2(), reader.u2())
            elif tag == 15:
                value = (reader.u1(), reader.u2())
            else:
                raise PolicyValidationError(f"Unsupported constant-pool tag {tag}")
            self.pool[index] = (tag, value)
            index += 2 if tag in (5, 6) else 1
            if index > len(self.pool):
                raise PolicyValidationError("Invalid wide constant-pool slot")
        self.flags = reader.u2()
        self.name, self.parent = self.class_name(reader.u2()), self.class_name(reader.u2())
        self.interfaces = [self.class_name(reader.u2()) for _ in range(reader.u2())]
        self.fields = self.members(reader)
        self.methods = self.members(reader)
        self.attributes = self.attributes_at(reader)
        reader.end()

    def item(self, index, expected):
        if not 0 < index < len(self.pool) or self.pool[index] is None or self.pool[index][0] != expected:
            raise PolicyValidationError("Invalid constant-pool reference")
        return self.pool[index][1]

    def utf8(self, index):
        return self.item(index, 1)

    def class_name(self, index):
        return self.utf8(self.item(index, 7))

    def attributes_at(self, reader):
        attributes = {}
        for _ in range(reader.u2()):
            name = self.utf8(reader.u2())
            if name in attributes:
                raise PolicyValidationError("Duplicate class-file attribute")
            attributes[name] = reader.take(reader.u4())
        return attributes

    def members(self, reader):
        return [dict(flags=reader.u2(), name=self.utf8(reader.u2()), descriptor=self.utf8(reader.u2()),
                     attributes=self.attributes_at(reader)) for _ in range(reader.u2())]

    def reference(self, index):
        if not 0 < index < len(self.pool) or self.pool[index] is None or self.pool[index][0] not in (9, 10, 11):
            raise PolicyValidationError("Invalid class member reference")
        owner_index, pair_index = self.pool[index][1]
        name_index, descriptor_index = self.item(pair_index, 12)
        return self.class_name(owner_index), self.utf8(name_index), self.utf8(descriptor_index)


def _type(descriptor, position, allow_void=False):
    if position >= len(descriptor):
        raise PolicyValidationError("Malformed type descriptor")
    kind = descriptor[position]
    if kind == "[":
        return _type(descriptor, position + 1)
    if kind in "BCDFIJSZ" or (kind == "V" and allow_void):
        return position + 1
    if kind == "L":
        end = descriptor.find(";", position)
        if end >= 0 and descriptor[position + 1:end] in ALLOWED_CLASSES:
            return end + 1
    raise PolicyValidationError(f"Undeclared type descriptor: {descriptor}")


def _descriptor(descriptor):
    if not descriptor.startswith("("):
        raise PolicyValidationError("Expected method descriptor")
    position = 1
    while position < len(descriptor) and descriptor[position] != ")":
        position = _type(descriptor, position)
    if position >= len(descriptor) or _type(descriptor, position + 1, allow_void=True) != len(descriptor):
        raise PolicyValidationError("Malformed method descriptor")


def _code(clazz, method):
    if set(method["attributes"]) - {"Code", "MethodParameters"}:
        raise PolicyValidationError(f"Unexpected method metadata: {method['name']}")
    data = method["attributes"].get("Code")
    if data is None:
        raise PolicyValidationError("Every candidate method must contain ordinary bytecode")
    reader = _Reader(data)
    stack, locals_ = reader.u2(), reader.u2()
    bytecode = reader.take(reader.u4())
    if reader.u2():
        raise PolicyValidationError("Candidate exception handlers/monitor cleanup are outside the allowed language")
    attributes = clazz.attributes_at(reader)
    if set(attributes) - {"LineNumberTable", "LocalVariableTable", "LocalVariableTypeTable", "StackMapTable"}:
        raise PolicyValidationError("Unexpected bytecode metadata")
    reader.end()
    return stack, locals_, bytecode


def _validate(clazz):
    if clazz.name != POLICY_CLASS or clazz.parent != "java/lang/Object" or clazz.interfaces != ["paper/ActorPolicy"]:
        raise PolicyValidationError("Require CandidatePolicy directly implementing paper.ActorPolicy with Object superclass")
    if clazz.flags != 0x0031:  # ACC_PUBLIC | ACC_FINAL | ACC_SUPER
        raise PolicyValidationError("Require an ordinary public final policy class")
    if clazz.fields:
        raise PolicyValidationError("All candidate instance/static fields are forbidden; use the supplied Memory")
    if set(clazz.attributes) - {"SourceFile"}:
        raise PolicyValidationError("Nested classes, dynamic linkage and undeclared class metadata are forbidden")
    declared = {(m["name"], m["descriptor"]) for m in clazz.methods}
    if len(declared) != len(clazz.methods) or not REQUIRED_METHODS <= declared:
        raise PolicyValidationError("Missing or duplicate policy entrypoint methods")
    references = []
    for index, item in enumerate(clazz.pool):
        if item is None:
            continue
        tag, value = item
        if tag == 7:
            name = clazz.class_name(index)
            if name.startswith("["):
                if _type(name, 0) != len(name):
                    raise PolicyValidationError("Invalid array class descriptor")
            elif name not in ALLOWED_CLASSES:
                raise PolicyValidationError(f"Undeclared class reference: {name}")
        elif tag == 9:
            raise PolicyValidationError("All field accesses are forbidden, including foreign shared fields")
        elif tag in (10, 11):
            owner, name, descriptor = clazz.reference(index)
            _descriptor(descriptor)
            if owner == POLICY_CLASS:
                if (name, descriptor) not in declared:
                    raise PolicyValidationError("Undeclared self method reference")
            elif (owner, name, descriptor) not in ALLOWED_METHODS:
                raise PolicyValidationError(f"Undeclared API: {owner}.{name}{descriptor}")
            references.append((owner, name, descriptor))
        elif tag in (15, 16, 17, 18, 19, 20):
            raise PolicyValidationError("Dynamic linkage, method handles and module access are forbidden")
    constructors = 0
    for method in clazz.methods:
        flags, name, descriptor = method["flags"], method["name"], method["descriptor"]
        _descriptor(descriptor)
        if flags & (0x0100 | 0x0400 | 0x0020):  # native, abstract, synchronized
            raise PolicyValidationError("Native, abstract and synchronized candidate methods are forbidden")
        if (name, descriptor) in REQUIRED_METHODS and flags != 0x0001:
            raise PolicyValidationError("Policy entrypoints must be ordinary public instance methods")
        stack, locals_, code = _code(clazz, method)
        if name == "<clinit>":
            raise PolicyValidationError("Static initializers are forbidden")
        if name == "<init>":
            constructors += 1
            if descriptor != "()V" or flags != 0x0001 or stack != 1 or locals_ != 1 or len(code) != 5 or code[:2] != b"\x2a\xb7" or code[-1:] != b"\xb1":
                raise PolicyValidationError("Only a side-effect-free public default constructor is permitted")
            if clazz.reference(struct.unpack(">H", code[2:4])[0]) != ("java/lang/Object", "<init>", "()V"):
                raise PolicyValidationError("Constructor may only call Object's constructor")
    if constructors != 1:
        raise PolicyValidationError("Exactly one side-effect-free constructor is required")
    return references


def validate_compiled(directory):
    """Return a hashable receipt or raise PolicyValidationError; never run/load code.

    There must be exactly one emitted CandidatePolicy.class. Ordinary helper
    methods and local primitive arrays are supported; fields, extra/nested
    classes, exception handlers and dynamic-language features are deliberately
    excluded. JVM/process resource limits remain the caller's responsibility.
    """
    directory = Path(directory)
    if directory.is_symlink() or not directory.is_dir():
        raise PolicyValidationError("Expected a real compiled-policy directory")
    files = sorted(directory.rglob("*.class"))
    if not files:
        raise PolicyValidationError("No compiled candidate class")
    parsed, hashes = {}, {}
    for path in files:
        if path.is_symlink():
            raise PolicyValidationError("Symlinked candidate classes are forbidden")
        data = path.read_bytes()
        if len(data) > 1024 * 1024:
            raise PolicyValidationError("Candidate class exceeds the structural inspection limit")
        clazz = _Class(data)
        if clazz.fields:
            raise PolicyValidationError(f"Fields are forbidden in every emitted class: {clazz.name}")
        name = path.relative_to(directory).as_posix()
        parsed[name] = clazz
        hashes[name] = hashlib.sha256(data).hexdigest()
    if list(parsed) != ["CandidatePolicy.class"]:
        raise PolicyValidationError("Unexpected additional or nested emitted candidate classes")
    references = _validate(parsed["CandidatePolicy.class"])
    return {"schema": SCHEMA, "guard_identity": guard_identity(), "class_files": hashes,
            "policy_class": POLICY_CLASS, "checked_classes": 1, "fields": 0,
            "method_reference_count": len(references), "pass": True}
