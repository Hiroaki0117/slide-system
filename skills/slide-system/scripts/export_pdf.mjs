#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const { PDFDocument } = require("pdf-lib");

function parseArgs(argv) {
  const result = {};
  for (let index = 0; index < argv.length; index += 2) {
    const key = argv[index];
    if (!key?.startsWith("--") || argv[index + 1] === undefined) throw new Error(`Invalid argument near ${key}`);
    result[key.slice(2)] = argv[index + 1];
  }
  for (const key of ["html", "pdf", "report", "work-state"]) {
    if (!result[key]) throw new Error(`Missing --${key}`);
  }
  return result;
}

function readWorkflowState(workStatePath) {
  const resolved = path.resolve(workStatePath);
  if (!fs.existsSync(resolved)) throw new Error(`PRODUCTION_NOT_APPROVED: work-state not found: ${resolved}`);
  const state = JSON.parse(fs.readFileSync(resolved, "utf8"));
  const approval = state.approval || {};
  const approved = ["approved", "waived"].includes(String(approval.status || "")) && String(approval.user_reply || "").trim();
  const revision = state.revision || {};
  const revisionApproved = [revision.source_artifact, revision.scope, revision.user_reply].every(value => String(value || "").trim());
  if (!approved && !revisionApproved) throw new Error("PRODUCTION_NOT_APPROVED: explicit approval record is required");
  const phase = String(state.phase || "");
  const pdfReply = String(state.pdf_request?.user_reply || "").trim();
  if (!["pdf_requested", "qa"].includes(phase) || !pdfReply) {
    throw new Error("PDF_STAGE_NOT_REQUESTED: an exact follow-up reply is required before PDF export");
  }
  return { path: resolved, phase, delivery_profile: String(state.delivery_profile || "standard") };
}

function findBrowser(explicitPath) {
  const candidates = [
    explicitPath,
    process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH,
    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
    "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
    "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    "/usr/bin/google-chrome",
    "/usr/bin/chromium",
    "/usr/bin/chromium-browser",
  ].filter(Boolean);
  return candidates.find(candidate => fs.existsSync(candidate)) || null;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const workflow = readWorkflowState(args["work-state"]);
  const htmlPath = path.resolve(args.html);
  const pdfPath = path.resolve(args.pdf);
  const reportPath = path.resolve(args.report);
  if (!fs.existsSync(htmlPath)) throw new Error(`HTML not found: ${htmlPath}`);
  fs.mkdirSync(path.dirname(pdfPath), { recursive: true });
  fs.mkdirSync(path.dirname(reportPath), { recursive: true });

  const browserPath = findBrowser(args.browser);
  const browser = await chromium.launch({ headless: true, ...(browserPath ? { executablePath: browserPath } : {}) });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
  const consoleErrors = [];
  page.on("console", message => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("pageerror", error => consoleErrors.push(error.message));
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "networkidle" });
  const checks = await page.evaluate(async () => {
    await document.fonts.ready;
    const slideCount = window.deckSlideCount || document.querySelectorAll(".slide").length;
    const fontLoaded = document.fonts.check('700 48px "Slide Noto Sans JP"');
    return { slideCount, fontLoaded, fontStatus: document.fonts.status };
  });
  if (!checks.slideCount) throw new Error("No slides found in HTML");
  if (!checks.fontLoaded || checks.fontStatus !== "loaded") throw new Error("FONT_LOAD: bundled Slide Noto Sans JP did not load");

  await page.emulateMedia({ media: "print" });
  const controlsHidden = await page.evaluate(() => {
    const controls = document.querySelector(".controls");
    return !controls || getComputedStyle(controls).display === "none";
  });
  if (!controlsHidden) throw new Error("PRINT_UI_VISIBLE: slide controls would appear in the PDF");

  // Save the requested artifact immediately. Detailed screenshot QA is a later,
  // optional pass so a resource-limited session cannot end before PDF delivery.
  const pdfBuffer = await page.pdf({
    printBackground: true,
    preferCSSPageSize: true,
    margin: { top: "0", right: "0", bottom: "0", left: "0" },
  });
  fs.writeFileSync(pdfPath, pdfBuffer);
  await browser.close();

  const pdf = await PDFDocument.load(pdfBuffer);
  const pageCount = pdf.getPageCount();
  const sizes = pdf.getPages().map(item => item.getSize());
  const aspectPass = sizes.every(({ width, height }) => Math.abs(width / height - 16 / 9) < 0.01);
  const failures = [];
  if (pageCount !== checks.slideCount) failures.push({ code: "PDF_PAGE_COUNT", message: `${pageCount} PDF pages for ${checks.slideCount} slides` });
  if (!aspectPass) failures.push({ code: "PDF_ASPECT", message: "One or more PDF pages are not 16:9" });
  if (consoleErrors.length) failures.push({ code: "CONSOLE", details: consoleErrors });

  const report = {
    status: failures.length ? "FAIL" : "PASS",
    workflow,
    html: htmlPath,
    pdf: pdfPath,
    slide_count: checks.slideCount,
    pdf_pages: pageCount,
    font: { loaded: checks.fontLoaded, status: checks.fontStatus },
    controls_hidden: controlsHidden,
    aspect_16_9: aspectPass,
    failures,
  };
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf8");
  process.stdout.write(JSON.stringify({ status: report.status, pdf: pdfPath, slide_count: checks.slideCount, pdf_pages: pageCount, report: reportPath, failure_count: failures.length }));
  process.exitCode = failures.length ? 2 : 0;
}

main().catch(error => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 2;
});
