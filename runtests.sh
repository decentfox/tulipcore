#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

TOXINIDIR=$1
ENVTMPDIR=$2

mkdir -p "${ENVTMPDIR}"
cp -r "${TOXINIDIR}/gevent" "${ENVTMPDIR}/gevent"
(
    cd "${ENVTMPDIR}/gevent"
    patch < "${TOXINIDIR}/known_failures.patch"
    make fulltoxtest
)
