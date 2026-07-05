// MkDocs 1.6.1 readthedocs search worker override.
// This keeps the default Lunr search flow and adds a CJK n-gram fallback so
// Chinese short words and substrings can match cookbook content. Re-check this
// file against MkDocs' bundled search/worker.js before upgrading MkDocs.
var base_path = 'function' === typeof importScripts ? '.' : '/search/';
var allowSearch = false;
var index;
var documents = {};
var lang = ['en'];
var data;
var cjkIndex = {};
var cjkDocumentLengths = {};

function getScript(script, callback) {
  console.log('Loading script: ' + script);
  $.getScript(base_path + script).done(function () {
    callback();
  }).fail(function (jqxhr, settings, exception) {
    console.log('Error: ' + exception);
  });
}

function getScriptsInOrder(scripts, callback) {
  if (scripts.length === 0) {
    callback();
    return;
  }
  getScript(scripts[0], function() {
    getScriptsInOrder(scripts.slice(1), callback);
  });
}

function loadScripts(urls, callback) {
  if( 'function' === typeof importScripts ) {
    importScripts.apply(null, urls);
    callback();
  } else {
    getScriptsInOrder(urls, callback);
  }
}

function normalizeText(value) {
  return String(value || '').toLowerCase();
}

function getCjkTerms(text) {
  var terms = [];
  var seen = {};
  var normalized = normalizeText(text);
  var cjkRuns = normalized.match(/[\u3400-\u9fff]+/g) || [];

  for (var i = 0; i < cjkRuns.length; i++) {
    var run = cjkRuns[i];
    for (var start = 0; start < run.length; start++) {
      for (var size = 2; size <= 4 && start + size <= run.length; size++) {
        var term = run.slice(start, start + size);
        if (!seen[term]) {
          seen[term] = true;
          terms.push(term);
        }
      }
    }
  }

  return terms;
}

function addCjkTerm(term, location, weight) {
  if (!cjkIndex[term]) {
    cjkIndex[term] = {};
  }
  cjkIndex[term][location] = (cjkIndex[term][location] || 0) + weight;
}

function buildCjkIndex(docs) {
  cjkIndex = {};
  cjkDocumentLengths = {};

  for (var i = 0; i < docs.length; i++) {
    var doc = docs[i];
    var location = doc.location;
    var titleTerms = getCjkTerms(doc.title);
    var textTerms = getCjkTerms(doc.text);

    cjkDocumentLengths[location] = normalizeText(doc.title).length + normalizeText(doc.text).length;

    for (var titleIndex = 0; titleIndex < titleTerms.length; titleIndex++) {
      addCjkTerm(titleTerms[titleIndex], location, 8);
    }

    for (var textIndex = 0; textIndex < textTerms.length; textIndex++) {
      addCjkTerm(textTerms[textIndex], location, 1);
    }
  }
}

function scoreCjkResults(query) {
  var queryTerms = getCjkTerms(query);
  var scores = {};

  for (var i = 0; i < queryTerms.length; i++) {
    var term = queryTerms[i];
    var postings = cjkIndex[term];
    if (!postings) {
      continue;
    }

    var termWeight = Math.min(term.length, 4);
    for (var location in postings) {
      if (Object.prototype.hasOwnProperty.call(postings, location)) {
        scores[location] = (scores[location] || 0) + postings[location] * termWeight;
      }
    }
  }

  var results = [];
  for (var resultLocation in scores) {
    if (Object.prototype.hasOwnProperty.call(scores, resultLocation)) {
      results.push({
        location: resultLocation,
        score: scores[resultLocation],
        length: cjkDocumentLengths[resultLocation] || 0
      });
    }
  }

  results.sort(function (left, right) {
    if (right.score !== left.score) {
      return right.score - left.score;
    }
    return left.length - right.length;
  });

  return results;
}

function onJSONLoaded () {
  data = JSON.parse(this.responseText);
  var scriptsToLoad = ['lunr.js'];
  if (data.config && data.config.lang && data.config.lang.length) {
    lang = data.config.lang;
  }
  if (lang.length > 1 || lang[0] !== "en") {
    scriptsToLoad.push('lunr.stemmer.support.js');
    if (lang.length > 1) {
      scriptsToLoad.push('lunr.multi.js');
    }
    if (lang.includes("ja") || lang.includes("jp")) {
      scriptsToLoad.push('tinyseg.js');
    }
    for (var i=0; i < lang.length; i++) {
      if (lang[i] != 'en') {
        scriptsToLoad.push(['lunr', lang[i], 'js'].join('.'));
      }
    }
  }
  loadScripts(scriptsToLoad, onScriptsLoaded);
}

function onScriptsLoaded () {
  console.log('All search scripts loaded, building Lunr index...');
  if (data.config && data.config.separator && data.config.separator.length) {
    lunr.tokenizer.separator = new RegExp(data.config.separator);
  }

  if (data.index) {
    index = lunr.Index.load(data.index);
    data.docs.forEach(function (doc) {
      documents[doc.location] = doc;
    });
    console.log('Lunr pre-built index loaded, search ready');
  } else {
    index = lunr(function () {
      if (lang.length === 1 && lang[0] !== "en" && lunr[lang[0]]) {
        this.use(lunr[lang[0]]);
      } else if (lang.length > 1) {
        this.use(lunr.multiLanguage.apply(null, lang));
      }
      this.field('title');
      this.field('text');
      this.ref('location');

      for (var i=0; i < data.docs.length; i++) {
        var doc = data.docs[i];
        this.add(doc);
        documents[doc.location] = doc;
      }
    });
    console.log('Lunr index built, search ready');
  }

  buildCjkIndex(data.docs);
  allowSearch = true;
  postMessage({config: data.config});
  postMessage({allowSearch: allowSearch});
}

function init () {
  var oReq = new XMLHttpRequest();
  oReq.addEventListener("load", onJSONLoaded);
  var index_path = base_path + '/search_index.json';
  if( 'function' === typeof importScripts ){
      index_path = 'search_index.json';
  }
  oReq.open("GET", index_path);
  oReq.send();
}

function addResult(resultDocuments, seenLocations, location) {
  if (!documents[location] || seenLocations[location]) {
    return;
  }

  var doc = documents[location];
  doc.summary = doc.text.substring(0, 200);
  resultDocuments.push(doc);
  seenLocations[location] = true;
}

function search (query) {
  if (!allowSearch) {
    console.error('Assets for search still loading');
    return;
  }

  var resultDocuments = [];
  var seenLocations = {};
  var results = index.search(query);

  for (var i=0; i < results.length; i++){
    addResult(resultDocuments, seenLocations, results[i].ref);
  }

  var cjkResults = scoreCjkResults(query);
  for (var cjkIndexPosition=0; cjkIndexPosition < cjkResults.length; cjkIndexPosition++) {
    addResult(resultDocuments, seenLocations, cjkResults[cjkIndexPosition].location);
  }

  return resultDocuments;
}

if( 'function' === typeof importScripts ) {
  onmessage = function (e) {
    if (e.data.init) {
      init();
    } else if (e.data.query) {
      postMessage({ results: search(e.data.query) });
    } else {
      console.error("Worker - Unrecognized message: " + e);
    }
  };
}
