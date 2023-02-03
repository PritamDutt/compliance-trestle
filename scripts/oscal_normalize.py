# -*- mode:python; coding:utf-8 -*-

# Copyright (c) 2020 IBM Corp. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
r"""
Script to normalize oscal after significant changes with version 1.0.0.

It then reorders the classes so there are minimal forwards required.
This script is normally called by gen_oscal.py when models are generated.

gen_oscal.py only need to be run when there is a need to update the python oscal classes to track new schemas
in the nist-source repository at the nist oscal web site.  The local version of that site is cloned as a
submodule in the trestle directory, and it would only be updated if you run the git submodule update command
(see gen_oscal.py for details).

Normally the submodule is set to track the main, or release, branch of the nist-source - but there may be a need
to work with 'draft' versions of the schemas, which are found in the develop branch of nist-source.  In that case
the makefile should specify the develop branch for the submodule and execute the `git submodule update --remote` as
shown in the Makefile for trestle.

The main purpose of this script is to collapse the long-name versions of the classes into as simple a version as
possible, while also collecting common classes into a separate file, common.py.

The second purpose is to remove all the __root__ classes from common.py.  __root__ classes are classes that wrap a
single __root__ member in the class along with its type - which could be a simple string, integer, or complex regex.
If the __root__ classes are not removed, simple string assignment would look like:

param.values[0] = ParameterValue(__root__='foo')

instead of:

param.values[0] = 'foo'

The removal of __root__ is performed by extracting the type (and its possible regex) and substituting it in classes
that reference the __root__ class.  For example:

class StringDatatype(OscalBaseModel):
    __root__: constr(regex=r'^\S(.*\S)?$')

class Parameter(OscalBaseModel):
    values: Optional[List[StringDataType]] = Field(None)

In this case Parameter values reference a root class that is a constr type with regex, so we substitute the regex as:

class Parameter(OscalBaseModel):
    values: Optional[List[constr(regex=r'^\S(.*\S)?$')]] = Field(None)

This has no impact on internal validation of the values and performs identically without the need to wrap strings
in a StringDatatype with __root__ value specified.

For convenience the original root classes are left in common.py for reference, but the root classes should never
be referenced by name.

The only exception to this is OscalVersion, which has a special validator inserted by this script.

Note that __root__ classes in the other oscal .py files are left as-is since they don't tend to be referenced much
if at all in the trestle code - but they could also be removed by extensions to this script.

"""

import logging
import pathlib
import re

from trestle.oscal import OSCAL_VERSION_REGEX

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler())

class_header = 'class '

# List of filestems not including 'complete' or 'common'
# 'common' is generated by this script.  'complete.py' comes from NIST and is ignored
fstems = ['assessment_plan', 'assessment_results', 'catalog', 'component', 'poam', 'profile', 'ssp']

alias_map = {
    'assessment_plan': 'assessment-plan',
    'assessment_results': 'assessment-results',
    'catalog': 'catalog',
    'component': 'component-definition',
    'poam': 'plan-of-action-and-milestones',
    'profile': 'profile',
    'ssp': 'system-security-plan'
}

camel_map = {
    'assessment_plan': 'AssessmentPlan',
    'assessment_results': 'AssessmentResults',
    'catalog': 'Catalog',
    'component': 'ComponentDefinition',
    'poam': 'PlanOfActionAndMilestones',
    'profile': 'Profile',
    'ssp': 'SystemSecurityPlan'
}

prefix_map = {
    'assessment_plan': 'Ap',
    'assessment_results': 'Ar',
    'catalog': 'Cat',
    'component': 'Comp',
    'poam': 'Poam',
    'profile': 'Prof',
    'ssp': 'Ssp'
}

# these prefixes are stripped repeatedly from class names until no more changes
prefixes_to_strip = [
    'OscalMetadata',
    'OscalAssessmentCommon',
    'OscalImplementationCommon',
    'OscalComponentDefinition',
    'OscalCatalog',
    'OscalControl',
    'OscalMapping',
    'OscalSsp',
    'OscalPoam',
    'OscalProfile',
    'OscalAr',
    'OscalAp',
    'Common'
]

