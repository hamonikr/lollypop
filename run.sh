rm -fr /usr/local/lib/python3.*/site-packages/lollypop/
ninja -C local install
reset
lollypop -e "$@"
