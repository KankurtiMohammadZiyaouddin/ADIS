/**
 * ADIS PDF Report Generator
 * Uses jsPDF to produce a professional forensic analysis report.
 * Supports: Audio, Video, Cross-Modal (combined) report types.
 */
import { jsPDF } from 'jspdf';

// ── Colours (match ADIS design system as close as possible in RGB) ──────────
const C = {
  bg:           [13,  17,  23],   // #0D1117 near-black background
  surface:      [26,  30,  37],   // #1A1E25 card surface
  primary:      [0,   87,  255],  // #0057FF
  error:        [186, 26,  26],   // #BA1A1A
  real:         [0,   100, 40],   // green
  outline:      [68,  71,  78],   // grey
  textMain:     [220, 225, 230],  // near-white body
  textMuted:    [140, 145, 150],  // muted grey
  textLabel:    [170, 175, 180],
  white:        [255, 255, 255],
  amber:        [215, 140, 0],
};

// ── Helpers ─────────────────────────────────────────────────────────────────
const rgb = (arr) => ({ r: arr[0], g: arr[1], b: arr[2] });

function setFont(doc, size, style = 'normal', color = C.textMain) {
  doc.setFontSize(size);
  doc.setFont('helvetica', style);
  doc.setTextColor(...color);
}

function hline(doc, y, color = C.outline, w = 0.3) {
  doc.setDrawColor(...color);
  doc.setLineWidth(w);
  doc.line(14, y, 196, y);
}

function rect(doc, x, y, w, h, fillColor) {
  doc.setFillColor(...fillColor);
  doc.rect(x, y, w, h, 'F');
}

function verdictColor(verdict) {
  if (verdict === 'FAKE') return C.error;
  if (verdict === 'REAL') return C.real;
  return C.amber;
}

function drawBar(doc, x, y, pct, color, barW = 80, barH = 3) {
  // Background
  doc.setFillColor(...C.outline);
  doc.roundedRect(x, y, barW, barH, 1, 1, 'F');
  // Fill
  doc.setFillColor(...color);
  const fill = Math.max(2, (pct / 100) * barW);
  doc.roundedRect(x, y, fill, barH, 1, 1, 'F');
}

function pageHeader(doc, pageNum, totalPages) {
  // Dark header bar
  rect(doc, 0, 0, 210, 16, C.surface);
  setFont(doc, 7, 'bold', C.primary);
  doc.text('ADIS — ADVANCED DIGITAL INVESTIGATION SUITE', 14, 10);
  setFont(doc, 7, 'normal', C.textMuted);
  doc.text(`FORENSIC ANALYSIS REPORT  |  CONFIDENTIAL`, 105, 10, { align: 'center' });
  doc.text(`Page ${pageNum} of ${totalPages}`, 196, 10, { align: 'right' });
}

function pageFooter(doc, genDate) {
  hline(doc, 282, C.outline, 0.2);
  setFont(doc, 6.5, 'normal', C.textMuted);
  doc.text(`Generated: ${genDate}`, 14, 287);
  doc.text('This report is produced by ADIS Forensic Suite. For law-enforcement use only.', 105, 287, { align: 'center' });
  doc.text('ADIS v2.0', 196, 287, { align: 'right' });
}

// ── Section title helper ────────────────────────────────────────────────────
function sectionTitle(doc, text, y) {
  rect(doc, 14, y, 182, 7, [30, 35, 45]);
  setFont(doc, 8, 'bold', C.primary);
  doc.text(text.toUpperCase(), 17, y + 5);
  return y + 11;
}

// ── KV row helper ───────────────────────────────────────────────────────────
function kv(doc, label, value, x, y, valueColor = C.textMain) {
  setFont(doc, 8, 'normal', C.textMuted);
  doc.text(label + ':', x, y);
  setFont(doc, 8, 'bold', valueColor);
  doc.text(String(value), x + 55, y);
  return y + 6;
}

