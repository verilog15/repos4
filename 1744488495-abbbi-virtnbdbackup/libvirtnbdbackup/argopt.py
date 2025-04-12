#!/usr/bin/python3
"""
Copyright (C) 2023  Michael Ablassmeier <abi@grinser.de>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
import os
from getpass import getuser
from argparse import _ArgumentGroup
from libvirtnbdbackup import __version__


def addRemoteArgs(opt: _ArgumentGroup) -> None:
    """Common remote backup arguments"""

    user = getuser() or None

    session = "qemu:///system"
    if user != "root":
        session = "qemu:///session"

    opt.add_argument(
        "-U",
        "--uri",
        default=session,
        required=False,
        type=str,
        help="Libvirt connection URI. (default: %(default)s)",
    )
    opt.add_argument(
        "--user",
        default=None,
        required=False,
        type=str,
        help="User to authenticate against libvirtd. (default: %(default)s)",
    )
    opt.add_argument(
        "--ssh-user",
        default=user,
        required=False,
        type=str,
        help=(
            "User to authenticate against remote sshd: "
            "used for remote copy of files. (default: %(default)s)"
        ),
    )
    opt.add_argument(
        "--ssh-port",
        default=22,
        required=False,
        type=int,
        help=(
            "Port to connect to remote sshd: "
            "used for remote copy of files. (default: %(default)s)"
        ),
    )
    opt.add_argument(
        "--password",
        default=None,
        required=False,
        type=str,
        help="Password to authenticate against libvirtd. (default: %(default)s)",
    )
    opt.add_argument(
        "-P",
        "--nbd-port",
        type=int,
        default=10809,
        required=False,
        help=(
            "Port used by remote NBD Service, should be unique for each"
            " started backup. (default: %(default)s)"
        ),
    )
    opt.add_argument(
        "-I",
        "--nbd-ip",
        type=str,
        default="",
        required=False,
        help=(
            "IP used to bind remote NBD service on"
            " (default: hostname returned by libvirtd)"
        ),
    )
    opt.add_argument(
        "--tls",
        action="store_true",
        required=False,
        help="Enable and use TLS for NBD connection. (default: %(default)s)",
    )
    opt.add_argument(
        "--tls-cert",
        type=str,
        default="/etc/pki/qemu/",
        required=False,
        help=(
            "Path to TLS certificates used during offline backup"
            " and restore. (default: %(default)s)"
        ),
    )


def addDebugArgs(opt: _ArgumentGroup) -> None:
    """Common debug arguments"""
    opt.add_argument(
        "-v",
        "--verbose",
        default=False,
        help="Enable debug output",
        action="store_true",
    )
    opt.add_argument(
        "-V",
        "--version",
        default=False,
        help="Show version and exit",
        action="version",
        version=__version__,
    )


def addLogArgs(opt, prog):
    """Logging related arguments"""
    try:
        HOME = os.environ["HOME"]
    except KeyError:
        HOME = "/tmp"
    opt.add_argument(
        "-L",
        "--logfile",
        default=f"{HOME}/{prog}.log",
        type=str,
        help="Path to Logfile (default: %(default)s)",
    )


def addLogColorArgs(opt):
    """Option to enable or disable colored output"""
    opt.add_argument(
        "--nocolor",
        default=False,
        help="Disable colored output (default: %(default)s)",
        action="store_true",
    )