license_header = (
    '# -*- mode:python; coding:utf-8 -*-\n'
    '# Copyright (c) 2020 IBM Corp. All rights reserved.\n'
    '#\n'
    '# Licensed under the Apache License, Version 2.0 (the "License");\n'
    '# you may not use this file except in compliance with the License.\n'
    '# You may obtain a copy of the License at\n'
    '#\n'
    '#     https://www.apache.org/licenses/LICENSE-2.0\n'
    '#\n'
    '# Unless required by applicable law or agreed to in writing, software\n'
    '# distributed under the License is distributed on an "AS IS" BASIS,\n'
    '# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.\n'
    '# See the License for the specific language governing permissions and\n'
    '# limitations under the License.\n'
)

main_header = """
#
#
####### DO NOT EDIT DO NOT EDIT DO NOT EDIT DO NOT EDIT DO NOT EDIT ######
#                                                                        #
#        This file is automatically generated by gen_oscal.py            #
#                                                                        #
####### DO NOT EDIT DO NOT EDIT DO NOT EDIT DO NOT EDIT DO NOT EDIT ######
#
#
from __future__ import annotations

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import AnyUrl, EmailStr, Extra, Field, conint, constr, validator

from trestle.core.base_model import OscalBaseModel
from trestle.oscal import OSCAL_VERSION_REGEX, OSCAL_VERSION
"""

oscal_validator_code = """

    @validator('__root__')
    def oscal_version_is_valid(cls, v):
        p = re.compile(OSCAL_VERSION_REGEX)
        matched = p.match(v)
        if matched is None:
            raise ValueError(f'OSCAL version: {v} is not supported, use {OSCAL_VERSION} instead.')
        return v

"""


class RelOrder():
    """Capture relative location of each class in list to its refs and deps."""

    def __init__(self, max_index):
        """Initialize with size of list being reordered."""
        self.latest_dep = 0
        self.earliest_ref = max_index


class ClassText():
    """Hold class text as named blocks with references to the added classes and capture its refs."""

    def __init__(self, first_line, parent_name):
        """Construct with first line of class definition and store the parent file name."""
        self.lines = [first_line.rstrip()]
        n = first_line.find('(')
        self.name = first_line[len(class_header):n]
        self.parent_names = [parent_name]
        self.original_name = self.name
        self.unique_name = None
        self.refs = set()
        self.full_refs = set()
        self.found_all_links = False
        self.is_self_ref = False
        self.is_local = False
        self.body_text = None

    def add_line(self, line):
        """Add new line to class text."""
        self.lines.append(line)

    def add_ref_if_good(self, ref_name):
        """Add non-empty refs that are not in common."""
        if ref_name and 'common.' not in ref_name:
            self.refs.add(ref_name)

    def add_ref_pattern(self, p, line):
        """Add refs for new class names found based on pattern."""
        new_refs = p.findall(line)
        if new_refs:
            for r in new_refs:
                if type(r) == tuple:
                    for s in r:
                        self.add_ref_if_good(s)
                else:
                    self.add_ref_if_good(r)

    @staticmethod
    def find_index(class_text_list, name):
        """Find index of class in list by name."""
        nclasses = len(class_text_list)
        for i in range(nclasses):
            if class_text_list[i].name == name:
                return i
        return -1

    def generate_body_text(self):
        """Get body text with whitespace removed."""
        # The body starts after the first colon
        full_text = ''
        for line in self.lines:
            # this adds the line with whitespace removed
            full_text += ''.join(line.split(' '))
        colon = full_text.find(':')
        self.body_text = full_text[colon:]

    @staticmethod
    def generate_all_body_text(classes):
        """Get the body of all classes into text."""
        new_classes = []
        for c in classes:
            c.generate_body_text()
            new_classes.append(c)
        return new_classes

    def bodies_equal(self, other):
        """Are class bodies equal with whitespace ignored."""
        return self.body_text == other.body_text

    def add_all_refs(self, line):
        """Find all refd class names found in line and add to references."""
        # find lone strings with no brackets
        p = re.compile(r'.*\:\s*([^\s\[\]]+).*')
        self.add_ref_pattern(p, line)
        # find objects in one or more bracket sets with possible first token and comma
        p = re.compile(r'.*\[(?:(.*),\s*)?((?:\[??[^\[]*?))\]')
        self.add_ref_pattern(p, line)
        # add refs found in optional unions
        p = re.compile(r'.*Optional\[Union\[([^,]+)')
        self.add_ref_pattern(p, line)
        return line

    def find_direct_refs(self, class_names_list):
        """Find direct refs without recursion."""
        for ref in self.refs:
            if ref == self.name:
                self.is_self_ref = True
            if ref in class_names_list and not ref == self.name:
                self.full_refs.add(ref)
        if len(self.full_refs) == 0:
            self.found_all_links = True

    def find_order(self, class_text_list):
        """Find latest dep and earliest reference."""
        ro = RelOrder(len(class_text_list) - 1)
        # find first class that needs this class
        for i, ct in enumerate(class_text_list):
            if self.name in ct.full_refs:
                ro.earliest_ref = i
                break
        # find last class this one needs
        # make sure result is deterministic and does not depend on order from set
        sorted_ref_list = sorted(self.full_refs)
        for ref in sorted_ref_list:
            n = ClassText.find_index(class_text_list, ref)
            if n > ro.latest_dep:
                ro.latest_dep = n
        return ro

    def strip_prefix(self, prefix):
        """Strip the prefix from the class name only."""
        if self.name.startswith(prefix) and self.name != prefix:
            self.name = self.name.replace(prefix, '', 1)
            return True
        return False