// ── Verdict badge helper ────────────────────────────────────────────────────
function verdictBadge(doc, verdict, x, y) {
  const color = verdictColor(verdict);
  const w = verdict.length * 2.2 + 6;
  doc.setFillColor(color[0], color[1], color[2], 0.2);
  doc.setDrawColor(...color);
  doc.setLineWidth(0.4);
  doc.roundedRect(x, y - 4.5, w, 6, 1.5, 1.5, 'FD');
  setFont(doc, 7.5, 'bold', color);
  doc.text(verdict, x + w / 2, y, { align: 'center' });
}

// ═══════════════════════════════════════════════════════════════════════════
// PUBLIC API
// ═══════════════════════════════════════════════════════════════════════════

/**
 * Generate and download a PDF forensic report for a single analysis record.
 * @param {Object} record  - from analysisStore (type, filename, verdict, confidence, timestamp, model, sha256, simulated)
 * @param {string} [caseId]
 */
export function generateSingleReport(record, caseId = 'N/A') {
  const doc = new jsPDF({ unit: 'mm', format: 'a4', compress: true });
  const genDate = new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
  const reportId = `FR-${Date.now().toString().slice(-6)}`;
  const totalPages = 1;

  // ── Cover background ──────────────────────────────────────────────────
  rect(doc, 0, 0, 210, 297, C.bg);
  pageHeader(doc, 1, totalPages);

  // ── Title block ───────────────────────────────────────────────────────
  let y = 28;
  setFont(doc, 18, 'bold', C.white);
  doc.text('FORENSIC ANALYSIS REPORT', 105, y, { align: 'center' });
  y += 7;
  setFont(doc, 9, 'normal', C.textMuted);
  const typeLabel = record.type === 'audio' ? 'Audio Deepfake Detection'
                  : record.type === 'video' ? 'Video Deepfake Detection'
                  : 'Image Forensic Analysis';
  doc.text(typeLabel, 105, y, { align: 'center' });
  y += 3;
  hline(doc, y, C.primary, 0.5);
  y += 8;

  // ── Report metadata ────────────────────────────────────────────────────
  y = sectionTitle(doc, '1. Report Metadata', y);
  y = kv(doc, 'Report ID',       reportId,     14, y);
  y = kv(doc, 'Case Reference',  caseId,        14, y);
  y = kv(doc, 'Generated',       genDate,       14, y);
  y = kv(doc, 'Analyst',         'ADIS System', 14, y);
  y = kv(doc, 'Classification',  'CONFIDENTIAL',14, y, C.error);
  y += 4;

  // ── Evidence metadata ──────────────────────────────────────────────────
  y = sectionTitle(doc, '2. Evidence File Metadata', y);
  y = kv(doc, 'Filename',    record.filename  || 'Unknown', 14, y);
  y = kv(doc, 'File Type',   record.type      || 'Unknown', 14, y);
  y = kv(doc, 'SHA-256',     record.sha256    || 'Not recorded', 14, y);
  y = kv(doc, 'Analyzed At', record.timestamp ? new Date(record.timestamp).toISOString().replace('T',' ').substring(0,19)+' UTC' : 'Unknown', 14, y);
  y += 4;

  // ── Analysis results ───────────────────────────────────────────────────
  y = sectionTitle(doc, '3. AI Model Analysis Results', y);
  y = kv(doc, 'AI Model Used', record.model || 'ADIS Forensic Model', 14, y);
  y = kv(doc, 'Result Source', record.simulated ? 'SIMULATION (no forensic value)' : 'Real AI Model Inference', 14, y,
    record.simulated ? C.amber : C.real);
  y += 4;

  // Verdict display
  setFont(doc, 10, 'bold', C.textMuted);
  doc.text('Verdict:', 14, y);
  verdictBadge(doc, record.verdict, 45, y);
  y += 10;

  // Confidence bar
  setFont(doc, 8, 'normal', C.textMuted);
  doc.text('Confidence Score:', 14, y);
  setFont(doc, 8, 'bold', verdictColor(record.verdict));
  doc.text(`${record.confidence}%`, 65, y);
  y += 5;
  drawBar(doc, 14, y, record.confidence, verdictColor(record.verdict), 130, 5);
  y += 10;

  if (record.simulated) {
    rect(doc, 14, y, 182, 12, [60, 40, 0]);
    setFont(doc, 7.5, 'bold', C.amber);
    doc.text('⚠  SIMULATION MODE — These results were generated randomly because the backend was offline.', 17, y + 5);
    doc.text('    They have NO forensic value. Re-run the analysis with the backend running.', 17, y + 10);
    y += 17;
  }
  y += 4;

  // ── Interpretation ────────────────────────────────────────────────────
  y = sectionTitle(doc, '4. Forensic Interpretation', y);
  const interp = record.verdict === 'FAKE'
    ? `The AI model classified this ${record.type} file as SYNTHETIC / MANIPULATED with ${record.confidence}% confidence. The evidence exhibits statistical patterns inconsistent with authentic ${record.type} capture. Recommend treating this file as potentially fabricated and conducting further investigation.`
    : record.verdict === 'REAL'
    ? `The AI model classified this ${record.type} file as AUTHENTIC with ${record.confidence}% confidence. No significant synthetic artifacts were detected. The file may be used as evidence, though further corroboration is recommended.`
    : `The AI model returned an INCONCLUSIVE result. Manual review by a qualified forensic examiner is required before this evidence can be used.`;

  setFont(doc, 8.5, 'normal', C.textMain);
  const lines = doc.splitTextToSize(interp, 178);
  doc.text(lines, 14, y);
  y += lines.length * 5 + 6;

  // ── Disclaimer ────────────────────────────────────────────────────────
  y = sectionTitle(doc, '5. Legal Disclaimer', y);
  setFont(doc, 7.5, 'normal', C.textMuted);
  const disc = 'This report is generated automatically by ADIS (Advanced Digital Investigation Suite). AI-based forensic analysis is a probabilistic tool and should not be used as the sole basis for legal decisions. Results must be reviewed and validated by a qualified human forensic examiner before submission to any legal proceeding. ADIS and its contributors accept no liability for decisions made based solely on this report.';
  const discLines = doc.splitTextToSize(disc, 178);
  doc.text(discLines, 14, y);

  pageFooter(doc, genDate);

  doc.save(`ADIS_Report_${record.type}_${reportId}.pdf`);
}

