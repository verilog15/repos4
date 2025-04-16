/*******************************************************************************
 * Copyright IBM Corp. and others 1991
 *
 * This program and the accompanying materials are made available under
 * the terms of the Eclipse Public License 2.0 which accompanies this
 * distribution and is available at https://www.eclipse.org/legal/epl-2.0/
 * or the Apache License, Version 2.0 which accompanies this distribution and
 * is available at https://www.apache.org/licenses/LICENSE-2.0.
 *
 * This Source Code may also be made available under the following
 * Secondary Licenses when the conditions for such availability set
 * forth in the Eclipse Public License, v. 2.0 are satisfied: GNU
 * General Public License, version 2 with the GNU Classpath
 * Exception [1] and GNU General Public License, version 2 with the
 * OpenJDK Assembly Exception [2].
 *
 * [1] https://www.gnu.org/software/classpath/license.html
 * [2] https://openjdk.org/legal/assembly-exception.html
 *
 * SPDX-License-Identifier: EPL-2.0 OR Apache-2.0 OR GPL-2.0-only WITH Classpath-exception-2.0 OR GPL-2.0-only WITH OpenJDK-assembly-exception-1.0
 *******************************************************************************/

#include "j9.h"
#include "util_internal.h"
#include <stdint.h>

/* there is no error checking: the signature MUST be well-formed */
UDATA
getSendSlotsFromSignature(const U_8* signature)
{
	UDATA sendArgs = 0;
	UDATA i = 1; /* 1 to skip the opening '(' */

	/* All UTF8 in the class file have a size represented by uint16_t. The size check
	 * is only necessary for ASGCT where the signature provided may not be valid,
	 * but is harmless in the normal runtime case.
	 */
	for (; i <= UINT16_MAX; i++) {
		switch (signature[i]) {
		case ')':
			goto done;
		case '[':
			/* skip all '['s */
			for (i++; (i <= UINT16_MAX) && (signature[i] == '['); i++);
			if (signature[i] == 'L') {
				/* FALL THRU */
			} else {
				sendArgs++;
				break;
			}
		case 'L':
			for (i++; (i <= UINT16_MAX) && (signature[i] != ';'); i++);
			sendArgs++;
			break;
		case 'D':
		case 'J':
			sendArgs += 2;
			break;
		default:
			/* any other primitive type */
			sendArgs++;
			break;
		}
	}
done:
	return sendArgs;
}

