#
# Copyright (c) 2014, Arista Networks, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
#   Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
#   Redistributions in binary form must reproduce the above copyright
#   notice, this list of conditions and the following disclaimer in the
#   documentation and/or other materials provided with the distribution.
#
#   Neither the name of Arista Networks nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL ARISTA NETWORKS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE
# OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
# IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

import collections.abc
import inspect
import logging
import re
import string  # pylint: disable=W0402

from ztpserver.config import runtime
from ztpserver.utils import expand_range, parse_interface

REQUIRED_PATTERN_ATTRIBUTES = ["name", "definition"]
OPTIONAL_PATTERN_ATTRIBUTES = ["node", "variables", "interfaces", "model", "config_handler"]
INTERFACE_PATTERN_KEYWORDS = ["any", "none"]
ANTINODE_PATTERN = rf"[^{string.hexdigits}]"
KW_ANY_RE = re.compile(r" *any *")
KW_NONE_RE = re.compile(r" *none *")
WC_PORT_RE = re.compile(r".*")

INVALID_INTERFACE_PATTERNS = [
    (KW_ANY_RE, KW_ANY_RE, KW_NONE_RE),
    (KW_ANY_RE, KW_NONE_RE, KW_NONE_RE),
    (KW_ANY_RE, KW_NONE_RE, KW_ANY_RE),
    (KW_ANY_RE, KW_NONE_RE, WC_PORT_RE),
    (KW_NONE_RE, KW_ANY_RE, KW_ANY_RE),
    (KW_NONE_RE, KW_ANY_RE, KW_NONE_RE),
    (KW_NONE_RE, KW_NONE_RE, WC_PORT_RE),
    (KW_NONE_RE, KW_NONE_RE, KW_ANY_RE),
]

log = logging.getLogger(__name__)  # pylint: disable=C0103


class ValidationError(Exception):
    """Base error class for validation failures"""


class Validator:
    def __init__(self, node_id):
        self.node_id = node_id
        self.data = {}
        self.fail = False
        self.errors = []

    def validate(self, data=None):
        log.debug("%s: running %s.validate", self.node_id, self.__class__.__name__)
        if data:
            self.data = data
        else:
            self.data = {}

        error = None
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for name in methods:
            if name[0].startswith("validate_"):
                if "name" not in self.data:
                    name_string = ""
                else:
                    name_string = f"for '{self.data['name']}'"

                log.debug(
                    "%s: running %s.%s %s",
                    self.node_id,
                    self.__class__.__name__,
                    name[0],
                    name_string,
                )
                try:
                    getattr(self, name[0])()
                except ValidationError as err:
                    if not error:
                        error = err
        if error:
            self.error(error)

        return not self.fail

    def error(self, err, *args, **kwargs):
        # pylint: disable=W0613
        cls = str(self.__class__).split("'")[1].split(".")[-1]
        log.error("%s: %s validation error: %s", self.node_id, cls, err)
        self.fail = True


class NeighbordbValidator(Validator):
    def __init__(self, node_id):
        self.invalid_patterns = set()
        self.valid_patterns = set()
        super().__init__(node_id)

    def validate_variables(self):
        variables = self.data.get("variables", None)
        if variables is not None:
            if not hasattr(variables, "__iter__"):
                raise ValidationError(f"invalid global variables value ({variables})")

    def validate_patterns(self):
        patterns = self.data.get("patterns", None)

        if not patterns:
            log.warning("%s: no patterns found in neighbordb (%s)", self.node_id, self.data)
            return

        for index, entry in enumerate(patterns):
            name = entry.get("name", None)

            validator = PatternValidator(self.node_id)

            if name and validator.validate(entry):
                log.debug(
                    "%s: adding pattern '%s' (%s) to valid patterns",
                    self.node_id,
                    name,
                    entry,
                )
                self.valid_patterns.add((index, str(name)))
            else:
                if not name:
                    name = "N/A"
                log.debug(
                    "%s: adding pattern '%s' (%s) to invalid patterns",
                    self.node_id,
                    name,
                    entry,
                )
                self.invalid_patterns.add((index, str(name)))

        if self.invalid_patterns:
            raise ValidationError(f"invalid patterns: {self.invalid_patterns}")


