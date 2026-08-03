#!/usr/bin/env node
// npm audit has no per-advisory ignore flag (unlike pip-audit's --ignore-vuln),
// so this mirrors that behavior: run the audit, allow only advisories whose
// GHSA ID is in WAIVERS, fail on anything else. Each waiver requires a JIRA
// key here, reviewed each sprint alongside the pip-audit ledger.
//
// Keyed on GHSA, not npm's numeric advisory id: npm reissues the numeric id
// when it republishes an advisory with a wider affected range, which silently
// un-waives the finding and reds every open PR. brace-expansion did exactly
// that (1124334 -> 1130588) between 2026-07-29 and 2026-08-01. The GHSA is stable.
import { execSync } from "node:child_process"

// Empty is the goal state. RF-98's brace-expansion waiver
// (GHSA-mh99-v99m-4gvg) was dropped 2026-08-04: upstream published patches on
// both affected lines (1.1.18 and 5.0.9), so package.json pins them via
// `overrides` instead. No ESLint 10 bump needed after all.
const WAIVERS = {}

// npm gives the advisory URL, not a bare GHSA id.
const ghsaOf = (a) => a.url?.split("/").pop() ?? String(a.source)

let stdout
try {
  stdout = execSync("npm audit --audit-level=high --json", {
    encoding: "utf8",
  })
} catch (err) {
  stdout = err.stdout
}

const report = JSON.parse(stdout)
const advisories = new Map()
for (const vuln of Object.values(report.vulnerabilities ?? {})) {
  for (const via of vuln.via) {
    if (typeof via === "object" && via.source !== undefined) {
      advisories.set(via.source, via)
    }
  }
}

const unwaived = [...advisories.values()].filter((a) => !(ghsaOf(a) in WAIVERS))

if (unwaived.length > 0) {
  console.error("Unwaived high/critical npm audit findings:")
  for (const a of unwaived) {
    console.error(`  - ${a.name} (${ghsaOf(a)}): ${a.title} - ${a.url}`)
  }
  process.exit(1)
}

if (advisories.size > 0) {
  console.log(
    `npm audit: ${advisories.size} finding(s), all waived: ${[...advisories.values()].map((a) => `${a.name} (${WAIVERS[ghsaOf(a)]})`).join(", ")}`
  )
} else {
  console.log("npm audit: clean, no high/critical findings.")
}
