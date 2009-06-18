#!/bin/bash
#emacs: -*- mode: shell-script; c-basic-offset: 4; tab-width: 4; indent-tabs-mode: t -*- 
#ex: set sts=4 ts=4 sw=4 noet:
#  Yaroslav Halchenko                                      CS@UNM, CS@NJIT
#  web:     http://www.onerussian.com                      & PSYCH@RUTGERS
#  e-mail:  yoh@onerussian.com                              ICQ#: 60653192
#
# COPYRIGHT: Yaroslav Halchenko 2009
#
# LICENSE:
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the
#  Free Software Foundation, Inc., 51 Franklin St, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
# On Debian system see /usr/share/common-licenses/GPL for the full license.
#
#-----------------\____________________________________/------------------

print_help()
{
#print_version
cat <<EOF

PsychoPy startup script.

Usage: psychopy [-c|--coder|-m|--monitors|-b|--builder] [--version] [--help] [args]

Options:
  -c, --coder      starts IDE
                    (default action if without any options)
  -m, --monitor    starts Monitor Center

  --version        prints version and exits
  -h, --help       prints this help and exits

  The last of the mentioned in command lines modes (e.g. coder) would start.

  [args] are passed as command line arguments to corresponding module. Therefore
  they could be filenames of files to open in coder, etc.

EOF
#   -b, --builder    starts Design builder
}

print_version()
{
	version=$(python -c "import psychopy; print psychopy.__version__")
cat <<EOF

PsychoPy version: $version

EOF
}

CLOPTS=`getopt -o h,c,m --long help,version,monitor,coder -n '$0' -- "$@"`

if [ $? != 0 ]; then
	echo "Terminating..." >&2
	exit 1
fi

# Note the quotes around `$CLOPTS': they are essential!
eval set -- "$CLOPTS"

module='PsychoPyIDE.PsychoPyIDE'; class=IDEApp
while true ; do
    case "$1" in
        -h|--help) print_help; exit 0;;
        --version) print_version; exit 0;;
        -c|--coder) shift; module='PsychoPyIDE.PsychoPyIDE'; class=IDEApp;;
        -m|--monitor) shift; module='monitors.MonitorCenter'; class=MonitorCenter;;
        --) shift ; break ;;
        *) echo "ERROR: Internal error! ($1)"; exit 1;;
    esac
done

python -c "import $module as m; app=m.$class(0); app.MainLoop();" $*