def find_forward_refs(class_list, orders):
    """Find forward references within the file."""
    forward_names = set()
    for c in class_list:
        if c.is_self_ref:
            forward_names.add(c.name)
    for i in range(len(orders)):
        if orders[i].earliest_ref < i:
            forward_names.add(class_list[i].name)

    forward_refs = []
    for c in class_list:
        if c.name in forward_names:
            forward_refs.append(f'{c.name}.update_forward_refs()')
    return forward_refs


def reorder(fstem, class_list):
    """Reorder the class list based on the location of its refs and deps."""
    # build list of all class names defined in file
    all_class_names = []
    for c in class_list:
        all_class_names.append(c.name)

    dups = {x for x in all_class_names if all_class_names.count(x) > 1}
    if len(dups) > 0:
        logger.error(f'ERROR Duplicate classes in {fstem}: {" ".join(dups)}')

    # find direct references for each class in list
    for n, c in enumerate(class_list):
        c.find_direct_refs(all_class_names)
        class_list[n] = c

    # with full dependency info, now reorder the classes to remove forward refs
    did_swap = True
    loop_num = 0
    orders = None
    while did_swap and loop_num < 1000:
        did_swap = False
        orders = []
        # find the relative placement of each class in list to its references and dependencies
        for c in class_list:
            ro = c.find_order(class_list)
            orders.append(ro)
        # find first class in list out of place and swap its dependency upwards, then break/loop to find new order
        for i, ro in enumerate(orders):
            if ro.latest_dep <= i <= ro.earliest_ref:
                continue
            # pop the out-of-place earliest ref and put it in front
            ct = class_list.pop(ro.earliest_ref)
            class_list.insert(i, ct)
            did_swap = True
            break
        loop_num += 1
    if did_swap:
        logger.info('Excess iteration in reordering!')
    forward_refs = find_forward_refs(class_list, orders)

    # return reordered list of classes with no forward refs
    return class_list, forward_refs


def constrain_oscal_version(class_list):
    """Constrain allowed oscal version."""
    for j in range(len(class_list)):
        cls = class_list[j]
        for i in range(len(cls.lines)):
            line = cls.lines[i]
            nstart = line.find('oscal_version:')
            if nstart >= 0:
                nstr = line.find('str')
                if nstr >= 0:
                    cls.lines[i] = line.replace('str', f'constr(regex={OSCAL_VERSION_REGEX})')
                    class_list[j] = cls
    return class_list


def load_classes(fstem):
    """Load all classes from a python file."""
    all_classes = []
    header = []
    forward_refs = []

    class_text = None
    done_header = False

    fname = pathlib.Path('trestle/oscal/tmp') / (fstem + '.py')

    with open(fname, 'r', encoding='utf8') as infile:
        for r in infile.readlines():
            # collect forward references
            if r.find('.update_forward_refs()') >= 0:
                forward_refs.append(r)
            elif r.find(class_header) == 0:  # start of new class
                done_header = True
                if class_text is not None:  # we are done with current class so add it
                    all_classes.append(class_text)
                class_text = ClassText(r, fstem)
            else:
                if not done_header:  # still in header
                    header.append(r.rstrip())
                else:
                    # this may not be needed
                    p = re.compile(r'.*Optional\[Union\[([^,]+),.*List\[Any\]')
                    refs = p.findall(r)
                    if len(refs) == 1:
                        logger.info(f'Replaced Any with {refs[0]} in {fstem}')
                        r_orig = r
                        r = r.replace('List[Any]', f'List[{refs[0]}]')
                        logger.info(f'{r_orig} -> {r}')
                    class_text.add_line(r.rstrip())

    all_classes.append(class_text)  # don't forget final class

    # force all oscal versions to the current one
    all_classes = constrain_oscal_version(all_classes)
    return all_classes


