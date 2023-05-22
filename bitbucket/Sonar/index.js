"use strict";

const chalk = require("chalk");
const figlet = require("figlet");

const bitbucketApi = require("./services/bitbucketApi");
const sonarApi = require("./services/sonarApi");
const {
  promiseAllInBatches,
  toShortDateTime,
  writeToCsvFile,
} = require("./utils");

const bitbucketColor = chalk.blue;
const sonarColor = chalk.red;
const info = chalk.yellow;

async function main() {
  try {
    // Print title.
    console.log(
      bitbucketColor(
        figlet.textSync("x-sonar", { horizontalLayout: "fitted" })
      )
    );

    console.log("\nGetting repository list from Bitbucket... ");
    const bitbucketRepos = await bitbucketApi.fetchRepositories();
    console.log("done.");

    const [sonarData, bitbucketData] = await Promise.all([
      getSonarData(bitbucketRepos),
      getBitbucketData(bitbucketRepos),
    ]);

    const output = mergeBitbucketAndSonarData(bitbucketData, sonarData);
    writeToCsvFile("output.csv", output);

    console.info(chalk.green("All done!"));
  } catch (err) {
    if (err) {
      switch (err.status) {
        default:
          console.error(chalk.red(err));
          throw err;
      }
    }
  }
}

async function getBitbucketData(repos) {
  console.log(bitbucketColor("Getting Bitbucket data..."));
  const output = await promiseAllInBatches(getBitbucketDataItem, repos, 100);
  console.log(info("Bitbucket data done."));

  return output;
}

async function getBitbucketDataItem(repo, i) {
  // console.log(chalk.blue("element " + i));

  const branch = repo.mainbranch ? repo.mainbranch.name : "master";

  const [defaultReviewers, lastCommit] = await Promise.all([
    bitbucketApi.fetchDefaultReviewers(repo.uuid),
    bitbucketApi.fetchLastCommit(repo.uuid, branch),
  ]);

  // console.log(bitbucketColor(`done ${i}`));

  return {
    workspace: repo.workspace.name,
    project: {
      id: repo.project.uuid,
      name: repo.project.name,
    },
    repo: {
      id: repo.uuid,
      name: repo.name,
    },
    pullRequestEnabled: "yes",
    defaultReviewers: defaultReviewers,
    lastCommitDate: lastCommit && lastCommit.date,
  };
}

async function getSonarDataItem(project, i, bitbucketRepos) {
  console.log(info(`Fetching issues from project ${project.key}...`, i));
  const issuesTotal = await sonarApi.getIssuesTotals(project);
  if (issuesTotal === 0) {
    console.log(sonarColor(`${project.key} has no issues.`, i));
    return null;
  }
  console.log(sonarColor(`${project.key} issues done.`, i));

  console.log(info(`Fetching OWASP from ${project.key}`, i));
  const owaspTop10 = await sonarApi.fetchOwaspTop10(project);
  console.log(sonarColor(`OWASP from ${project.key} done.`, i));

  const bitbucketRepo = bitbucketRepos.find(
    (r) => r.slug === project.key.replace(project.organization + "_", "") // remove the workspace prefix from the key
  );

  if (!bitbucketRepo) {
    console.log(
      `${project.key.replace(project.organization + "_", "")} does not exist on the ${process.env.BITBUCKET_WORKSPACE} workspace from Bitbucket on SONAR.`, i);
    return null;
  }

  return {
    bitbucketRepoId: bitbucketRepo.uuid,
    sonarId: project.key,
    openIssues: {
      total: issuesTotal,
      bugs: {
        total: await sonarApi.getIssuesTotals(project, "BUG"),
        blocker: await sonarApi.getIssuesTotals(project, "BUG", "BLOCKER"),
        critical: await sonarApi.getIssuesTotals(project, "BUG", "CRITICAL"),
        major: await sonarApi.getIssuesTotals(project, "BUG", "MAJOR"),
        minor: await sonarApi.getIssuesTotals(project, "BUG", "MINOR"),
        info: await sonarApi.getIssuesTotals(project, "BUG", "INFO"),
      },
      vulnerabilities: {
        total: await sonarApi.getIssuesTotals(project, "VULNERABILITY"),
        blocker: await sonarApi.getIssuesTotals(project, "VULNERABILITY", "BLOCKER"),
        critical: await sonarApi.getIssuesTotals(project, "VULNERABILITY", "CRITICAL"),
        major: await sonarApi.getIssuesTotals(project, "VULNERABILITY", "MAJOR"),
        minor: await sonarApi.getIssuesTotals(project, "VULNERABILITY", "MINOR"),
        info: await sonarApi.getIssuesTotals(project, "VULNERABILITY", "INFO"),
      },
      codeSmells: {
        total: await sonarApi.getIssuesTotals(project, "CODE_SMELL"),
        blocker: await sonarApi.getIssuesTotals(project, "CODE_SMELL", "BLOCKER"),
        critical: await sonarApi.getIssuesTotals(project, "CODE_SMELL", "CRITICAL"),
        major: await sonarApi.getIssuesTotals(project, "CODE_SMELL", "MAJOR"),
        minor: await sonarApi.getIssuesTotals(project, "CODE_SMELL", "MINOR"),
        info: await sonarApi.getIssuesTotals(project, "CODE_SMELL", "INFO"),
      },
    },
    owaspA1: owaspTop10.a1 ? owaspTop10.a1 : 0,
    owaspA2: owaspTop10.a2 ? owaspTop10.a2 : 0,
    owaspA3: owaspTop10.a3 ? owaspTop10.a3 : 0,
    owaspA4: owaspTop10.a4 ? owaspTop10.a4 : 0,
    owaspA5: owaspTop10.a5 ? owaspTop10.a5 : 0,
    owaspA6: owaspTop10.a6 ? owaspTop10.a6 : 0,
    owaspA7: owaspTop10.a7 ? owaspTop10.a7 : 0,
    owaspA8: owaspTop10.a8 ? owaspTop10.a8 : 0,
    owaspA9: owaspTop10.a9 ? owaspTop10.a9 : 0,
    owaspA10: owaspTop10.a10 ? owaspTop10.a10 : 0,
    lastScanDate: project.lastAnalysisDate,
    lastIssueDate: await sonarApi.getLastIssueDate(project),
  };
}