/**
 * Generate and download a combined cross-modal PDF report.
 * @param {Object|null} audioRec  - audio analysis record from store
 * @param {Object|null} videoRec  - video analysis record from store
 * @param {Object} crossResult    - { fakeProbability, combined, conflicting, sources }
 * @param {string} [caseId]
 */
export function generateCrossModalReport(audioRec, videoRec, crossResult, caseId = 'N/A') {
  const doc = new jsPDF({ unit: 'mm', format: 'a4', compress: true });
  const genDate = new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
  const reportId = `CMFR-${Date.now().toString().slice(-6)}`;
  const totalPages = 1;

  rect(doc, 0, 0, 210, 297, C.bg);
  pageHeader(doc, 1, totalPages);

  let y = 28;
  setFont(doc, 18, 'bold', C.white);
  doc.text('CROSS-MODAL FORENSIC REPORT', 105, y, { align: 'center' });
  y += 7;
  setFont(doc, 9, 'normal', C.textMuted);
  doc.text('Combined Audio + Video Deepfake Correlation', 105, y, { align: 'center' });
  y += 3;
  hline(doc, y, C.primary, 0.5);
  y += 8;

  // Report metadata
  y = sectionTitle(doc, '1. Report Metadata', y);
  y = kv(doc, 'Report ID',       reportId,      14, y);
  y = kv(doc, 'Case Reference',  caseId,         14, y);
  y = kv(doc, 'Generated',       genDate,        14, y);
  y = kv(doc, 'Classification',  'CONFIDENTIAL', 14, y, C.error);
  y += 4;

  // Combined verdict
  y = sectionTitle(doc, '2. Combined Cross-Modal Verdict', y);
  setFont(doc, 10, 'bold', C.textMuted);
  doc.text('Combined Verdict:', 14, y);
  verdictBadge(doc, crossResult.combined, 65, y);
  y += 10;
  setFont(doc, 8, 'normal', C.textMuted);
  doc.text('AI Manipulation Probability:', 14, y);
  setFont(doc, 8, 'bold', verdictColor(crossResult.combined));
  doc.text(`${crossResult.fakeProbability.toFixed(1)}%`, 75, y);
  y += 5;
  drawBar(doc, 14, y, crossResult.fakeProbability, verdictColor(crossResult.combined), 130, 5);
  y += 12;

  if (crossResult.conflicting) {
    rect(doc, 14, y, 182, 10, [60, 50, 0]);
    setFont(doc, 7.5, 'bold', C.amber);
    doc.text('⚠  MODALITY CONFLICT: Audio and Video models returned opposite verdicts.', 17, y + 4);
    doc.text('    Manual forensic review is required before any legal determination.', 17, y + 9);
    y += 15;
  }
  y += 2;

  // Audio evidence
  y = sectionTitle(doc, '3. Audio Evidence', y);
  if (audioRec) {
    y = kv(doc, 'Filename',   audioRec.filename, 14, y);
    y = kv(doc, 'Verdict',    audioRec.verdict,  14, y, verdictColor(audioRec.verdict));
    y = kv(doc, 'Confidence', `${audioRec.confidence}%`, 14, y);
    y = kv(doc, 'Model',      audioRec.model || 'Deepfake-YamNet', 14, y);
    y = kv(doc, 'SHA-256',    audioRec.sha256 || 'Not recorded', 14, y);
    if (audioRec.simulated) { setFont(doc, 7.5, 'bold', C.amber); doc.text('⚠ Simulated result — no forensic value', 14, y); y += 6; }
  } else {
    setFont(doc, 8, 'italic', C.textMuted);
    doc.text('No audio evidence was selected for this report.', 14, y); y += 6;
  }
  y += 4;

  // Video evidence
  y = sectionTitle(doc, '4. Video Evidence', y);
  if (videoRec) {
    y = kv(doc, 'Filename',   videoRec.filename, 14, y);
    y = kv(doc, 'Verdict',    videoRec.verdict,  14, y, verdictColor(videoRec.verdict));
    y = kv(doc, 'Confidence', `${videoRec.confidence}%`, 14, y);
    y = kv(doc, 'Model',      videoRec.model || 'EfficientNet-B0', 14, y);
    y = kv(doc, 'SHA-256',    videoRec.sha256 || 'Not recorded', 14, y);
    if (videoRec.simulated) { setFont(doc, 7.5, 'bold', C.amber); doc.text('⚠ Simulated result — no forensic value', 14, y); y += 6; }
  } else {
    setFont(doc, 8, 'italic', C.textMuted);
    doc.text('No video evidence was selected for this report.', 14, y); y += 6;
  }
  y += 4;

  // Interpretation
  y = sectionTitle(doc, '5. Forensic Interpretation', y);
  const interp = crossResult.combined === 'FAKE'
    ? `Cross-modal correlation of the selected audio and video evidence yields a combined synthetic probability of ${crossResult.fakeProbability.toFixed(1)}%, exceeding the FAKE classification threshold of 60%. The weighted analysis of both modalities strongly suggests the submitted media has been artificially generated or manipulated. This evidence should be flagged as potentially fabricated pending further examination.`
    : crossResult.combined === 'REAL'
    ? `Cross-modal correlation yields a combined synthetic probability of ${crossResult.fakeProbability.toFixed(1)}%, below the REAL classification threshold of 35%. Both modalities indicate the media is consistent with authentic capture. However, AI-based tools are probabilistic and human verification is recommended before legal use.`
    : `The cross-modal correlation yields an inconclusive result (${crossResult.fakeProbability.toFixed(1)}%). This falls between the FAKE (≥60%) and REAL (≤35%) thresholds. Manual review by a qualified forensic examiner is required.`;
  setFont(doc, 8.5, 'normal', C.textMain);
  const lines = doc.splitTextToSize(interp, 178);
  doc.text(lines, 14, y);
  y += lines.length * 5 + 6;

  // Disclaimer
  y = sectionTitle(doc, '6. Legal Disclaimer', y);
  setFont(doc, 7.5, 'normal', C.textMuted);
  const disc = 'This report is generated automatically by ADIS. Results are probabilistic and must be validated by a qualified forensic examiner before any legal use. ADIS accepts no liability for decisions made solely on the basis of this automated report.';
  doc.text(doc.splitTextToSize(disc, 178), 14, y);

  pageFooter(doc, genDate);
  doc.save(`ADIS_CrossModal_Report_${reportId}.pdf`);
}

