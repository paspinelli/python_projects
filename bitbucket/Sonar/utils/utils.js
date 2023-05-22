const csv = require("fast-csv");
const fs = require("fs");
const chalk = require("chalk");

/**
 * Returns the larger date from an array of dates.
 * @param {string[]} dates An array of dates in ISO format.
 */
function getMaxDate(dates) {
  return dates.reduce((a, b) => (new Date(a) > new Date(b) ? a : b));
}

/**
 * Converts the string representation of a date and time from YYYY-MM-DDThh:mm:ssTZD (ISO format) to YYYY-MM-DD hh:mm:ss.
 * @param {String} s A string that contains a date and time to convert.
 */
function toShortDateTime(s) {
  if (!s) {
    throw new Error("s cannot be null");
  }
  return s.split("T").join(" ").split("+")[0];
}

function writeToCsvFile(filename, data) {
  const file = fs.createWriteStream(filename);
  csv.write(data, { headers: true }).pipe(file);
}

/**
 * Same as Promise.all(), but it waits for the first {batchSize} promises to finish
 * before starting the next batch.
 *
 * @param {function} task The task to run for each item.
 * @param {[]} items Arguments to pass to the task for each call.
 * @param {number} batchSize The size of each batch.
 * @param {any} data Optional data.
 * @returns {[]} An array of results from the task.
 */
async function promiseAllInBatches(task, items, batchSize, data) {
  let position = 0;
  let results = [];
  const batch = {
    number: 1,
    total: Math.ceil(items.length / batchSize),
  };
  try {
    while (position < items.length) {
      console.log(chalk.blue("=== Proccesing batch  ===", batch.number, "from", batch.total));
      batch.number += 1;

      const itemsForBatch = items.slice(position, position + batchSize);
      results = [
        ...results,
        ...(await Promise.all(
          itemsForBatch.map((item, index) => task(item, index, data))
        )),
      ];
      position += batchSize;
    }
  } catch (err) {
    throw new Error(err.message);
  }
  return results;
}

module.exports = {
  getMaxDate,
  toShortDateTime,
  writeToCsvFile,
  promiseAllInBatches,
};
