#!/bin/bash
SCRIPTPATH=$(dirname "$(readlink -f "$0")")
if [[ -f "${SCRIPTPATH}/../meson.build" ]]; then
    cat ${SCRIPTPATH}/../meson.build | grep " version: '[0-9].*'" | sed -ne 's/[^0-9]*\(\([0-9]\.\)\{0,4\}[0-9][^.]\).*/\1/p'
else
    git describe --tags | sed 's/\([^-]*-g\)/r\1/;s/-/./g'
fi