def load_all_classes():
    """Load all classes from all files on per file basis."""
    all_classes = []
    for fstem in fstems:
        all_classes.extend(load_classes(fstem))
    return all_classes


def keep_distinct(a, b):
    """If class names don't resolve to the same value then keep separate."""
    # It is possible two classes with very different names have the same bodies
    # This is allowed if the names are different enough since they provide useful context
    stripped_classes = strip_prefixes([a, b])
    a = stripped_classes[0]
    b = stripped_classes[1]
    if a.name == b.name:
        return False
    return True


def find_unique_classes(all_classes):
    """Find unique classes based mainly on bodies."""
    unique_classes = []
    all_classes = ClassText.generate_all_body_text(all_classes)
    for a in all_classes:
        # ignore the Model class - it is added at end
        if a.name == 'Model':
            continue
        is_unique = True
        for i, u in enumerate(unique_classes):
            if a.bodies_equal(u):
                if keep_distinct(a, u):
                    continue
                is_unique = False
                unique_classes[i].parent_names.append(a.parent_names[0])
                break
        if is_unique:
            a.unique_name = a.name
            unique_classes.append(a)
    return unique_classes


def strip_prefixes(classes):
    """Strip prefixes from class names."""
    new_classes = []
    # are we stripping all names in a file
    full_file = len(classes) > 2
    all_names = [c.name for c in classes]
    for c in classes:
        made_change = True
        # keep stripping til clean
        while made_change:
            made_change = False
            for prefix in prefixes_to_strip:
                if c.strip_prefix(prefix):
                    # if we generated a collision with existing name, append integer
                    if full_file and c.name in all_names:
                        ii = 1
                        while f'c.name{ii}' in all_names:
                            ii += 1
                        c.name = f'{c.name}{ii}'
                    made_change = True
        new_classes.append(c)
    return new_classes


def fix_clashes(classes):
    """Fix clashes in names."""
    # If two classes have the same name and different bodies, adjust each name
    # Leave bodies alone
    # each new class name will be local to its one parent file
    nclasses = len(classes)
    changes = []
    for i in range(nclasses):
        for j in range(i + 1, nclasses):
            if classes[i].name == classes[j].name:
                a = classes[i]
                b = classes[j]
                if a.bodies_equal(b):
                    continue
                a_parents = a.parent_names
                b_parents = b.parent_names
                for a_parent in a_parents:
                    for b_parent in b_parents:
                        a_pre = prefix_map[a_parent]
                        a_new = a.name if a.name.startswith(a_pre) else a_pre + '_' + a.name
                        b_pre = prefix_map[b_parent]
                        b_new = b.name if b.name.startswith(b_pre) else b_pre + '_' + b.name
                        changes.append((a_parent, a.name, a_new))
                        changes.append((b_parent, b.name, b_new))

    # now make the actual class name changes
    new_classes = []
    for c in classes:
        for change in changes:
            for parent_name in c.parent_names:
                # find the one class with parent that matches the change - and change only its name
                if parent_name == change[0] and c.name == change[1]:
                    c.name = change[2]
                    # mark the class as local to the one file
                    c.is_local = True
                    break
        new_classes.append(c)
    return new_classes


def token_in_line(line, token):
    """Find if token is present in string."""
    # the second regex needs to include digits for Base64 vs. Base, Type vs. Type1 etc.
    pattern = r'(^|[^a-zA-Z_]+)' + token + r'($|[^a-zA-Z0-9_]+)'
    p = re.compile(pattern)
    hits = p.findall(line)
    return len(hits) > 0


