#!/bin/bash
#
# asciidoc-report an asciidoc pdf builder
#
# Copyright (C) 2022-2023 Savoir-faire Linux Inc.
#
# This program is free software, distributed under the Apache License
# version 2.0, as well as the GNU General Public License version 3, at
# your own convenience. See LICENSE and LICENSE.GPLv3 for details.

TEST_ADOC_FILE=$(readlink -f "include/test-reports.adoc")

# Standard help message
usage()
{
    cat <<EOF
NAME:
    asciidoc-report an asciidoc pdf builder.
    Copyright (C) 2022-2023 Savoir-faire Linux Inc.

USAGE:
    ./compile.sh [options]

OPTIONS:
    -h: display this message
    -i <dir>: source Junit directory to use
    -s: Split test name and ID. Test name must be formated as ID - test name.
EOF
}

die()
{
    echo "error: $1"
    exit 1
}

integrate_all()
{
    [ -d "$XML_SRC_DIR" ] || die "$XML_SRC_DIR does not exist"
    [ -f "$TEST_ADOC_FILE" ] && rm "$TEST_ADOC_FILE"
    echo "== Test reports" > "$TEST_ADOC_FILE"

    for f in $(find "$XML_SRC_DIR" -name "*.xml"); do
        echo "including $f into $TEST_ADOC_FILE"
        add_xml_to_adoc "$f" "$TEST_ADOC_FILE"
    done
}

generate_row()
{
    local i="$1"
    local testcase="$2"
    local xml="$3"
    local green_color="#90EE90"
    local red_color="#F08080"
    if [ -n "$USE_ID" ] ; then
        test_id=$(echo "$testcase" | awk -F ' - ' '{print $1}')
        testcase_name=$(echo "$testcase" | awk -F ' - ' '{$1=""; print }')
        if [ -z "$testcase_name" ] ; then
            testcase_name="$test_id"
            test_id=""
        fi
        echo "|${test_id}" >> "$TEST_ADOC_FILE"
        # Reset color
        echo "{set:cellbgcolor!}" >> "$TEST_ADOC_FILE"
        echo "|${testcase_name}" >> "$TEST_ADOC_FILE"
    else
        testcase_name="$testcase"
        echo "|${testcase_name}" >> "$TEST_ADOC_FILE"
        # Reset color
        echo "{set:cellbgcolor!}" >> "$TEST_ADOC_FILE"
    fi
    if $(xmlstarlet -q sel -t  -v  "//testcase[$i]/failure" "$xml")
    then
        echo "|FAIL{set:cellbgcolor:$red_color}" >> "$TEST_ADOC_FILE"
    else
        echo "|PASS{set:cellbgcolor:$green_color}" >> "$TEST_ADOC_FILE"
    fi
}

add_xml_to_adoc()
{
    local xml="$1"
    local testname=$(xmlstarlet sel -t -v '//testsuite/@name' "$xml")
    local package=$(xmlstarlet sel -t -v '//testsuite/@package' "$xml")
    local classname=$(xmlstarlet sel -t -v '(//testcase[1])/@classname' "$xml")
    local nb_tests=$(xmlstarlet sel -t -v '(//testsuite[1])/@tests' "$xml")
    local failures=$(xmlstarlet sel -t -v '(//testsuite[1])/@failures' "$xml")
    local cols='"7,1"'
    if [ -z "$testname" -o "$testname" == "default" ] ; then
        testname=$(basename $xml)
    fi
    echo -n "=== Tests $testname" >> "$TEST_ADOC_FILE"
    if [ -n "$package" -a "$package" != "default" ] ; then
        echo -n " package $package" >> "$TEST_ADOC_FILE"
    fi
    if [ -n "$classname" -a "$classname" != "cukinia" ] ; then
        echo -n " for $classname" >> "$TEST_ADOC_FILE"
    fi
    echo >> "$TEST_ADOC_FILE"
    if [ -n "$USE_ID" ] ; then
        cols='"2,7,1"'
    fi

    echo "[options=\"header\",cols=$cols,frame=all, grid=all]" >> "$TEST_ADOC_FILE"
    echo "|===" >> "$TEST_ADOC_FILE"
    if [ -n "$USE_ID" ] ; then
        echo -n "|Test ID" >> "$TEST_ADOC_FILE"
    fi
    echo "|Tests |Results" >> "$TEST_ADOC_FILE"
    local i=1
    while read testcase ; do
        generate_row "$i" "$testcase" "$xml"
        let i++
    done < <(xmlstarlet sel -t -v '//testcase/@name' "$xml")
    echo "|===" >> "$TEST_ADOC_FILE"
    echo "{set:cellbgcolor!}" >> "$TEST_ADOC_FILE"
    echo "" >> "$TEST_ADOC_FILE"
    echo "* number of tests: $nb_tests" >> "$TEST_ADOC_FILE"
    echo "* number of failures: $failures" >> "$TEST_ADOC_FILE"
    echo "" >> "$TEST_ADOC_FILE"

}

while getopts ":si:h" opt; do
    case $opt in
    i)
        XML_SRC_DIR="$OPTARG"
        ;;
    s)
        USE_ID="true"
        ;;
    h)
        usage
        exit 0
        ;;
    esac
done
shift $((OPTIND-1))

if [ -z "$XML_SRC_DIR" ] || [ ! -d "$XML_SRC_DIR" ] ; then
    die "$XML_SRC_DIR is not found or is not a directory"
fi

integrate_all
asciidoctor-pdf main.adoc