/**
 * Generate a bulk summary PDF of all analysis history records.
 * @param {Array} history  - from getAnalysisHistory()
 */
export function generateBulkReport(history) {
  if (!history.length) return;
  const doc = new jsPDF({ unit: 'mm', format: 'a4', compress: true });
  const genDate = new Date().toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
  const reportId = `BULK-${Date.now().toString().slice(-6)}`;

  // Stats
  const fakeCount = history.filter((r) => r.verdict === 'FAKE').length;
  const realCount = history.filter((r) => r.verdict === 'REAL').length;

  rect(doc, 0, 0, 210, 297, C.bg);
  pageHeader(doc, 1, 1);

  let y = 28;
  setFont(doc, 18, 'bold', C.white);
  doc.text('BULK ANALYSIS SUMMARY REPORT', 105, y, { align: 'center' });
  y += 7;
  setFont(doc, 9, 'normal', C.textMuted);
  doc.text(`${history.length} analysis records — generated ${genDate}`, 105, y, { align: 'center' });
  y += 3;
  hline(doc, y, C.primary, 0.5);
  y += 8;

  // Summary stats
  y = sectionTitle(doc, 'Summary Statistics', y);
  y = kv(doc, 'Report ID',        reportId, 14, y);
  y = kv(doc, 'Total Analyses',   history.length, 14, y);
  y = kv(doc, 'Deepfakes (FAKE)', fakeCount, 14, y, C.error);
  y = kv(doc, 'Authentic (REAL)', realCount, 14, y, C.real);
  y = kv(doc, 'Inconclusive',     history.length - fakeCount - realCount, 14, y, C.amber);
  y += 6;

  // Table
  y = sectionTitle(doc, 'Analysis Records', y);

  // Table header
  const cols = [14, 40, 90, 125, 155, 175];
  const headers = ['#', 'Type', 'Filename', 'Verdict', 'Confidence', 'Time'];
  rect(doc, 14, y, 182, 7, [30, 35, 48]);
  setFont(doc, 7, 'bold', C.primary);
  headers.forEach((h, i) => doc.text(h, cols[i] + 1, y + 5));
  y += 9;

  history.slice(0, 40).forEach((rec, idx) => {
    if (idx % 2 === 0) rect(doc, 14, y - 1, 182, 6, [20, 24, 32]);
    setFont(doc, 7, 'normal', C.textMuted);
    doc.text(String(idx + 1), cols[0] + 1, y + 4);
    setFont(doc, 7, 'normal', C.textMain);
    doc.text((rec.type || '').toUpperCase(), cols[1] + 1, y + 4);
    const fn = (rec.filename || '').length > 28 ? rec.filename.slice(0, 25) + '…' : (rec.filename || '');
    doc.text(fn, cols[2] + 1, y + 4);
    setFont(doc, 7, 'bold', verdictColor(rec.verdict));
    doc.text(rec.verdict + (rec.simulated ? '*' : ''), cols[3] + 1, y + 4);
    setFont(doc, 7, 'normal', C.textMain);
    doc.text(`${rec.confidence}%`, cols[4] + 1, y + 4);
    setFont(doc, 6.5, 'normal', C.textMuted);
    const ts = rec.timestamp ? new Date(rec.timestamp).toISOString().substring(0, 16).replace('T', ' ') : '';
    doc.text(ts, cols[5] + 1, y + 4);
    y += 6;
    if (y > 270) { doc.addPage(); rect(doc, 0, 0, 210, 297, C.bg); pageHeader(doc, doc.getNumberOfPages(), doc.getNumberOfPages()); y = 25; }
  });

  if (history.length > 40) {
    setFont(doc, 7.5, 'italic', C.textMuted);
    doc.text(`… and ${history.length - 40} more records (truncated for readability)`, 14, y + 6);
  }

  pageFooter(doc, genDate);
  doc.save(`ADIS_Bulk_Report_${reportId}.pdf`);
}
