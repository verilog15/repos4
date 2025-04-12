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

from argparse import Namespace
from typing import Union
from libvirtnbdbackup import output


def get(
    args: Namespace, repository: output.target
) -> Union[output.target.Directory, output.target.Zip]:
    """Get filehandle for output files based on output
    mode"""
    fileStream: Union[output.target.Directory, output.target.Zip]
    if args.stdout is False:
        fileStream = repository.Directory()
    else:
        fileStream = repository.Zip()
        args.output = "./"
        args.worker = 1

    return fileStream
