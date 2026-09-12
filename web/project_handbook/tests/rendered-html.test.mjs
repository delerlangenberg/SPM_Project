import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(new Request("http://localhost/", { headers: { accept: "text/html" } }), {
    ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) },
  }, { waitUntil() {}, passThroughOnException() {} });
}

test("renders the local construction handbook", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /SPM Prusa Project/);
  assert.match(html, /Construction sequence/);
  assert.match(html, /D8 socket Grove Yellow \/ D8/);
  assert.match(html, /D2 socket Grove White \/ D3/);
  assert.match(html, /Real Measurement/);
  assert.match(html, /234 physical measurements/);
  assert.match(html, /10\.0–11\.0 mm/);
  assert.doesNotMatch(html, /signin-with-chatgpt|oai-authenticated-user/i);
});

test("provides a readable offline index and clickable launcher", async () => {
  const [index, launcher] = await Promise.all([
    readFile(new URL("../index.html", import.meta.url), "utf8"),
    readFile(new URL("../OPEN_HANDBOOK.ps1", import.meta.url), "utf8"),
  ]);
  assert.match(index, /SPM Prusa construction handbook/);
  assert.match(index, /Open full interactive handbook/);
  assert.match(index, /Mega 2560 five-wire adapter/);
  assert.match(index, /D2 socket White \/ Mega D3/);
  assert.match(index, /D8 socket Yellow \/ Mega D8/);
  assert.match(index, /Adaptive 2D map/);
  assert.match(index, /Two-object discovery/);
  assert.match(index, /authoritative engineering record/);
  assert.match(launcher, /http:\/\/localhost:4310/);
  assert.match(launcher, /Start-Process/);
});
