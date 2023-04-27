#!/bin/bash
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

TMP_ADOC_FILE=$(readlink -f "test-reports-content.adoc")

# Standard help message
usage()
{
    cat <<EOF
NAME:
    test-report-pdf an asciidoc pdf test report builder.
    Copyright (C) 2022-2023 Savoir-faire Linux Inc.

SYNOPSIS:
    ./compile.sh [options]

DESCRIPTION:
    This script will automatically look for all .xml files contained in the
    source directory and integrate them in the test report. By default, one
    table will be created for each file containing all test one after another.

    Different tables can be generated for the same file using cukinia tests
    suites in cukinia (`logging suite "string"`).

    A machine name can be specified in the table title using cukinia class
    (`logging class "string"`).

OPTIONS:
    -h: display this message
    -i <dir>: source directory to use for xml files and additionnal adoc files
              ( default is example/ )
    -s: Split test name and ID. Test name must be formated as ID - test name.
EOF
}

die()
{
    echo "error: $1"
    exit 1
}

generate_adoc()
{
    [ -d "$SRC_DIR" ] || die "$SRC_DIR does not exist"
    [ -f "$TMP_ADOC_FILE" ] && rm "$TMP_ADOC_FILE"

    echo "include::$SRC_DIR/prerequisites.adoc[opts=optional]" > "$TMP_ADOC_FILE"
    echo "" >> "$TMP_ADOC_FILE" # new line needed for a new page in asciidoc

    echo "== Test reports" >> "$TMP_ADOC_FILE"

    for f in $(find "$SRC_DIR" -name "*.xml"); do
        echo "including test file $f"
        add_test_file_to_adoc "$f"
    done

    echo "include::$SRC_DIR/notes.adoc[opts=optional]" >> "$TMP_ADOC_FILE"
}

generate_test_row()
{
    local i="$1"
    local j="$2"
    local testcase="$3"
    local xml="$4"
    local green_color="#90EE90"
    local red_color="#F08080"

    # Sanitize testcase (escape |)
    testcase=$(echo "$testcase" | sed 's/|/\\|/g')

    if [ -n "$USE_ID" ] ; then
        test_id=$(echo "$testcase" | awk -F ' - ' '{print $1}')
        testcase_name=$(echo "$testcase" | awk -F ' - ' '{$1=""; print }')
        if [ -z "$testcase_name" ] ; then
            testcase_name="$test_id"
            test_id=""
        fi
        echo "|${test_id}" >> "$TMP_ADOC_FILE"
        # Reset color
        echo "{set:cellbgcolor!}" >> "$TMP_ADOC_FILE"
        echo "|${testcase_name}" >> "$TMP_ADOC_FILE"
    else
        testcase_name="$testcase"
        echo "|${testcase_name}" >> "$TMP_ADOC_FILE"
        # Reset color
        echo "{set:cellbgcolor!}" >> "$TMP_ADOC_FILE"
    fi
    if $(xmlstarlet -q sel -t  -v "////testsuites/testsuite[$i]/testcase[$j]/failure" "$xml")
    then
        echo "|FAIL{set:cellbgcolor:$red_color}" >> "$TMP_ADOC_FILE"
    else
        echo "|PASS{set:cellbgcolor:$green_color}" >> "$TMP_ADOC_FILE"
    fi
}

add_test_file_to_adoc()
{
    local xml="$1"
    local nb_suites="$(( $(xmlstarlet sel -t -v  '//testsuite/@name' "$xml"\
        |wc -l) +1 ))"
    for i in $(seq 1 ${nb_suites}) ; do
        local testname=$(xmlstarlet sel -t -v "//testsuite[$i]/@name" "$xml")
        local classname=$(xmlstarlet sel -t -v "//testsuite[$i]/testcase[1]/@classname" "$xml")
        local nb_tests=$(xmlstarlet sel -t -v "//testsuite[$i]/@tests" "$xml")
        local failures=$(xmlstarlet sel -t -v "//testsuite[$i]/@failures" "$xml")
        local cols='"7,1"'
        if [ -z "$testname" -o "$testname" == "default" ] ; then
            testname=$(basename $xml)
        fi
        echo -n "=== Tests $testname" >> "$TMP_ADOC_FILE"
        if [ -n "$classname" -a "$classname" != "cukinia" ] ; then
            echo -n " for $classname" >> "$TMP_ADOC_FILE"
        fi
        echo >> "$TMP_ADOC_FILE"
        if [ -n "$USE_ID" ] ; then
            cols='"2,7,1"'
        fi

        echo "[options=\"header\",cols=$cols,frame=all, grid=all]" >> "$TMP_ADOC_FILE"
        echo "|===" >> "$TMP_ADOC_FILE"
        if [ -n "$USE_ID" ] ; then
            echo -n "|Test ID" >> "$TMP_ADOC_FILE"
        fi
        echo "|Tests |Results" >> "$TMP_ADOC_FILE"

        local j=1
        local testcases=$(xmlstarlet sel -t -v "//testsuite[$i]/testcase/@name" "$xml")
        echo "$testcases" | while read testcase ; do
            generate_test_row "$i" "$j" "$testcase" "$xml"
            let j++
        done
        echo "|===" >> "$TMP_ADOC_FILE"
        echo "{set:cellbgcolor!}" >> "$TMP_ADOC_FILE"
        echo "" >> "$TMP_ADOC_FILE"
        echo "* number of tests: $nb_tests" >> "$TMP_ADOC_FILE"
        echo "* number of failures: $failures" >> "$TMP_ADOC_FILE"
        echo "" >> "$TMP_ADOC_FILE"
    done
}

SRC_DIR="example"
while getopts ":si:h" opt; do
    case $opt in
    i)
        SRC_DIR="$OPTARG"
        ;;
    s)
        USE_ID="true"
        ;;
    h)
        usage
        exit 0
        ;;
    *)
        echo "Unrecognized option"
        usage
        exit 1
    esac
done
shift $((OPTIND-1))

if [ -z "$SRC_DIR" ] || [ ! -d "$SRC_DIR" ] ; then
    die "$SRC_DIR is not found or is not a directory"
fi

generate_adoc
asciidoctor-pdf test-report.adoc

rm $TMP_ADOC_FILE
