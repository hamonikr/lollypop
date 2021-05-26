#!/bin/bash
for i in 16 22 32 48 256 512; do
	inkscape -z -e data/icons/hicolor/"$i"x"$i"/apps/org.gnome.Lollypop.png -w $i -h $i data/icons/hicolor/scalable/apps/org.gnome.Lollypop.svg
done
