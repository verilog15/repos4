
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
#include "j9cfg.h"
#include "j9port.h"

#include "CopyScanCacheChunkVLHGC.hpp"
#include "CopyScanCacheVLHGC.hpp"
#include "EnvironmentVLHGC.hpp"
#include "GCExtensions.hpp"


MM_CopyScanCacheChunkVLHGC *
MM_CopyScanCacheChunkVLHGC::newInstance(MM_EnvironmentVLHGC *env, uintptr_t cacheEntryCount, MM_CopyScanCacheVLHGC **tailCacheAddr, MM_CopyScanCacheChunkVLHGC *nextChunk)
{
	MM_CopyScanCacheChunkVLHGC *chunk = (MM_CopyScanCacheChunkVLHGC *)env->getForge()->allocate(sizeof(MM_CopyScanCacheChunkVLHGC) + cacheEntryCount * sizeof(MM_CopyScanCacheVLHGC), MM_AllocationCategory::FIXED, J9_GET_CALLSITE());

	if (NULL != chunk) {
		new(chunk) MM_CopyScanCacheChunkVLHGC();
		if (!chunk->initialize(env, cacheEntryCount, tailCacheAddr, nextChunk)) {
			chunk->kill(env);
			return NULL;
		}
	}
	return chunk;	
}

void
MM_CopyScanCacheChunkVLHGC::kill(MM_EnvironmentVLHGC *env)
{
	tearDown(env);
	env->getForge()->free(this);
}


bool
MM_CopyScanCacheChunkVLHGC::initialize(MM_EnvironmentVLHGC *env, uintptr_t cacheEntryCount, MM_CopyScanCacheVLHGC **tailCacheAddr, MM_CopyScanCacheChunkVLHGC *nextChunk)
{
	_baseCache = (MM_CopyScanCacheVLHGC *)(this + 1);
	_nextChunk = nextChunk;
	
	Assert_MM_true(0 < cacheEntryCount);

	*tailCacheAddr = _baseCache + cacheEntryCount - 1;
	MM_CopyScanCacheVLHGC *previousCache = NULL;

	for (MM_CopyScanCacheVLHGC *currentCache = *tailCacheAddr; currentCache >= _baseCache; currentCache--) {
		new(currentCache) MM_CopyScanCacheVLHGC();
		currentCache->next = previousCache;
		previousCache = currentCache;
	}
	
	return true;
}

void
MM_CopyScanCacheChunkVLHGC::tearDown(MM_EnvironmentVLHGC *env)
{
	_baseCache = NULL;
	_nextChunk = NULL;
}


