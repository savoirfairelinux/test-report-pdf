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
import csv
import glob
import os
import sys
import textwrap
from junitparser import TestCase, JUnitXml, Properties
from datetime import datetime

ADOC_FILE_PATH = "test-report-content.adoc"
GREEN_COLOR = "#90EE90"
RED_COLOR = "#F08080"
ORANGE_COLOR = "#ee6644"


class CukiniaTest(TestCase):
    '''
    Custom class to get property value in TestCase
    '''
    def get_property_value(self, name):
        '''
        Gets a property from a testcase.
        '''
        props = self.child(Properties)
        if props is None:
            return None
        for prop in props:
            if prop.name == name:
                return prop.value
        return None


def die(error_string):
    print("ERROR : ", error_string)
    sys.exit(1)


def parse_arguments():

    parser = argparse.ArgumentParser(
        prog="test-report-pdf",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        # formatter is used to display description with correct indentation
        description="""
    This script will automatically look for all .xml files contained in the
    source directory and integrate them in the test report. By default, one
    table will be created for each file containing all test one after another.

    Different tables can be generated for the same file using cukinia tests
    suites in cukinia (`logging suite "string"`).

    A machine name can be specified in the table title using cukinia class
    (`logging class "string"`).
               """,
    )

    parser.add_argument(
        "-i",
        "--include_dir",
        help="""source directory to use for xml files and additionnal
        adoc files.""",
    )

    parser.add_argument(
        "-m",
        "--add_machine_name",
        const=True,
        default=False,
        help="""Add the name of the machine in the title of each tables.
        This machine name should be given in the test suite
        using the classname feature of cukinia.""",
        action="store_const",
    )

    parser.add_argument(
        "-c",
        "--compliance_matrix",
        action="append",
        help="""add the compliance matrix specified in the file.
        Can be used multiple times for multiple matrices to add.""",
    )

    parser.add_argument(
        "-C",
        "--client_name",
        help="""Name of the client. This will be added in receiver field""",
    )

    parser.add_argument(
        "-p",
        "--project_name",
        help="""Name of the project. This will be added to the report title""",
    )

    return parser.parse_args()


def open_test_files(directory):

    if not os.path.isdir(directory):
        die("Directory {} does not exists".format(directory))

    files = glob.glob(os.path.join(directory, "*.xml"))

    if not files:
        die("No test file found in {}".format(directory))

    xml_files = []
    for f in files:
        xml_files.append(JUnitXml.fromfile(f))

    return xml_files


def generate_adoc(xml_files):

    if os.path.exists(ADOC_FILE_PATH):
        if not os.path.isfile(ADOC_FILE_PATH):
            die("temporary file {} is not a file".format(ADOC_FILE_PATH))
        os.remove(ADOC_FILE_PATH)

    with open(ADOC_FILE_PATH, "w", encoding="utf-8") as adoc_file:
        adoc_file.write(
            "include::{}/prerequisites.adoc[opts=optional]\n\n".format(
                args.include_dir
            )
        )

        adoc_file.write("== Test reports\n")

        for xml in xml_files:
            for suite in xml:
                has_test_id = check_for_id(suite)
                write_table_header(suite, adoc_file, has_test_id)
                for test in suite:
                    write_table_line(CukiniaTest.fromelem(test), adoc_file,
                                     has_test_id)
                write_table_footer(suite, adoc_file)

        add_compliance_matrix(xml_files, adoc_file, has_test_id)

        adoc_file.write(
            "include::{}/notes.adoc[opts=optional]\n".format(args.include_dir)
        )


def check_for_id(suite):
    '''
    Check in the first test if there is an id. If yes return True otherwise
    return False
    '''
    for test in suite:
        if(CukiniaTest.fromelem(test).get_property_value("cukinia.id")):
            return True
        else:
            return False

def write_table_header(suite, adoc_file, has_test_id):

    table_header = textwrap.dedent(
        """
        === Tests {_suitename_} {_machinepart_}
        [options="header",cols="{_colsize_}",frame=all, grid=all]
        |===
        {_testid_}|Tests |Results
        """
    )

    # Weird tricks to get the classname of the first test of the suite
    # This classname is used as machine name.
    machine_name = next(iter(suite)).classname
    if args.add_machine_name:
        machine_part = "for {}".format(machine_name)
    else:
        machine_part = ""

    if has_test_id:
        adoc_file.write(
            table_header.format(
                _suitename_=suite.name,
                _machinepart_=machine_part,
                _colsize_="2,6,1",
                _testid_="|Test ID",
            )
        )
    else:
        adoc_file.write(
            table_header.format(
                _suitename_=suite.name,
                _machinepart_=machine_part,
                _colsize_="8,1",
                _testid_="",
            )
        )