def replace_token(line, str1, str2):
    """Replace token str1 with new str2 in line."""
    # pull out what you want to keep on left and right
    # rather than capture what you want and replace it
    if str1 not in line:
        return line
    pattern = r'(^|.*[^a-zA-Z_]+)' + str1 + r'($|[^a-zA-Z0-9_]+.*)'
    line = re.sub(pattern, r'\1' + str2 + r'\2', line)
    return line


def is_common(cls):
    """Class is not common if _ in name or only one parent."""
    if '_' in cls.name:
        return False
    if len(cls.parent_names) == 1:
        return False
    return True


def _list_to_file_classes(classes):
    file_classes = {}
    for stem in fstems:
        file_classes[stem] = []
    file_classes['common'] = []

    for c in classes:
        file_classes[c.parent_names[0]].append(c)
    return file_classes


def _file_classes_to_list(file_classes, exclude_common):
    classes = []
    for item in file_classes.items():
        if item[0] == 'common' and exclude_common:
            continue
        for c in item[1]:
            classes.append(c)
    return classes


def refine_split(file_classes):
    """Make sure no references in common link to the other files."""
    # get list of original names in current common file
    common_names = []
    for c in file_classes['common']:
        common_names.append(c.unique_name)

    # find all original names of classes in other files that shouldn't be refd by common
    names = set()
    for stem in fstems:
        for c in file_classes[stem]:
            if (c.is_local) or (c.unique_name not in common_names):
                names.add(c.unique_name)
    names = list(names)

    # if any common class references outside common - exclude it from common
    not_com = []
    for c in file_classes['common']:
        excluded = False
        for line in c.lines:
            if excluded:
                break
            if '"' not in line and "'" not in line:
                for name in names:
                    if token_in_line(line, name):
                        not_com.append(c.name)
                        excluded = True
                        break

    # remove all not_com from com and add to other files as needed by parents
    new_com = []
    for c in file_classes['common']:
        if c.name in not_com:
            for parent in c.parent_names:
                file_classes[parent].append(c)
        else:
            new_com.append(c)
    file_classes['common'] = new_com
    return file_classes


def _find_in_classes(name, file_classes):
    # debugging utility
    found = []
    for item in file_classes.items():
        for c in item[1]:
            if name in c.name:
                found.append((item[0], c.name))
    return found


def _find_in_class_list(name, classes):
    # debugging utility
    found = []
    for c in classes:
        if name in c.name:
            found.append((name, c.name))
    return found


def split_classes(classes):
    """Split into separate common and other files."""
    file_classes = {}
    for stem in fstems:
        file_classes[stem] = []
    file_classes['common'] = []
    com_names = []

    for c in classes:
        if is_common(c):
            if c.name not in com_names:
                com_names.append(c.name)
                file_classes['common'].append(c)
        else:
            # remove clash prefix from the class name if present
            # the prefix is removed from bodies after the split
            c.name = c.name.split('_')[-1]
            for parent in c.parent_names:
                # the class carries with it that it is local and bound to the parent
                file_classes[parent].append(c)

    # keep removing classes in com that have external dependencies until it is clean
    new_ncom = 0
    while new_ncom != len(file_classes['common']):
        new_ncom = len(file_classes['common'])
        file_classes = refine_split(file_classes)
    return file_classes


def reorder_classes(fstem, classes):
    """Reorder the classes to minimize needed forwards."""
    classes = sorted(classes, key=lambda c: c.name)
    new_classes = []
    for c in classes:
        for line in c.lines:
            _ = c.add_all_refs(line)
        new_classes.append(c)
    reordered, forward_refs = reorder(fstem, new_classes)
    return reordered, forward_refs


def write_oscal(classes, forward_refs, fstem):
    """Write out oscal.py with all classes in it."""
    with open(f'trestle/oscal/{fstem}.py', 'w', encoding='utf8') as out_file:
        is_common = fstem == 'common'

        out_file.write(license_header)
        out_file.write('\n')
        out_file.write(main_header)

        if not is_common:
            out_file.write('import trestle.oscal.common as common\n')
        out_file.write('\n\n')

        for c in classes:
            out_file.writelines('\n'.join(c.lines) + '\n')
            # add special validator for OscalVersion
            if c.name == 'OscalVersion':
                out_file.write(oscal_validator_code)

        if not is_common:
            out_file.writelines('class Model(OscalBaseModel):\n')
            alias = alias_map[fstem]
            snake = alias.replace('-', '_')
            class_name = camel_map[fstem]
            if '-' in alias:
                out_file.writelines(f"    {snake}: {class_name} = Field(..., alias='{alias}')\n")
            else:
                out_file.writelines(f'    {snake}: {class_name}\n')

        if forward_refs:
            if not is_common:
                out_file.writelines('\n\n')
            out_file.writelines('\n'.join(forward_refs) + '\n')


