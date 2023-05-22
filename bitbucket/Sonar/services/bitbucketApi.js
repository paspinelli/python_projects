"use strict";

const axios = require("axios");

const WORKSPACE = process.env.BITBUCKET_WORKSPACE;
const BASE_URL = `https://api.bitbucket.org/2.0/repositories/${WORKSPACE}/`;
const MAX_PAGE_SIZE = 100;

const auth = {
  username: process.env.BITBUCKET_USER,
  password: process.env.BITBUCKET_PASS,
};

async function fetchRepositories(page = 1) {
  let repos;
  try {
    const {
      data: { pagelen, size, values },
    } = await axios.get(BASE_URL, {
      params: {
        page,
        pagelen: MAX_PAGE_SIZE
      },
      auth,
    });

    const totalPages = Math.ceil(size / pagelen);

    if (page < totalPages) {
      repos = values.concat(await fetchRepositories(page + 1));
    } else {
      repos = values;
    }
  } catch (err) {
    throw err;
  }
  return repos;
}

async function fetchDefaultReviewers(repoUiid) {
  let reviewers = [];
  try {
    const response = await axios.get(BASE_URL + `${repoUiid}/default-reviewers`, {
      params: {
        fields: "values.display_name",
      },
      auth,
    });
    reviewers = response.data.values
      .map((reviewer) => reviewer.display_name)
      .join(", ");
  } catch (err) {
    throw err;
  }
  return reviewers;
}

async function fetchLastCommit(repoUiid, branch) {
  let lastCommit = null;
  try {
    const response = await axios.get(BASE_URL + `${repoUiid}/commits/${branch}`, {
      auth: auth,
    });
    lastCommit = response.data.values[0];
  } catch (err) {
    throw err;
  }
  return lastCommit;
}

module.exports = {
  fetchRepositories,
  fetchDefaultReviewers,
  fetchLastCommit,
};
