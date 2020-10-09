#!/bin/sh
which py > /dev/null 2>&1
if [[ $? == 0 ]]; then
    echo "Running in Windows"
    PYTHON='python'
    py -3 -m venv testenv3
    source testenv3/Scripts/activate
else
    echo "Running in Linux"
    PYTHON=python3
    python3 -m venv testenv3
    source testenv3/bin/activate
fi

git stash

${PYTHON} -m pip install bumpversion
git checkout dev
git pull
git checkout master
git pull
git merge dev
git tag v`cat .bumpversion.cfg | grep current_version | cut -d " " -f 3`
git push
git push --tags
git checkout dev
bumpversion minor
git commit setup.py .bumpversion.cfg -m "Bump version for next release"
git push
