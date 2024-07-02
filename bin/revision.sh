#!/bin/sh
git describe --tags | sed 's/\([^-]*-g\)/r\1/;s/-/./g'
