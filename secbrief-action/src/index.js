const core = require("@actions/core");
const github = require("@actions/github");

async function run() {
  try {
    const apiKey = core.getInput("api-key", { required: true });
    const githubToken = core.getInput("github-token", { required: true });
    const failOnSeverity = core.getInput("fail-on-severity") || "critical";
    const apiUrl = core.getInput("secbrief-api-url") || "https://api.secbrief.dev";

    const octokit = github.getOctokit(githubToken);
    const context = github.context;

    if (context.eventName !== "pull_request") {
      core.warning("This action only runs on pull_request events");
      return;
    }

    const pullNumber = context.payload.pull_request.number;
    const repo = context.repo.repo;
    const owner = context.repo.owner;

    core.info(`Fetching changed files for PR #${pullNumber}...`);

    const { data: files } = await octokit.rest.pulls.listFiles({
      owner,
      repo,
      pull_number: pullNumber,
    });

    const changedFiles = [];
    const ecosystemFiles = [];

    const codeExtensions = [".js", ".ts", ".jsx", ".tsx", ".py", ".java", ".go", ".rb", ".php", ".cs"];
    const ecosystemNames = ["package-lock.json", "requirements.txt", "go.sum", "pom.xml", "Gemfile.lock"];

    for (const file of files) {
      if (file.status === "removed") continue;

      core.info(`Processing ${file.filename}...`);

      try {
        const { data: contentData } = await octokit.rest.repos.getContent({
          owner,
          repo,
          path: file.filename,
          ref: context.payload.pull_request.head.sha,
        });

        const content = Buffer.from(contentData.content, "base64").toString("utf-8");

        if (ecosystemNames.some((name) => file.filename.includes(name))) {
          ecosystemFiles.push({ filename: file.filename, content });
        } else if (codeExtensions.some((ext) => file.filename.endsWith(ext))) {
          changedFiles.push({ filename: file.filename, content });
        }
      } catch (err) {
        core.warning(`Could not fetch ${file.filename}: ${err.message}`);
      }
    }

    core.info(`Found ${changedFiles.length} code file(s) and ${ecosystemFiles.length} ecosystem file(s)`);

    const payload = {
      repo: `${owner}/${repo}`,
      pr_number: pullNumber,
      changed_files: changedFiles,
      ecosystem_files: ecosystemFiles,
    };

    core.info("Calling SecBrief API...");

    const response = await fetch(`${apiUrl}/api/github-scan`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      const text = await response.text();
      core.warning(`SecBrief API error (${response.status}): ${text}`);
      return;
    }

    const result = await response.json();

    core.setOutput("overall-severity", result.overall_severity);
    core.setOutput("total-findings", result.total_findings);

    core.info(`Scan complete: ${result.total_findings} finding(s), severity ${result.overall_severity}`);

    if (result.pr_comment) {
      core.info("Posting PR comment...");
      await octokit.rest.issues.createComment({
        owner,
        repo,
        issue_number: pullNumber,
        body: result.pr_comment,
      });
    }

    const severityOrder = ["low", "medium", "high", "critical"];
    const resultSeverityIndex = severityOrder.indexOf(result.overall_severity.toLowerCase());
    const failOnIndex = severityOrder.indexOf(failOnSeverity.toLowerCase());

    if (resultSeverityIndex >= failOnIndex && result.total_findings > 0) {
      core.setFailed(`SecBrief found ${result.total_findings} security issue(s). Overall severity: ${result.overall_severity}`);
    }
  } catch (error) {
    core.warning(`SecBrief action failed: ${error.message}`);
  }
}

run();
