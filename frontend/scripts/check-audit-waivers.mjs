#!/usr/bin/env node
// npm audit has no per-advisory ignore flag (unlike pip-audit's --ignore-vuln),
// so this mirrors that behavior: run the audit, allow only advisories whose
// npm advisory ID is in WAIVERS, fail on anything else. Each waiver requires
// a JIRA key here, reviewed each sprint alongside the pip-audit ledger.
import { execSync } from "node:child_process"

const WAIVERS = {
  // brace-expansion DoS (GHSA-mh99-v99m-4gvg), reached via eslint-config-next's
  // eslint-plugin-import/-jsx-a11y/-react -> minimatch@3.1.5, and eslint's own
  // @eslint/config-array -> same old minimatch. Fix requires ESLint 10, which
  // breaks eslint-plugin-react (react/display-name calls the removed
  // context.getFilename()) - none of eslint-plugin-react/-import/-jsx-a11y
  // support ESLint 10 yet (confirmed against their latest published versions).
  // RF-98: re-check each sprint, drop once those plugins ship ESLint 10 support.
  1124334: "RF-98",
}

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

const unwaived = [...advisories.values()].filter((a) => !(a.source in WAIVERS))

if (unwaived.length > 0) {
  console.error("Unwaived high/critical npm audit findings:")
  for (const a of unwaived) {
    console.error(`  - ${a.name} (${a.source}): ${a.title} - ${a.url}`)
  }
  process.exit(1)
}

if (advisories.size > 0) {
  console.log(
    `npm audit: ${advisories.size} finding(s), all waived: ${[...advisories.values()].map((a) => `${a.name} (${WAIVERS[a.source]})`).join(", ")}`
  )
} else {
  console.log("npm audit: clean, no high/critical findings.")
}
