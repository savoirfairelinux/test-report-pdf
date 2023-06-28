#!/bin/python3
#
# Copyright (C) 2023 Savoir-faire Linux, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
from junitparser import JUnitXml

parser = argparse.ArgumentParser(
            prog='test-report-pdf',
            description='''
    This script will automatically look for all .xml files contained in the
    source directory and integrate them in the test report. By default, one
    table will be created for each file containing all test one after another.

    Different tables can be generated for the same file using cukinia tests
    suites in cukinia (`logging suite "string"`).

    A machine name can be specified in the table title using cukinia class
    (`logging class "string"`).
           ''',
            formatter_class=argparse.RawDescriptionHelpFormatter)
            # formatter is used to display description with correct indentation

parser.add_argument('-i', '--include_dir', help='source directory to use for xml files and additionnal adoc files ( default is example/ )', default="example")

parser.add_argument('-s', '--split_test_id', help='Split test name and ID. Test name must be formated as "ID - test name".', action='store_const', const=True, default=False)

parser.add_argument('-c', '--compliance_matrix', help='add the compliance matrix specified in the file.', action='append')

args = parser.parse_args()
