#!/bin/bash
set -e
pylint --exit-zero $(fdfind -e py --exclude conf.py) \
    --output-format=parseable \
    >pylint-report.txt
/opt/sonar-scanner/bin/sonar-scanner

if [ "$1" != "--pylint-only" ]; then
    /opt/sonar-scanner/bin/sonar-scanner
fi
