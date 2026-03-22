import fs from "fs";
import path from "path";
import {
  PDFDocument,
  PDFTextField,
  PDFCheckBox,
  PDFRadioGroup,
  StandardFonts,
  rgb,
} from "pdf-lib";

const [, , templatePath, outputPath, dataPath, ...flags] = process.argv;
const flatten = flags.includes("--flatten");
const debugGrid = flags.includes("--debug-grid");

const templateBytes = fs.readFileSync(templatePath);
const pdfDoc = await PDFDocument.load(templateBytes);
const form = pdfDoc.getForm();
const data = JSON.parse(fs.readFileSync(dataPath, "utf-8"));
const font = await pdfDoc.embedFont(StandardFonts.Helvetica);

const scriptDir = path.dirname(new URL(import.meta.url).pathname);
const staticMarksPath = path.join(scriptDir, "pdf_static_marks.json");

const placeholderValues = new Set(["Sample", "Sample Text", "Sample text", "Text"]);

function normalize(value) {
  return String(value ?? "")
    .toLowerCase()
    .replace(/[().,/:+\-]/g, " ")
    .replace(/&/g, " and ")
    .replace(/\bpsi(?:onic)?\b/g, "psionic")
    .replace(/\bext\b/g, "ext")
    .replace(/\biq\b/g, "i q")
    .replace(/\bme\b/g, "m e")
    .replace(/\bma\b/g, "m a")
    .replace(/\bpe\b/g, "p e")
    .replace(/\bpp\b/g, "p p")
    .replace(/\bps\b/g, "p s")
    .replace(/\bpb\b/g, "p b")
    .replace(/\s+/g, " ")
    .trim();
}

function fieldNameCandidates(name) {
  const n = normalize(name);
  const out = new Set([n]);

  const aliases = {
    "sixth sense": ["6th sense"],
    "telepathic transmission": ["telepathic transmit", "transmission"],
    "extraordinary i q": ["extraordinary iq"],
    "extraordinary m e": ["extraordinary me"],
    "extraordinary m a": ["extraordinary ma"],
    "extraordinary p e": ["extraordinary pe"],
    "extraordinary p p": ["extraordinary pp"],
    "extraordinary p s": ["extraordinary ps"],
    "extraordinary p b": ["extraordinary pb"],
    "ext ectoplasmic hands": ["extended ectoplasmic hands", "ectoplasmic hands"],
    "techno mind": ["technomind"],
    "animal aura": ["aura"],
    "animal control": ["control"],
    "animal speech": ["speech"],
    "create force field": ["force field"],
    "create darkness": ["darkness"],
    "electrical field": ["electric field"],
    "mechanical manipulation": ["mechanical"],
    "shadow meld": ["shadow"]
  };

  if (aliases[n]) {
    for (const alias of aliases[n]) {
      out.add(normalize(alias));
    }
  }

  return [...out];
}

function extractSelectedLabels(payload) {
  const direct = String(payload["__SELECTED_STATIC_LABELS__"] ?? "")
    .split(/\r?\n/)
    .map((x) => x.trim())
    .filter(Boolean);

  if (direct.length) {
    return [...new Set(direct)];
  }

  const labels = [];
  const directPrefixes = [
    "Psionic.Spell.Name.",
    "Abilities.Animal.Other.",
    "Weapon.Proficiency.",
  ];

  for (const [key, value] of Object.entries(payload)) {
    const text = String(value ?? "").trim();
    if (!text) continue;

    if (directPrefixes.some((prefix) => key.startsWith(prefix))) {
      labels.push(text);
      continue;
    }

    if (key.startsWith("Build.Notes.") || key.startsWith("Ch.Notes.")) {
      if (text.startsWith("- ")) {
        labels.push(
          text.replace(/^-+\s*/, "").replace(/\s*\(\d+\s*Bio-E\)\s*$/i, "").trim()
        );
      }
    }
  }

  return [...new Set(labels.filter(Boolean))];
}

function findButtonFieldMap(fields) {
  const map = new Map();

  for (const field of fields) {
    if (field instanceof PDFCheckBox || field instanceof PDFRadioGroup) {
      map.set(normalize(field.getName()), field);
    }
  }

  return map;
}

function trySelectButtonField(field) {
  try {
    if (field instanceof PDFCheckBox) {
      field.check();
      return true;
    }

    if (field instanceof PDFRadioGroup) {
      const options = field.getOptions();
      if (Array.isArray(options) && options.length > 0) {
        field.select(options[0]);
        return true;
      }
    }
  } catch (e) {
    return false;
  }

  return false;
}

function markMatchingButtonFields(payload, fields) {
  const buttonMap = findButtonFieldMap(fields);
  const selectedLabels = extractSelectedLabels(payload);

  for (const label of selectedLabels) {
    const candidates = fieldNameCandidates(label);

    for (const candidate of candidates) {
      for (const [fieldName, field] of buttonMap.entries()) {
        if (
          fieldName === candidate ||
          fieldName.includes(candidate) ||
          candidate.includes(fieldName)
        ) {
          trySelectButtonField(field);
        }
      }
    }
  }
}

