import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import vm from "node:vm";

const repoRoot = process.cwd();
const searchDir = path.join(repoRoot, "site", "search");
const workerPath = path.join(searchDir, "worker.js");
const indexPath = path.join(searchDir, "search_index.json");

function runWorkerSearch(query) {
  const messages = [];
  const context = {
    console,
    postMessage(message) {
      messages.push(message);
    },
    importScripts(...urls) {
      for (const url of urls) {
        const scriptPath = path.join(searchDir, path.basename(url));
        vm.runInContext(fs.readFileSync(scriptPath, "utf8"), context, {
          filename: scriptPath,
        });
      }
    },
  };

  context.XMLHttpRequest = class {
    addEventListener(eventName, callback) {
      if (eventName === "load") {
        this.loadCallback = callback;
      }
    }

    open() {}

    send() {
      this.responseText = fs.readFileSync(indexPath, "utf8");
      this.loadCallback.call(this);
    }
  };

  vm.createContext(context);
  vm.runInContext(fs.readFileSync(workerPath, "utf8"), context, {
    filename: workerPath,
  });

  context.onmessage({ data: { init: true } });
  assert.equal(
    messages.some((message) => message.allowSearch === true),
    true,
    "search worker should finish loading"
  );

  context.onmessage({ data: { query } });
  const resultMessage = messages.findLast((message) => message.results);
  assert.ok(resultMessage, `search worker should return results for ${query}`);
  return resultMessage.results;
}

const expectations = [
  ["火锅", "short Chinese query should match recipe text", 200],
  ["丸子", "short Chinese query should match recipe text", 200],
  ["牡蛎煨面", "full Chinese dish name should match recipe text", 200],
  ["youtube", "ASCII query should keep matching source links", 300],
];

const searchIndex = JSON.parse(fs.readFileSync(indexPath, "utf8"));
assert.ok(
  searchIndex.config.min_search_length <= 2,
  "search page should submit two-character Chinese queries"
);

for (const [query, reason, maxResults] of expectations) {
  const results = runWorkerSearch(query);
  assert.ok(results.length > 0, `${reason}: ${query}`);
  assert.ok(
    results.length <= maxResults,
    `${reason}: ${query} should not return an overly broad result set`
  );
  console.log(`${query}: ${results.length}`);
}
