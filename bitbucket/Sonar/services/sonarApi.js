"use strict";

const axios = require("axios");

const SONAR_TOKEN = process.env.SONAR_TOKEN;
const BASE_URL = `https://${SONAR_TOKEN}@sonarcloud.io/api/`;
const ORGANIZATION = process.env.BITBUCKET_WORKSPACE;
const BRANCH_NAME = "master";
const MAX_PAGE_SIZE = 500;

async function fetchProjects(page = 1) {
  let projects = [];
  try {
    const {
      data: {
        components,
        paging: { pageSize, total },
      },
    } = await axios.get(BASE_URL + "projects/search", {
      params: {
        organization: ORGANIZATION,
        p: page, // page number
        ps: MAX_PAGE_SIZE,
      },
    });

    const totalPages = Math.ceil(total / pageSize);

    if (page < totalPages) {
      projects.concat(await fetchProjects(page + 1));
    } else {
      projects = components;
    }
  } catch (err) {
    throw new Error(err.message);
  }
  return projects;
}

async function getIssuesTotals(project, types = null, severities = null) {
  try {
    const {
      data: { total },
    } = await axios.get(BASE_URL + "issues/search", {
      params: {
        projects: project.key,
        branch: BRANCH_NAME,
        organization: ORGANIZATION,
        statuses: "OPEN",
        types,
        severities,
      },
    });

    return total;
  } catch (err) {
    throw new Error(err.message);
  }
}

async function fetchOwaspTop10(project) {
  const owaspTop10 = {};
  try {
    const {
      data: { facets },
    } = await axios.get(
      `https://${SONAR_TOKEN}@sonarcloud.io/api/issues/search`,
      {
        params: {
          projects: project.key,
          branch: "master",
          facets: "owaspTop10",
          organization: ORGANIZATION,
        },
      }
    );
    facets[0].values.forEach((value) => {
      owaspTop10[value.val] = value.count;
    });
  } catch (err) {
    throw new Error(err.message);
  }
  return owaspTop10;
}

async function getLastIssueDate(project) {
  try {
    const {
      data: { issues },
    } = await axios.get(
      `https://${SONAR_TOKEN}@sonarcloud.io/api/issues/search`,
      {
        params: {
          projects: project.key,
          branch: "master",
          organization: ORGANIZATION,
          statuses: "OPEN",
          s: "CREATION_DATE", // sort field
          asc: "no", // ascending sort
        },
      }
    );

    if (issues.length !== 0) {
      return issues[0].creationDate;
    } else {
      return null;
    }
  } catch (err) {
    throw new Error(err.message);
  }
}

module.exports = {
  fetchProjects,
  fetchOwaspTop10,
  getIssuesTotals,
  getLastIssueDate,
};