function loadStaticMarks() {
  try {
    if (!fs.existsSync(staticMarksPath)) {
      return { circle: {}, highlight: {} };
    }
    const raw = JSON.parse(fs.readFileSync(staticMarksPath, "utf-8"));
    return {
      circle: raw.circle ?? {},
      highlight: raw.highlight ?? {},
    };
  } catch (e) {
    return { circle: {}, highlight: {} };
  }
}

function drawCircle(page, entry) {
  const x = Number(entry.x ?? 0);
  const y = Number(entry.y ?? 0);
  const size = Number(entry.size ?? 16);
  const lineWidth = Number(entry.lineWidth ?? 1.8);

  page.drawEllipse({
    x,
    y,
    xScale: size / 2,
    yScale: size / 2,
    borderColor: rgb(0.85, 0.1, 0.1),
    borderWidth: lineWidth,
    color: undefined,
    opacity: 1,
    borderOpacity: 1,
  });
}

function drawHighlight(page, entry) {
  const x = Number(entry.x ?? 0);
  const y = Number(entry.y ?? 0);
  const width = Number(entry.width ?? 120);
  const height = Number(entry.height ?? 14);
  const opacity = Number(entry.opacity ?? 0.18);

  page.drawRectangle({
    x,
    y,
    width,
    height,
    color: rgb(1, 0.95, 0.2),
    opacity,
    borderWidth: 0,
  });
}

function applyStaticMarks(payload, pdfDoc) {
  const selectedLabels = extractSelectedLabels(payload);
  const marks = loadStaticMarks();
  const seen = new Set();

  for (const label of selectedLabels) {
    const candidates = fieldNameCandidates(label);

    for (const candidate of candidates) {
      if (seen.has(candidate)) continue;
      seen.add(candidate);

      const circleEntries = marks.circle[candidate] ?? [];
      const highlightEntries = marks.highlight[candidate] ?? [];

      for (const entry of circleEntries) {
        const pageIndex = Number(entry.page ?? 1) - 1;
        if (pageIndex >= 0 && pageIndex < pdfDoc.getPageCount()) {
          drawCircle(pdfDoc.getPage(pageIndex), entry);
        }
      }

      for (const entry of highlightEntries) {
        const pageIndex = Number(entry.page ?? 1) - 1;
        if (pageIndex >= 0 && pageIndex < pdfDoc.getPageCount()) {
          drawHighlight(pdfDoc.getPage(pageIndex), entry);
        }
      }
    }
  }
}

function drawDebugGrid(pdfDoc) {
  for (let i = 0; i < pdfDoc.getPageCount(); i++) {
    const page = pdfDoc.getPage(i);
    const { width, height } = page.getSize();

    for (let x = 0; x <= width; x += 50) {
      page.drawLine({
        start: { x, y: 0 },
        end: { x, y: height },
        thickness: x % 100 === 0 ? 0.8 : 0.3,
        color: rgb(0.7, 0.7, 0.7),
        opacity: 0.35,
      });

      page.drawText(String(x), {
        x: x + 2,
        y: 2,
        size: 6,
        font,
        color: rgb(0.35, 0.35, 0.35),
        opacity: 0.8,
      });
    }

    for (let y = 0; y <= height; y += 50) {
      page.drawLine({
        start: { x: 0, y },
        end: { x: width, y },
        thickness: y % 100 === 0 ? 0.8 : 0.3,
        color: rgb(0.7, 0.7, 0.7),
        opacity: 0.35,
      });

      page.drawText(String(y), {
        x: 2,
        y: y + 2,
        size: 6,
        font,
        color: rgb(0.35, 0.35, 0.35),
        opacity: 0.8,
      });
    }

    page.drawText(`DEBUG GRID - PAGE ${i + 1}`, {
      x: 20,
      y: height - 20,
      size: 10,
      font,
      color: rgb(0.8, 0.1, 0.1),
    });
  }
}

const fields = form.getFields();

for (const field of fields) {
  try {
    if (field instanceof PDFTextField && field.isRichFormatted()) {
      field.disableRichFormatting();
    }
  } catch (e) {
    // ignore
  }
}

for (const field of fields) {
  try {
    if (field instanceof PDFTextField) {
      const name = field.getName();

      if (!name.startsWith("__") && Object.prototype.hasOwnProperty.call(data, name)) {
        field.setText(String(data[name] ?? ""));
      } else {
        try {
          const current = field.getText();
          if (placeholderValues.has(String(current ?? "").trim())) {
            field.setText("");
          }
        } catch (e) {
          // ignore
        }
      }

      try {
        field.setFontSize(12);
      } catch (e) {
        // ignore
      }
    }
  } catch (e) {
    // ignore
  }
}

markMatchingButtonFields(data, fields);

try {
  form.updateFieldAppearances(font);
} catch (e) {
  // ignore
}

if (flatten) {
  form.flatten();
}

applyStaticMarks(data, pdfDoc);

if (debugGrid) {
  drawDebugGrid(pdfDoc);
}

const pdfBytes = await pdfDoc.save();
fs.writeFileSync(outputPath, pdfBytes);