venv_path="ENV"
build_lib () {
    if [ ! -e  "$1" ] ; then
        # FIXME: the 1.2.8 should not be hard-coded
        version=$(echo "$1" | cut -f 3 -d '-')
        wget http://oligarchy.co.uk/xapian/$version/$1.tar.gz
        tar -C . -xzf $1.tar.gz
    fi
    pushd $1
    ./configure --prefix=`pwd`/../$venv_path/ --with-python
    make -j5
    make install
    popd
}

virtualenv --no-site-package $venv_path
. $venv_path/bin/activate
build_lib "xapian-core-1.2.8"
build_lib "xapian-bindings-1.2.8"
python setup.py develop
python bench.py
