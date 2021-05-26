    #!/bin/bash

function generate_resource()
{
    echo '<?xml version="1.0" encoding="UTF-8"?>'
    echo '<gresources>'
    echo '  <gresource prefix="/org/gnome/Lollypop">'
    for file in data/*.css
    do
        echo -n '    <file compressed="true">'
        echo -n $(basename $file)
        echo '</file>'
    done
    for file in data/*.ui AboutDialog.ui
    do
        echo -n '     <file compressed="true" preprocess="xml-stripblanks">'
        echo -n $(basename $file)
        echo '</file>'
    done
    echo '  </gresource>'
    echo '</gresources>'
}

function generate_po()
{
    cd po
    git pull https://hosted.weblate.org/git/gnumdk/lollypop
    >lollypop.pot
    for file in ../data/org.gnome.Lollypop.gschema.xml ../data/*.in ../data/*.ui ../lollypop/*.py
    do
        xgettext --from-code=UTF-8 -j $file -o lollypop.pot
    done
    >LINGUAS
    for po in *.po
    do
        msgmerge -N $po lollypop.pot > /tmp/$$language_new.po
        mv /tmp/$$language_new.po $po
        language=${po%.po}
        echo $language >>LINGUAS
    done
}

generate_resource > data/lollypop.gresource.xml
generate_po