def apply_changes_to_class_list(classes, changes):
    """Make all changes to the name and body of a list of classes."""
    for i, c in enumerate(classes):
        lines = []
        for line in c.lines:
            if 'title=' not in line and 'description=' not in line:
                for item in changes:
                    if item[0] in line:
                        line = replace_token(line, item[0], item[1])
            lines.append(line)
        classes[i].lines = lines

        # make sure class definition has correct name
        paren = lines[0].find('(')
        class_name = classes[i].name
        if paren > 0:
            class_name = lines[0][len('class '):paren]
        classes[i].name = class_name
        # need to regenerate body since tokens changed
        classes[i].generate_body_text()
    return classes


def apply_changes_to_classes(file_classes, changes, com_names):
    """Apply changes to dict of classes organized by file."""
    for fc in file_classes.items():
        classes = fc[1]
        for i, c in enumerate(classes):
            lines = []
            for line in c.lines:
                if 'title=' not in line and 'description=' not in line:
                    for item in changes.items():
                        if item[0] not in line:
                            continue
                        new_name = item[1]
                        # if not in common then need to add common. to common names
                        if fc[0] != 'common' and new_name in com_names:
                            tentative_name = 'common.' + new_name
                            if tentative_name not in line:
                                new_name = tentative_name
                        line = replace_token(line, item[0], new_name)
                lines.append(line)
            classes[i].lines = lines

            # class name may have been replaced by change - so update with new name
            paren = lines[0].find('(')
            class_name = classes[i].name
            if paren > 0:
                class_name = lines[0][len('class '):paren]
            classes[i].name = class_name
            classes[i].generate_body_text()
        file_classes[fc[0]] = classes
    return file_classes


def reorder_and_dump_as_python(file_classes):
    """Reorder the files and dump."""
    for item in file_classes.items():
        ordered, forward_refs = reorder_classes(item[0], item[1])
        write_oscal(ordered, forward_refs, item[0])


def find_full_changes(file_classes):
    """Find all name changes and what files made them."""
    changes = {}
    com_names = []
    for c in file_classes['common']:
        changes[c.unique_name] = c.name
        com_names.append(c.name)
    for fstem in fstems:
        for c in file_classes[fstem]:
            changes[c.unique_name] = c.name
    return changes, com_names


def kill_min_items(classes):
    """Kill all references to min_items=1."""
    # NOTE!  This changes all constr list to normal List
    for i, c in enumerate(classes):
        for j, line in enumerate(c.lines):
            c.lines[j] = line.replace(', min_items=1', '')
        classes[i] = c
    return classes


def fix_include_all(classes):
    """Replace [IncludeAll] with [Any]."""
    for i, c in enumerate(classes):
        for j, line in enumerate(c.lines):
            c.lines[j] = line.replace('[IncludeAll]', '[Any]')
        classes[i] = c
    return classes


def fix_regexes(classes):
    """Replace all regex not supported by python."""
    bad_regex = "r'^(\p{L}|_)(\p{L}|\p{N}|[.\-_])*$'"
    good_regex = "r'^[_A-Za-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD][_A-Za-z\\u00C0-\\u00D6\\u00D8-\\u00F6\\u00F8-\\u02FF\\u0370-\\u037D\\u037F-\\u1FFF\\u200C-\\u200D\\u2070-\\u218F\\u2C00-\\u2FEF\\u3001-\\uD7FF\\uF900-\\uFDCF\\uFDF0-\\uFFFD\\-\\.0-9\\u00B7\\u0300-\\u036F\\u203F-\\u2040]*$'"  # noqa E501
    for i, c in enumerate(classes):
        for j, line in enumerate(c.lines):
            c.lines[j] = line.replace(bad_regex, good_regex)
        classes[i] = c
    return classes


def strip_file(classes):
    """Given set of classes from a file strip all names and apply changes to references in the bodies."""
    classes = strip_prefixes(classes)
    changes = []
    for c in classes:
        changes.append((c.original_name, c.name))
    return apply_changes_to_class_list(classes, changes)


