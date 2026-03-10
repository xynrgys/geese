use regex::Regex;
use std::path::Path;

pub struct ToolShed;

impl ToolShed {
    pub async fn fetch(target: &str) -> String {
        if target.starts_with("http://") || target.starts_with("https://") {
            // Fetch URL
            match reqwest::get(target).await {
                Ok(response) => {
                    response.text().await.unwrap_or_else(|_| format!("Failed to read text from {}", target))
                }
                Err(e) => format!("Failed to fetch {}: {}", target, e),
            }
        } else if Path::new(target).exists() {
            // Read file
            std::fs::read_to_string(target).unwrap_or_else(|e| format!("Failed to read file {}: {}", target, e))
        } else if target.chars().all(|c| c.is_ascii_uppercase() || c.is_ascii_digit() || c == '-') && target.contains('-') {
            // Mock Jira ID
            format!("Jira issue {} content (mocked)", target)
        } else {
            format!("Could not fetch content for {}", target)
        }
    }
}

pub struct Hydrator;

impl Hydrator {
    pub async fn hydrate(prompt: &str) -> String {
        let mut context_blocks = Vec::new();

        // 1. Parse GitHub URLs
        if let Ok(gh_re) = Regex::new(r"https?://github\.com/[^\s]+") {
            for cap in gh_re.captures_iter(prompt) {
                let url = &cap[0];
                let content = ToolShed::fetch(url).await;
                context_blocks.push(format!("Content for {}:\n{}", url, content));
            }
        }

        // Jira IDs (e.g., PROJ-123)
        if let Ok(jira_re) = Regex::new(r"\b[A-Z]+-\d+\b") {
            for cap in jira_re.captures_iter(prompt) {
                let id = &cap[0];
                let content = ToolShed::fetch(id).await;
                context_blocks.push(format!("Content for Jira {}:\n{}", id, content));
            }
        }

        // File paths
        for word in prompt.split_whitespace() {
            if Path::new(word).is_file() {
                let content = ToolShed::fetch(word).await;
                context_blocks.push(format!("Content for file {}:\n{}", word, content));
            }
        }

        if context_blocks.is_empty() {
            return String::new();
        }

        format!("--- Initial Context Block ---\n{}\n---------------------------\n", context_blocks.join("\n\n"))
    }
}
