use rmcp::model::{CallToolResult, Content};
use std::path::Path;
use std::process::Command;

pub struct Harness;

impl Harness {
    pub fn intercept(path: &Path, original_result: CallToolResult) -> CallToolResult {
        if original_result.is_error == Some(true) {
            return original_result;
        }

        let parent_dir = path.parent().unwrap_or(Path::new("."));
        let file_name = path.file_name().unwrap_or_default().to_string_lossy();
        let mut lint_cmd = None;
        let mut linter_name = "";

        if file_name.ends_with(".py") {
            let mut cmd = Command::new("ruff");
            cmd.arg("check").arg(path).current_dir(parent_dir);
            lint_cmd = Some(cmd);
            linter_name = "ruff";
        } else if file_name.ends_with(".js") || file_name.ends_with(".ts") || file_name.ends_with(".jsx") || file_name.ends_with(".tsx") {
            let mut cmd = Command::new("npx");
            cmd.arg("eslint").arg(path).current_dir(parent_dir);
            lint_cmd = Some(cmd);
            linter_name = "eslint";
        } else if file_name.ends_with(".rs") {
            let mut cmd = Command::new("cargo");
            cmd.arg("clippy").arg("--").arg("-D").arg("warnings").current_dir(parent_dir);
            lint_cmd = Some(cmd);
            linter_name = "cargo clippy";
        }

        if let Some(mut cmd) = lint_cmd {
            match cmd.output() {
                Ok(output) => {
                    if !output.status.success() {
                        let stdout = String::from_utf8_lossy(&output.stdout);
                        let stderr = String::from_utf8_lossy(&output.stderr);
                        return CallToolResult::error(vec![Content::text(format!(
                            "Linter failed on {}:\nSTDOUT:\n{}\nSTDERR:\n{}",
                            path.display(),
                            stdout,
                            stderr
                        )).with_priority(0.0)]);
                    }
                }
                Err(e) => {
                    return CallToolResult::error(vec![Content::text(format!(
                        "Failed to spawn linter '{}' on {}: {}",
                        linter_name,
                        path.display(),
                        e
                    )).with_priority(0.0)]);
                }
            }
        }

        let _ = Command::new("git").arg("add").arg(path).current_dir(parent_dir).output();
        let commit_msg = format!("Auto-commit: Modified {}", path.display());
        let _ = Command::new("git").arg("commit").arg("-m").arg(&commit_msg).current_dir(parent_dir).output();

        original_result
    }
}
