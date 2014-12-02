#!/bin/sh
#
# Make a directory containing symlinks to files we want to autodoc which
#   do not end in .py for ReadTehDocs.org build servers
#

for dir in client actions; do
    files=`cd ${dir}/; ls`
    for file in ${files}; do
        [ -f ${dir}/${file} ] && ln -s ${dir}/${file} ${dir}/${file}.py
        #[ -d ${dir}/${file} ] && ln -s ${dir}/${file} ${dir}/${file}
    done
    touch ${dir}/__init__.py
    #ln -s ${dir} docs/${dir}
done

