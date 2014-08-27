#!/bin/sh
#
# Make a direcroty containing symlinks to files we want to autodoc which 
#   do not end in .py for ReadTehDocs.org build servers
#

rm -rf ztps
mkdir ztps
cd ztps
touch __init__.py

for dir in client actions; do
    #(cd ../${dir}/; ls) | xargs -I \{\} ln -s ../${dir}/\{\} \{\}.py
    files=`cd ../${dir}/; ls`
    for file in ${files}; do
        [ -f ../${dir}/${file} ] && ln -s ../${dir}/${file} ${file}.py
        [ -d ../${dir}/${file} ] && ln -s ../${dir}/${file} ${file}
    done
done

