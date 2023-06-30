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
import sys
import os
import glob
import textwrap
from junitparser import JUnitXml

ADOC_FILE_PATH = "test-report-content.adoc"
GREEN_COLOR = "#90EE90"
RED_COLOR = "#F08080"


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
        default="example",
        help="""source directory to use for xml files and additionnal
        adoc files ( default is example/ )""",
    )

    parser.add_argument(
        "-s",
        "--split_test_id",
        const=True,
        default=False,
        help="""Split test name and ID. Test name must be formated as
        "ID - test name".""",
        action="store_const",
    )

    parser.add_argument(
        "-c",
        "--compliance_matrix",
        action="append",
        help="add the compliance matrix specified in the file.",
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
            "include::{}/prerequisites.adoc[opts=optional]\n".format(
                args.include_dir
            )
        )

        adoc_file.write("== Test reports\n")
        for xml in xml_files:
            add_xml_to_adoc(xml, adoc_file)

        adoc_file.write(
            "include::{}/notes.adoc[opts=optional]\n".format(args.include_dir)
        )


def add_xml_to_adoc(xml, adoc_file):

    for suite in xml:

        table_header = textwrap.dedent(
            """
            === Tests {_suitename_}
            [options="header",cols="{_colsize_}",frame=all, grid=all]
            |===
            {_testid_}|Tests |Results
            """
        )

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

        table_footer = textwrap.dedent(
            """
            |===
            * number of tests: {_nbtests_}
            * number of failures: {_nbfailures_}

            """
        )

        if args.split_test_id:
            adoc_file.write(
                table_header.format(
                    _suitename_=suite.name,
                    _colsize_="2,6,1",
                    _testid_="|Test ID",
                )
            )
        else:
            adoc_file.write(
                table_header.format(
                    _suitename_=suite.name, _colsize_="8,1", _testid_=""
                )
            )

        for test in suite:

            if args.split_test_id:
                if not " - " in test.name:
                    die("Test name must be formated as 'ID - name'")
                parts = test.name.split(" - ")
                test_name = parts[1]
                adoc_file.write(table_line_test_id.format(_testid_=parts[0]))
            else:
                test_name = test.name

            if test.is_passed:
                adoc_file.write(
                    table_line.format(
                        _testname_=test_name,
                        _result_="PASS",
                        _color_=GREEN_COLOR,
                    )
                )
            else:
                adoc_file.write(
                    table_line.format(
                        _testname_=test_name, _result_="FAIL", _color_=RED_COLOR
                    )
                )

        adoc_file.write(
            table_footer.format(
                _nbtests_=suite.tests, _nbfailures_=suite.failures
            )
        )


args = parse_arguments()
xml_files = open_test_files(args.include_dir)

try:
    generate_adoc(xml_files)
    os.system("asciidoctor-pdf test-report.adoc")
finally:
    os.remove(ADOC_FILE_PATH)
# TODO : return the exception if something bad happen
# TODO: add logs
