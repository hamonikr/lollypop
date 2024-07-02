rm -fr /usr/local/lib/python3.*/site-packages/lollypop/
sudo ninja -C local install
reset
lollypop -e "$@"