async function getSonarData(bitbucketRepos) {
  console.log(sonarColor("Processing Sonar data..."));

  console.log(sonarColor("Fetching Sonar projects..."));
  const projects = await sonarApi.fetchProjects();
  console.log(sonarColor("sonar projects done."));

  const output = await promiseAllInBatches(
    getSonarDataItem,
    projects,
    100,
    bitbucketRepos
  );

  console.log(info("Sonar data done. Please review the output.csv file generated in the ROOT folder"));
  return output.filter((d) => d !== null);
}

function mergeBitbucketAndSonarData(bitbucketData, sonarData) {
  return bitbucketData.map((b) => {
    const s = sonarData.find((s) => s.bitbucketRepoId === b.repo.id);

    return {
      Workspace: b.workspace,
      Project: b.project.name,
      Repository: b.repo.name,
      "Repository ID": b.repo.id,
      "Pull Request Enabled?": b.pullRequestEnabled,
      "Default Pull Request Approvers": b.defaultReviewers.length
        ? b.defaultReviewers.length
        : "N/A",
      "Last Commit": b.lastCommitDate
        ? toShortDateTime(b.lastCommitDate)
        : null,
      "Sonar ID": s && s.sonarId,
      "Open Issues Total": s && s.openIssues.total,
      "Open Bugs Total": s && s.openIssues.bugs.total,
      "Blocker Bugs": s && s.openIssues.bugs.blocker,
      "Critical Bugs": s && s.openIssues.bugs.critical,
      "Major Bugs": s && s.openIssues.bugs.major,
      "Info Bugs": s && s.openIssues.bugs.info,
      "Minor Bugs": s && s.openIssues.bugs.minor,
      "Open Vulnerabilities Total": s && s.openIssues.vulnerabilities.total,
      "Blocker Vulnerabilities": s && s.openIssues.vulnerabilities.blocker,
      "Critical Vulnerabilities": s && s.openIssues.vulnerabilities.critical,
      "Major Vulnerabilities": s && s.openIssues.vulnerabilities.major,
      "Info Vulnerabilities": s && s.openIssues.vulnerabilities.info,
      "Minor Vulnerabilities": s && s.openIssues.vulnerabilities.minor,
      "Open Code Smells Total": s && s.openIssues.codeSmells.total,
      "Blocker Code Smells": s && s.openIssues.codeSmells.blocker,
      "Critical Code Smells": s && s.openIssues.codeSmells.critical,
      "Major Code Smells": s && s.openIssues.codeSmells.major,
      "Info Code Smells": s && s.openIssues.codeSmells.info,
      "Minor Code Smells": s && s.openIssues.codeSmells.minor,
      "owasp a1": s && s.owaspA1,
      "owasp a2": s && s.owaspA2,
      "owasp a3": s && s.owaspA3,
      "owasp a4": s && s.owaspA4,
      "owasp a5": s && s.owaspA5,
      "owasp a6": s && s.owaspA6,
      "owasp a7": s && s.owaspA7,
      "owasp a8": s && s.owaspA8,
      "owasp a9": s && s.owaspA9,
      "owasp a10": s && s.owaspA10,
      "Last Issue": s && toShortDateTime(s.lastIssueDate),
      "Last Scan": s && toShortDateTime(s.lastScanDate),
    };
  });
}

main();