class PatternValidator(Validator):
    def __init__(self, node_id):
        self.invalid_interface_patterns = set()
        self.valid_interface_patterns = set()
        super().__init__(node_id)

    def validate_attributes(self):
        for attr in REQUIRED_PATTERN_ATTRIBUTES:
            if attr not in self.data:
                raise ValidationError(f"missing attribute: {attr}")

        if "node" not in self.data and "model" not in self.data and "interfaces" not in self.data:
            raise ValidationError("missing attribute: 'node' OR 'model' OR 'interfaces'")

        if "node" in self.data and "model" in self.data:
            raise ValidationError("'node' AND 'model' are mutually exclusive")

        for attr in self.data:
            if attr not in REQUIRED_PATTERN_ATTRIBUTES + OPTIONAL_PATTERN_ATTRIBUTES:
                raise ValidationError(f"{attr} not allowed")

    def validate_name(self):
        if not self.data or "name" not in self.data:
            raise ValidationError("missing attribute: 'name'")

        if self.data["name"] is None or not isinstance(self.data["name"], (int, str)):
            raise ValidationError(f"invalid value for 'name' ({self.data['name']})")

    def validate_interfaces(self):
        if not self.data:
            return

        if "interfaces" not in self.data:
            return

        if not isinstance(self.data["interfaces"], collections.abc.Iterable):
            raise ValidationError(f"'interfaces' is not iterable ({self.data['interfaces']})")

        for index, pattern in enumerate(self.data["interfaces"]):
            if not isinstance(pattern, collections.abc.Mapping):
                raise ValidationError(f"invalid value for interface pattern ({pattern})")

            validator = InterfacePatternValidator(self.node_id)

            if validator.validate(pattern):
                log.debug(
                    "%s: adding interface pattern '%s' to valid interface patterns",
                    self.node_id,
                    repr(pattern),
                )
                self.valid_interface_patterns.add((index, repr(pattern)))
            else:
                log.debug(
                    "%s: adding interface pattern '%s' to invalid interface patterns",
                    self.node_id,
                    repr(pattern),
                )
                self.invalid_interface_patterns.add((index, repr(pattern)))

        if self.invalid_interface_patterns:
            raise ValidationError(f"invalid interface patterns: {self.invalid_interface_patterns}")

    def validate_definition(self):
        if not self.data:
            return

        if "definition" not in self.data:
            return

        if not isinstance(self.data["definition"], (int, str)):
            raise ValidationError(f"invalid value for 'definition' ({self.data['definition']})")

        for wspc in string.whitespace:
            if wspc in self.data["definition"]:
                raise ValidationError(
                    f"invalid value for 'definition' "
                    f"({self.data['definition']}) - '{wspc}' not allowed"
                )

    def validate_node(self):
        if not self.data:
            return

        node = self.data.get("node", None)
        if not node:
            return

        if isinstance(node, int):
            node = str(node)

        if not isinstance(node, str):
            raise ValidationError(f"invalid value for 'node' ({str(node)})")

        # if system MAC is used
        if runtime.default.identifier == "systemmac":
            node = node.replace(":", "").replace(".", "")
            if re.search(ANTINODE_PATTERN, node):
                raise ValidationError(f"invalid value for 'node' ({node})")

    def validate_variables(self):
        if not self.data:
            return

        if "variables" not in self.data:
            return

        if "variables" in self.data:
            if not hasattr(self.data["variables"], "__iter__"):
                raise ValidationError(
                    f"invalid value for 'variables' "
                    f"(expecting iterable object, got: {self.data['variables']})"
                )


class InterfacePatternValidator(Validator):
    def validate_interface_pattern(self):
        for interface, peer in self.data.items():
            if peer is None:
                raise ValidationError(f"missing peer for interface {interface}")

            try:
                (device, port) = parse_interface(peer, self.node_id)
            except Exception as err:
                raise ValidationError(f"PatternError: {err}") from err

            if interface not in INTERFACE_PATTERN_KEYWORDS:
                try:
                    for entry in expand_range(interface):
                        self._validate_pattern(entry, device, port)
                except Exception as err:
                    raise ValidationError(f"invalid interface {interface} ({err})") from err
            else:
                self._validate_pattern(interface, device, port)

    def _validate_pattern(self, interface, device, port):
        if KW_NONE_RE.match(interface) and KW_NONE_RE.match(device) and KW_NONE_RE.match(port):
            # no LLDP neighbors
            return

        for interface_re, device_re, port_re in INVALID_INTERFACE_PATTERNS:
            if interface_re.match(interface) and device_re.match(device) and port_re.match(port):
                raise ValidationError(
                    f"invalid interface pattern: ({interface}, {device}, {port}) matches "
                    f"({interface_re.pattern}, {device_re.pattern}, {port_re.pattern})"
                )


def _validator(contents, cls, node_id):
    try:
        validator = cls(node_id)
        result = validator.validate(contents)
        if result:
            log.debug("%s: %s validation successful", node_id, validator.__class__.__name__)
        else:
            log.debug("%s: %s validation failed", node_id, validator.__class__.__name__)

        return result
    except Exception as exc:
        log.error(
            "%s: failed to run validator %s(%s): %s",
            node_id,
            cls.__name__,
            contents,
            repr(exc),
        )
        raise


def validate_neighbordb(contents, node_id):
    return _validator(contents, NeighbordbValidator, node_id)


def validate_pattern(contents, node_id):
    return _validator(contents, PatternValidator, node_id)
