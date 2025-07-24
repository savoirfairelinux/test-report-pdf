#!/bin/bash
set -e
pylint --exit-zero $(fdfind -e py --exclude conf.py) \
    --output-format=parseable \
    >pylint-report.txt
export SONAR_SCANNER_OPTS="--add-opens java.base/sun.nio.ch=ALL-UNNAMED --add-opens java.base/java.io=ALL-UNNAMED"

if [ "$1" != "--pylint-only" ]; then
    if [ -n "$GERRIT_CHANGE_NUMBER" ]; then
        GERRIT_ARGS="-Dsonar.pullrequest.key=${GERRIT_CHANGE_NUMBER}-${GERRIT_PATCHSET_NUMBER} \
            -Dsonar.pullrequest.base=${GERRIT_BRANCH} -Dsonar.pullrequest.branch=${GERRIT_REFSPEC} \
            -Dsonar.scm.provider=git"
    fi
    /opt/sonar-scanner/bin/sonar-scanner $GERRIT_ARGS -Dsonar.token="$SONAR_AUTH_TOKEN"
fi
