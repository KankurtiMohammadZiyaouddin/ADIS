# ADIS Forensic Suite — React App

A single, maintainable React application converted from 13 standalone Stitch-generated
HTML prototypes (login, dashboard, cases, case investigation, evidence management,
image/video/audio forensics, metadata & provenance, cross-modal analysis, investigation
timeline, reports, audit logs).

## Stack
- Vite + React
- React Router (`react-router-dom`) for client-side routing
- Tailwind CSS, configured from the shared `DESIGN.md` design tokens (colors, type scale,
  spacing, radius) that were consistent across all 13 original prototypes
- Chart.js for the dashboard risk-breakdown doughnut chart

## Structure
```
src/
  components/
    Layout.jsx       # Sidebar + Topbar shell, renders the active page via <Outlet/>
    Sidebar.jsx       # Route-aware nav (active link highlighting via NavLink)
    Topbar.jsx        # Page title + current-case badge + icon actions
    navConfig.js      # Single source of truth for sidebar links
    RiskChart.jsx     # Chart.js doughnut, replaces the old inline <script>/getElementById
  pages/
    DashboardPage.jsx, CasesPage.jsx, CaseInvestigationPage.jsx, EvidencePage.jsx,
    ImageForensicsPage.jsx, VideoForensicsPage.jsx, AudioForensicsPage.jsx,
    MetadataProvenancePage.jsx, CrossModalAnalysisPage.jsx, TimelinePage.jsx,
    ReportsPage.jsx, AuditLogsPage.jsx, LoginPage.jsx
  App.jsx             # Route table
```

## Getting started
```bash
npm install
npm run dev
```

## What changed vs. the 13 static prototypes
- One shared `Layout`/`Sidebar`/`Topbar` instead of each page carrying its own copy —
  the active nav item now highlights based on the actual route, not a hardcoded class.
- One `tailwind.config.js` sourced from the design tokens instead of an inline
  `tailwind.config` `<script>` block duplicated in every HTML file.
- Clicking a case row (on the Dashboard or Cases page) now actually navigates to
  `/cases/:caseId` via React Router instead of `href="#"`.
- The login form is a real controlled component that navigates to `/` on submit.
- The dashboard's Chart.js doughnut is a proper React component (`RiskChart`) with
  correct mount/unmount lifecycle, instead of a `<script>` tag calling
  `document.getElementById`.

## Known gaps / next steps
- The original design's sidebar referenced a few modules with no corresponding
  screen in the exported prototypes — **Comparison**, **Investigation Graph**,
  **Model Registry**, and **Settings**. These were intentionally left out of the
  nav rather than linking to dead routes; add a page + route + `navConfig.js`
  entry for each when you build them.
- All page content is currently static markup (no live data/API calls) — same as
  the original prototypes, just now componentized.
- No auth guard yet — `/login` and the app routes are both reachable directly.
