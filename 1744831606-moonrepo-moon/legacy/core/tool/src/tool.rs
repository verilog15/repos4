use async_trait::async_trait;
use moon_lang::LockfileDependencyVersions;
use moon_process::Command;
use proto_core::UnresolvedVersionSpec;
use rustc_hash::FxHashMap;
use std::any::Any;
use std::path::Path;

#[async_trait]
pub trait Tool: Any + Send + Sync {
    fn as_any(&self) -> &(dyn Any + Send + Sync);

    /// Setup the tool by downloading and installing it.
    /// Return a count of how many sub-tools were installed.
    async fn setup(
        &mut self,
        _last_versions: &mut FxHashMap<String, UnresolvedVersionSpec>,
    ) -> miette::Result<u8> {
        Ok(0)
    }

    /// Teardown the tool by uninstalling and deleting files.
    async fn teardown(&mut self) -> miette::Result<()> {
        Ok(())
    }
}

#[async_trait]
pub trait DependencyManager<T: Send + Sync>: Send + Sync + Tool {
    /// Create a command to run that wraps the binary.
    fn create_command(&self, tool: &T) -> miette::Result<Command>;

    /// Dedupe dependencies after they have been installed.
    async fn dedupe_dependencies(
        &self,
        tool: &T,
        working_dir: &Path,
        log: bool,
    ) -> miette::Result<()>;

    /// Return the name of the lockfile.
    fn get_lock_filename(&self) -> String;

    /// Return the name of the manifest.
    fn get_manifest_filename(&self) -> String;

    /// Return a list of dependencies resolved to their latest version from the lockfile.
    /// Dependencies are based on a manifest at the provided path.
    async fn get_resolved_dependencies(
        &self,
        project_root: &Path,
    ) -> miette::Result<LockfileDependencyVersions>;

    /// Install dependencies for a defined manifest.
    async fn install_dependencies(
        &self,
        tool: &T,
        working_dir: &Path,
        log: bool,
    ) -> miette::Result<()>;

    /// Install dependencies for a single package in the workspace.
    async fn install_focused_dependencies(
        &self,
        tool: &T,
        packages: &[String],
        production_only: bool,
    ) -> miette::Result<()>;
}
