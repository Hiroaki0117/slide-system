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
  for (let i = 0; i < argv.length; i += 2) {
    const key = argv[i];
    if (!key?.startsWith("--") || argv[i + 1] === undefined) throw new Error(`Invalid argument near ${key}`);
    result[key.slice(2)] = argv[i + 1];
  }
  for (const key of ["html", "pdf", "renders", "report", "work-state"]) {
    if (!result[key]) throw new Error(`Missing --${key}`);
  }
  return result;
}

function readWorkflowState(workStatePath) {
  const resolved = path.resolve(workStatePath);
  if (!fs.existsSync(resolved)) throw new Error(`PRODUCTION_NOT_APPROVED: work-state not found: ${resolved}`);
  const state = JSON.parse(fs.readFileSync(resolved, "utf8"));
  const approval = state.approval || {};
  const approvalStatus = String(approval.status || "");
  const approvalReply = String(approval.user_reply || "").trim();
  const revision = state.revision || {};
  const revisionApproved = [revision.source_artifact, revision.scope, revision.user_reply]
    .every(value => String(value || "").trim());
  if ((!['approved', 'waived'].includes(approvalStatus) || !approvalReply) && !revisionApproved) {
    throw new Error("PRODUCTION_NOT_APPROVED: explicit approval record is required");
  }

  const phase = String(state.phase || "");
  const deliveryProfile = String(state.delivery_profile || "standard");
  if (deliveryProfile === "staged") {
    const pdfReply = String(state.pdf_request?.user_reply || "").trim();
    if (!["pdf_requested", "qa"].includes(phase) || !pdfReply) {
      throw new Error("PDF_STAGE_NOT_REQUESTED: deliver HTML and wait for the user's next reply before rendering PDF");
    }
  } else if (!["approved", "building", "qa"].includes(phase)) {
    throw new Error(`PRODUCTION_NOT_APPROVED: unsupported production phase ${phase || "(missing)"}`);
  }
  return { path: resolved, phase, delivery_profile: deliveryProfile, approval_status: approvalStatus };
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
    "/opt/google/chrome/chrome",
  ].filter(Boolean);
  return candidates.find(candidate => fs.existsSync(candidate)) || null;
}