def write_table_line(test, adoc_file, has_test_id):

    table_line_test_id = textwrap.dedent(
        """
        |{_testid_}
        {{set:cellbgcolor!}}
        """
    )

    table_line = textwrap.dedent(
        """
        |{_testname_}
        {{set:cellbgcolor!}}
        |{_result_}
        {{set:cellbgcolor:{_color_}}}
        """
    )

    if has_test_id:
        adoc_file.write(table_line_test_id.format(
            _testid_=test.get_property_value("cukinia.id")))

    if test.is_passed:
        adoc_file.write(
            table_line.format(
                _testname_=test.name.replace('|', '\|'),
                _result_="PASS",
                _color_=GREEN_COLOR,
            )
        )
    else:
        adoc_file.write(
            table_line.format(
                _testname_=test.name.replace('|', '\|'),
                _result_="FAIL",
                _color_=RED_COLOR
            )
        )


def write_table_footer(suite, adoc_file):

    table_footer = textwrap.dedent(
        """
        |===
        * number of tests: {_nbtests_}
        * number of failures: {_nbfailures_}

        """
    )

    adoc_file.write(
        table_footer.format(_nbtests_=suite.tests, _nbfailures_=suite.failures)
    )


def add_compliance_matrix(xml_files, adoc_file, has_test_id):

    if args.compliance_matrix:
        if not has_test_id:
            die(
                "Can't include compliance matrix, test id feature is not enabled"
            )
        adoc_file.write("== Compliance Matrix\n")

        for matrix in args.compliance_matrix:

            if not os.path.exists(matrix):
                die("Matrix file {} doesn't exists".format(matrix))
            if not os.path.isfile(matrix):
                die("Matrix file {} is not a file".format(matrix))

            matrix_header = textwrap.dedent(
                """
                === Matrix {_matrixname_}
                [options="header",cols="6,2,1",frame=all, grid=all]
                |===
                |Requirement |Test id |Status
                """
            )

            adoc_file.write(matrix_header.format(_matrixname_=matrix))

            with open(matrix, "r", encoding="utf-8") as matrix_file:

                requirements = list(sorted(csv.reader(matrix_file)))
                # requirements is a list, each item of the list has the form
                # ["requirement name", test_ID]
                write_matrix_tests(requirements, xml_files, adoc_file)

            matrix_footer = textwrap.dedent(
                """
                |===

                """
            )

            adoc_file.write(matrix_footer)


def write_matrix_tests(requirements, xml_files, adoc_file):

    matrix_line_req = textwrap.dedent(
        """
        .{_nbtests_}+|{_req_}
        {{set:cellbgcolor!}}
        """
    )

    matrix_line_test = textwrap.dedent(
        """
        |{_id_}
        {{set:cellbgcolor!}}
        |{_status_}
        {{set:cellbgcolor:{_color_}}}
        """
    )

    current_requirement = ""

    for req, test_id in requirements:

        # This code section uses the span rows feature of asciidoc
        # https://docs.asciidoctor.org/asciidoc/latest/tables/span-cells/
        if req != current_requirement:
            current_requirement = req
            nb_tests = sum([current_requirement == r[0] for r in requirements])
            # nb_tests control the number of lines the requirement cell will
            # be spanned. This number should be equal to the number of times
            # the same requirement appears

            adoc_file.write(
                matrix_line_req.format(
                    _nbtests_=nb_tests,
                    _req_=req,
                )
            )

        present, passed = check_test(test_id, xml_files)
        if not present:
            adoc_file.write(
                matrix_line_test.format(
                    _id_=test_id,
                    _status_="ABSENT",
                    _color_=ORANGE_COLOR,
                )
            )
        elif passed:
            adoc_file.write(
                matrix_line_test.format(
                    _id_=test_id,
                    _status_="PASS",
                    _color_=GREEN_COLOR,
                )
            )
        else:
            adoc_file.write(
                matrix_line_test.format(
                    _id_=test_id,
                    _status_="FAIL",
                    _color_=RED_COLOR,
                )
            )


# This function read all the xml and look for all tests that matches a given ID.
# It return present=True if the ID is found at least once
# It return passed=False if at least one test is failed.
def check_test(test_id, xml_files):

    present = False
    passed = True

    for xml in xml_files:
        for suite in xml:
            for test in suite:
                current_id = CukiniaTest.fromelem(test).get_property_value(
                    "cukinia.id"
                )
                if current_id == test_id:
                    present = True
                    if not test.is_passed:
                        passed = False

    return present, passed


args = parse_arguments()
xml_files = open_test_files(args.include_dir)

try:
    generate_adoc(xml_files)
    date = datetime.now().astimezone().strftime("%-d %B %Y, %H:%M:%S %Z")
    year = datetime.now().astimezone().strftime("%Y")
    os.system(f"asciidoctor-pdf \
            -r ./extended-pdf-converter.rb \
            -a revdate='{date}' \
            -a year='{year}' \
            -a author='{args.client_name}' \
            -a project='{args.project_name}' \
            test-report.adoc")
finally:
    os.remove(ADOC_FILE_PATH)
# TODO : return the exception if something bad happen
# TODO: add logs
