/*[INCLUDE-IF SharedClasses]*/
/*
 * Copyright IBM Corp. and others 1998
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
 */
package com.ibm.oti.shared;

import java.lang.ref.WeakReference;
/*[IF JAVA_SPEC_VERSION < 24]*/
import java.security.AccessControlException;
/*[ENDIF] JAVA_SPEC_VERSION < 24 */

import com.ibm.oti.util.Msg;

/**
 * SharedAbstractHelper provides common functions and data to helper subclasses.
 *
 * @see SharedHelper
 * @see SharedClassAbstractHelper
 */
public abstract class SharedAbstractHelper implements SharedHelper {
	private Boolean verbose;
	private WeakReference<ClassLoader> loaderRef;
	/*[IF JAVA_SPEC_VERSION < 24]*/
	private SharedClassPermission readPerm;
	private SharedClassPermission writePerm;
	boolean canFind;
	boolean canStore;
	/*[ENDIF] JAVA_SPEC_VERSION < 24 */
	int id;

	/**
	 * Constructs a new instance of this class.
	 */
	public SharedAbstractHelper() {
		super();
	}

	/*[IF JAVA_SPEC_VERSION >= 24]*/
	void initialize(ClassLoader loader, int loaderId) {
		this.id = loaderId;
		this.loaderRef = new WeakReference<>(loader);
		/*[MSG "K0591", "Created {0} with id {1}"]*/
		printVerboseInfo(Msg.getString("K0591", getHelperType(), Integer.valueOf(id))); //$NON-NLS-1$
	}
	/*[ELSE] JAVA_SPEC_VERSION >= 24 */
	void initialize(ClassLoader loader, int loaderId, boolean canLoaderFind, boolean canLoaderStore) {
		this.id = loaderId;
		this.canFind = canLoaderFind;
		this.canStore = canLoaderStore;
		this.loaderRef = new WeakReference<>(loader);
		/*[MSG "K0591", "Created {0} with id {1}"]*/
		printVerboseInfo(Msg.getString("K0591", getHelperType(), Integer.valueOf(id))); //$NON-NLS-1$
	}
	/*[ENDIF] JAVA_SPEC_VERSION >= 24 */

	/**
	 * Utility function. Returns the ClassLoader that owns this SharedHelper.
	 *
	 * Will return null if the Helper's ClassLoader has been garbage collected.
	 *
	 * @return the ClassLoader owning this helper, or null if the ClassLoader has been garbage collected
	 */
	@Override
	public ClassLoader getClassLoader() {
		return loaderRef.get();
	}

	private native boolean getIsVerboseImpl();

	/*[IF JAVA_SPEC_VERSION < 24]*/
	/* Do not cache the permission objects, else classloader references will prevent class GC */
	@SuppressWarnings("removal")
	private static boolean checkPermission(SecurityManager sm, ClassLoader loader, String type) {
		boolean result = false;
		try {
			sm.checkPermission(new SharedClassPermission(loader, type));
			result = true;
		} catch (AccessControlException e) {
			/* do nothing */
		}
		return result;
	}

	static boolean checkReadPermission(ClassLoader loader) {
		@SuppressWarnings("removal")
		SecurityManager sm = System.getSecurityManager();
		if (sm != null) {
			return checkPermission(sm, loader, "read"); //$NON-NLS-1$
		}
		return true; // no security manager means the check is successful
	}

	static boolean checkWritePermission(ClassLoader loader) {
		@SuppressWarnings("removal")
		SecurityManager sm = System.getSecurityManager();
		if (sm != null) {
			return checkPermission(sm, loader, "write"); //$NON-NLS-1$
		}
		return true; // no security manager means the check is successful
	}
	/*[ENDIF] JAVA_SPEC_VERSION < 24 */

	private boolean isVerbose() {
		if (verbose == null) {
			boolean verboseSet = getIsVerboseImpl();
			verbose = Boolean.valueOf(verboseSet);
			if (verboseSet) {
				/*[MSG "K0592", "Verbose output enabled for {0} id {1}"]*/
				printVerboseInfo(Msg.getString("K0592", getHelperType(), Integer.valueOf(id))); //$NON-NLS-1$
			}
		}
		return verbose.booleanValue();
	}

	void printVerboseError(String message) {
		if (isVerbose()) {
			/*[MSG "K0593", "Error for {0} id {1}: {2}"]*/
			System.err.println(Msg.getString("K0593", getHelperType(), Integer.toString(id), message)); //$NON-NLS-1$
		}
	}

	void printVerboseInfo(String message) {
		if (isVerbose()) {
			/*[MSG "K0594", "Info for {0} id {1}: {2}"]*/
			System.err.println(Msg.getString("K0594", getHelperType(), Integer.toString(id), message)); //$NON-NLS-1$
		}
	}

	abstract String getHelperType();
}