async function makeContactSheet(browser, imagePaths, outputPath) {
  const thumbs = imagePaths.map((imagePath, index) => {
    const data = fs.readFileSync(imagePath).toString("base64");
    return `<figure><img src="data:image/png;base64,${data}"><figcaption>${String(index + 1).padStart(2, "0")}</figcaption></figure>`;
  }).join("");
  const sheet = await browser.newPage({ viewport: { width: 1600, height: 900 } });
  await sheet.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>
    *{box-sizing:border-box}html,body{margin:0;background:#e9ecef;font-family:Arial,sans-serif}main{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;padding:24px}figure{margin:0;background:#fff;padding:8px;border-radius:8px;box-shadow:0 2px 10px #0002}img{width:100%;aspect-ratio:16/9;object-fit:contain;display:block}figcaption{text-align:right;padding:6px 4px 0;color:#555;font-weight:700}
  </style></head><body><main>${thumbs}</main></body></html>`, { waitUntil: "load" });
  await sheet.screenshot({ path: outputPath, fullPage: true });
  await sheet.close();
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const workflow = readWorkflowState(args["work-state"]);
  const htmlPath = path.resolve(args.html);
  const pdfPath = path.resolve(args.pdf);
  const renderDir = path.resolve(args.renders);
  const reportPath = path.resolve(args.report);
  if (!fs.existsSync(htmlPath)) throw new Error(`HTML not found: ${htmlPath}`);
  fs.mkdirSync(path.dirname(pdfPath), { recursive: true });
  fs.mkdirSync(renderDir, { recursive: true });
  fs.mkdirSync(path.dirname(reportPath), { recursive: true });

  const browserPath = findBrowser(args.browser);
  const browser = await chromium.launch({ headless: true, ...(browserPath ? { executablePath: browserPath } : {}) });
  const page = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
  const consoleErrors = [];
  page.on("console", message => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("pageerror", error => consoleErrors.push(error.message));
  await page.goto(pathToFileURL(htmlPath).href, { waitUntil: "networkidle" });
  const fontCheck = await page.evaluate(async () => {
    await document.fonts.ready;
    const loaded = document.fonts.check('700 48px "Slide Noto Sans JP"');
    const probe = document.createElement("span");
    probe.textContent = "日本語フォント確認";
    probe.style.cssText = 'position:absolute;visibility:hidden;font:700 48px "Slide Noto Sans JP"';
    document.body.appendChild(probe);
    const family = getComputedStyle(probe).fontFamily;
    probe.remove();
    return { loaded, family, status: document.fonts.status };
  });

  const slideCount = await page.evaluate(() => window.deckSlideCount || document.querySelectorAll(".slide").length);
  if (!slideCount) throw new Error("No slides found in HTML");

  const navigation = await page.evaluate(count => {
    const read = () => document.getElementById("indicator")?.textContent?.trim();
    const initial = read();
    window.showSlide(1);
    const second = read();
    window.showSlide(count + 5);
    const clampedEnd = read();
    window.showSlide(-5);
    const clampedStart = read();
    return { initial, second, clampedEnd, clampedStart };
  }, slideCount);

  const expectedSecond = slideCount > 1 ? `2 / ${slideCount}` : `1 / ${slideCount}`;
  const navigationPass = navigation.initial === `1 / ${slideCount}` && navigation.second === expectedSecond && navigation.clampedEnd === `${slideCount} / ${slideCount}` && navigation.clampedStart === `1 / ${slideCount}`;

  // Navigation is tested above. Hide viewer-only UI before visual inspection so
  // it cannot obscure slide content in screenshots or the contact sheet.
  await page.addStyleTag({ content: ".controls,.draft-banner{display:none!important}" });

  const slides = [];
  const imagePaths = [];
  for (let index = 0; index < slideCount; index += 1) {
    await page.evaluate(i => window.showSlide(i), index);
    await page.waitForTimeout(40);
    const qa = await page.evaluate(() => {
      const slide = document.querySelector(".slide.active");
      const slideRect = slide.getBoundingClientRect();
      const overflow = [];
      for (const element of slide.querySelectorAll("h1,h2,h3,p,li,table,.panel,.step,.stat,.image-frame,.actions,.sources-list,.message-stage,.text-focus-grid,.process-grid,.bar-chart,.exercise-box")) {
        const rect = element.getBoundingClientRect();
        const style = getComputedStyle(element);
        if (style.display === "none" || style.visibility === "hidden") continue;
        if (rect.left < slideRect.left - 1 || rect.right > slideRect.right + 1 || rect.top < slideRect.top - 1 || rect.bottom > slideRect.bottom + 1) {
          overflow.push(`${element.tagName.toLowerCase()}.${element.className || ""}`);
        }
      }
      const h2 = slide.querySelector("h2");
      let titleWrap = false;
      if (h2) {
        const lineHeight = Number.parseFloat(getComputedStyle(h2).lineHeight);
        titleWrap = Number.isFinite(lineHeight) && h2.getBoundingClientRect().height > lineHeight * 1.45;
      }
      let coverTitleOrphan = false;
      const h1 = slide.querySelector("h1");
      if (h1 && h1.firstChild?.nodeType === Node.TEXT_NODE) {
        const text = h1.firstChild.textContent || "";
        const lines = [];
        for (let index = 0; index < text.length; index += 1) {
          if (/\s/.test(text[index])) continue;
          const range = document.createRange();
          range.setStart(h1.firstChild, index);
          range.setEnd(h1.firstChild, index + 1);
          const rect = range.getBoundingClientRect();
          let line = lines.find(item => Math.abs(item.top - rect.top) < 2);
          if (!line) {
            line = { top: rect.top, left: rect.left, right: rect.right, count: 0 };
            lines.push(line);
          }
          line.left = Math.min(line.left, rect.left);
          line.right = Math.max(line.right, rect.right);
          line.count += 1;
        }
        if (lines.length > 1) {
          lines.sort((a, b) => a.top - b.top);
          const previous = lines.at(-2);
          const last = lines.at(-1);
          coverTitleOrphan = last.count <= 2 || (last.right - last.left) < (previous.right - previous.left) * 0.25;
        }
      }
      const fontFailures = [];
      const checks = [
        ["h1", 66.6],
        ["h2", 46.6],
        ["h3", 32],
        ["p:not(.note):not(.source-main):not(.source-meta):not(.stat-note):not(.step p),li,td", 21.3]
      ];
      for (const [selector, minimum] of checks) {
        for (const element of slide.querySelectorAll(selector)) {
          if (element.closest(".sources-list") || element.classList.contains("slide-source")) continue;
          const size = Number.parseFloat(getComputedStyle(element).fontSize);
          if (Number.isFinite(size) && size + 0.1 < minimum) fontFailures.push(`${selector}:${size}px`);
        }
      }
      return { overflow, titleWrap, coverTitleOrphan, fontFailures, width: slideRect.width, height: slideRect.height };
    });
    const imagePath = path.join(renderDir, `slide-${String(index + 1).padStart(2, "0")}.png`);
    await page.locator(".slide.active").screenshot({ path: imagePath });
    imagePaths.push(imagePath);
    slides.push({ number: index + 1, image: imagePath, ...qa });
  }

  const contactSheet = path.join(renderDir, "contact-sheet.png");
  await makeContactSheet(browser, imagePaths, contactSheet);

  const mergedPdf = await PDFDocument.create();
  const individualPdfBytes = [];
  for (let index = 0; index < slideCount; index += 1) {
    // Print every slide from a fresh document with only the target slide in the
    // body. Hiding non-target slides alone can leave a blank first print page
    // when a layout class changes the selected slide's flow or positioning.
    const printPage = await browser.newPage({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: 1 });
    await printPage.goto(pathToFileURL(htmlPath).href, { waitUntil: "networkidle" });
    await printPage.evaluate(() => document.fonts.ready);
    await printPage.emulateMedia({ media: "print" });
    const selected = await printPage.evaluate(target => {
      const slide = document.querySelector(`.slide[data-slide="${target}"]`);
      if (!slide) return false;
      const clone = slide.cloneNode(true);
      clone.classList.add("active");
      clone.style.setProperty("display", "block", "important");
      clone.style.setProperty("position", "relative", "important");
      clone.style.setProperty("inset", "auto", "important");
      clone.style.setProperty("break-after", "auto", "important");
      clone.style.setProperty("page-break-after", "auto", "important");
      const viewport = document.createElement("main");
      viewport.className = "viewport";
      viewport.appendChild(clone);
      document.body.replaceChildren(viewport);
      return true;
    }, index + 1);
    if (!selected) throw new Error(`Slide ${index + 1} not found while printing`);
    const onePageBuffer = await printPage.pdf({ width: "1600px", height: "900px", printBackground: true, preferCSSPageSize: false, pageRanges: "1" });
    individualPdfBytes.push(onePageBuffer.length);
    await printPage.close();
    const onePagePdf = await PDFDocument.load(onePageBuffer);
    if (onePagePdf.getPageCount() !== 1) throw new Error(`Slide ${index + 1} produced ${onePagePdf.getPageCount()} PDF pages`);
    const [copiedPage] = await mergedPdf.copyPages(onePagePdf, [0]);
    mergedPdf.addPage(copiedPage);
  }
  const pdfBuffer = Buffer.from(await mergedPdf.save());
  fs.writeFileSync(pdfPath, pdfBuffer);
  const detectedPdfPages = mergedPdf.getPageCount();
  await browser.close();

  const failures = [];
  if (!fontCheck.loaded || fontCheck.status !== "loaded" || !fontCheck.family.includes("Slide Noto Sans JP")) failures.push({ code: "FONT_LOAD", message: "Bundled Slide Noto Sans JP did not load", details: fontCheck });
  if (!navigationPass) failures.push({ code: "NAVIGATION", message: "Navigation did not clamp or update correctly" });
  if (consoleErrors.length) failures.push({ code: "CONSOLE", message: "Browser console errors occurred", details: consoleErrors });
  for (const slide of slides) {
    if (slide.overflow.length) failures.push({ code: "OVERFLOW", slide: slide.number, details: slide.overflow });
    if (slide.titleWrap) failures.push({ code: "TITLE_WRAP", slide: slide.number });
    if (slide.coverTitleOrphan) failures.push({ code: "COVER_TITLE_ORPHAN", slide: slide.number });
    if (slide.fontFailures.length) failures.push({ code: "FONT_SIZE", slide: slide.number, details: slide.fontFailures });
    if (Math.round(slide.width) !== 1600 || Math.round(slide.height) !== 900) failures.push({ code: "SLIDE_SIZE", slide: slide.number, details: [slide.width, slide.height] });
  }
  if (detectedPdfPages && detectedPdfPages !== slideCount) failures.push({ code: "PDF_PAGE_COUNT", message: `${detectedPdfPages} PDF pages for ${slideCount} slides` });
  individualPdfBytes.forEach((byteCount, index) => {
    if (byteCount < 4000) failures.push({ code: "PDF_SUSPECT_BLANK", slide: index + 1, message: `Individual PDF page is only ${byteCount} bytes` });
  });

  const report = {
    status: failures.length ? "FAIL" : "PASS",
    browser: browserPath || "playwright-managed",
    workflow,
    html: htmlPath,
    pdf: pdfPath,
    slide_count: slideCount,
    detected_pdf_pages: detectedPdfPages || null,
    individual_pdf_bytes: individualPdfBytes,
    navigation,
    navigation_pass: navigationPass,
    font: fontCheck,
    contact_sheet: contactSheet,
    slides,
    failures,
  };
  fs.writeFileSync(reportPath, JSON.stringify(report, null, 2), "utf8");
  process.stdout.write(JSON.stringify({ status: report.status, slide_count: slideCount, pdf_pages: report.detected_pdf_pages, renders: renderDir, contact_sheet: contactSheet, pdf: pdfPath, report: reportPath, failure_count: failures.length }));
  process.exitCode = failures.length ? 2 : 0;
}

main().catch(error => {
  process.stderr.write(`${error.stack || error.message}\n`);
  process.exitCode = 2;
});
