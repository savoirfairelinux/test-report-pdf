#!/bin/sh
#
# asciidoc-report an asciidoc pdf builder
#
# Copyright (C) 2022-2023 Savoir-faire Linux Inc.
#
# This program is free software, distributed under the Apache License
# version 2.0, as well as the GNU General Public License version 3, at
# your own convenience. See LICENSE and LICENSE.GPLv3 for details.

CSV_DST_DIR=$(readlink -f "include/tests")
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
    -i <dir> source csv directory to use
EOF
}

die()
{
    echo "error: $1"
    exit 1
}

beautify_csv()
{
    local csv_file=$1
    local green_color="#90EE90"
    local red_color="#F08080"

    sed -i -e "/FAIL/ s/./{set:cellbgcolor:$red_color}&/" $csv_file
    sed -i -e "/PASS/ s/./{set:cellbgcolor:$green_color}&/" $csv_file
}

integrate_all()
{
    local src_dir=$1
    local dst_dir=$2
    local adoc_file=$3
    [ -d "$src_dir" ] || die "$src_dir does not exist"
    [ -d "$dst_dir" ] || die "$dst_dir does not exist"
    [ -f $adoc_file ] && rm $adoc_file
    echo "== Test reports" > $adoc_file
    echo "deleting all csv in $dst_dir"
    rm $dst_dir/*.csv
    cp $src_dir/*.csv $dst_dir

    for f in $(find $dst_dir -name *.csv); do
        echo "including $f into $adoc_file"
        beautify_csv $f
        add_csv_to_adoc $f $adoc_file
    done
}

add_csv_to_adoc()
{
    local csv=$1
    local adoc=$2

    echo "=== Tests $(basename $csv)" >> $adoc
    echo "[%autowidth,%header,format=csv,options="header",frame=all, grid=all]" >> $adoc
    echo "|===" >> $adoc
    echo "include::$csv[]" >>$adoc
    echo "|===" >> $adoc
}

while getopts ":i:h" opt; do
    case $opt in
    i)
        CSV_SRC_DIR=$OPTARG
        ;;
    h)
        usage
        exit 0
        ;;
    esac
done
shift $((OPTIND-1))

[ -z $CSV_SRC_DIR ] && usage

integrate_all $CSV_SRC_DIR $CSV_DST_DIR $TEST_ADOC_FILE
asciidoctor-pdf main.adoc