def _strip_all_files(file_classes):
    for item in file_classes.items():
        stem = item[0]
        if item[0] != 'common':
            file_classes[stem] = strip_file(file_classes[stem])
    return file_classes


def update_refs_per_file(classes):
    """Change all refs to the _ versions."""
    changes = []
    for c in classes:
        if '_' in c.name:
            changes.append((c.name.split('_')[1], c.name))
    classes = apply_changes_to_class_list(classes, changes)
    return classes


def _strip_unrefed_files(file_class):
    """
    Strip unreferenced classes from each oscal file.

    The generated oscal files include classes that aren't referenced within the file.
    Those classes need to be removed early since they shouldn't be there at all.
    A key problem class is SetParameter, but there are others.
    This does a simple check of the file name being present at all in the body other classes.
    It could instead be a token-based search but this seems sufficient.
    """
    dead_names = []
    for c in file_class:
        if c.name == 'Model':
            continue
        refd = False
        for d in file_class:
            if d.name in [c.name] + dead_names:
                continue
            if c.name in d.body_text:
                refd = True
                break
        if not refd:
            dead_names.append(c.name)
    return [c for c in file_class if c.name not in dead_names]


def kill_roots(file_classes):
    """Kill the root classes in common."""
    com = file_classes['common']
    root_classes = {}
    match_str = ':__root__:'
    # find all root classes
    for c in com:
        body = c.body_text
        if body.startswith(match_str):
            p_field = body.find('=Field(')
            if p_field > 0:
                body = body[:p_field]
            root_classes[c.name] = body[len(match_str):]
    new_root_classes = {}
    skip_class_names = ['IntegerDatatype', 'NonNegativeIntegerDatatype', 'PositiveIntegerDatatype', 'OscalVersion']
    # replace references to root classes in the root classes
    for name, body in root_classes.items():
        if body in root_classes:
            body = root_classes[body]
        # now have mapping of root class name to its simplified body
        if name not in skip_class_names:
            new_root_classes[name] = body
    for classes in file_classes.values():
        for c in classes:
            if c.name not in new_root_classes:
                for ii in range(1, len(c.lines)):
                    line = c.lines[ii]
                    for name, body in new_root_classes.items():
                        if 'OscalVersion' not in line and 'OSCAL' not in line:
                            line = line.replace('common.' + name, body, 1)
                            line = line.replace(name, body, 1)
                    c.lines[ii] = line
    return file_classes


def normalize_files():
    """Clean up classes to minimise cross reference."""
    all_classes = load_all_classes()

    # kill the min_items immediately
    uc = kill_min_items(all_classes)

    # fix IncludeAll that isn't defined properly in schema
    uc = fix_include_all(all_classes)

    # fix non-supported regexes
    uc = fix_regexes(all_classes)

    # organize in a dict with filename as key
    file_classes = _list_to_file_classes(all_classes)

    # strip all names and bodies
    file_classes = _strip_all_files(file_classes)

    # strip classes that are never used in file
    for name, file_class in file_classes.items():
        file_classes[name] = _strip_unrefed_files(file_class)

    # convert dict to single list of classes with expected duplicates
    uc = _file_classes_to_list(file_classes, True)

    # find all unique classes based on body text
    uc = find_unique_classes(uc)

    # find classes with same name and different bodies - and modify class names with _
    # bodies are not changed
    uc = fix_clashes(uc)
    # now have unique list of classes with unique names
    # some names have _ in them to be removed later

    # make sure all classes have the proper unique name set at this point
    for c in uc:
        c.unique_name = c.name

    # some class names have _ in them, so change refs in each file to include the _
    uc = update_refs_per_file(uc)

    # split the classes based on current name and whether referenced by only one file
    file_classes = split_classes(uc)

    # find all changes from old name to new
    changes, com_names = find_full_changes(file_classes)

    # now apply all the changes to the class bodies
    file_classes = apply_changes_to_classes(file_classes, changes, com_names)

    # kill the __root__ classes
    file_classes = kill_roots(file_classes)

    # re-order them in each file and dump
    reorder_and_dump_as_python(file_classes)

    # this will leave files with raw formatting and make code-format must be run separately


if __name__ == '__main__':
    """Main invocation."""
    normalize_files()
