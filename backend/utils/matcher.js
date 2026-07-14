/* ================================================================
   AutoJobApply — Resume ↔ Job Matching Engine  (no LLM, rule-based)

   Given a user's profile (skills + resume text + experience) and a job
   (title + description), it produces:
     - fit_score   0–100
     - matched     skills the user has that the job mentions
     - missing     skills the job mentions that the user does NOT have

   Everything here is pure keyword / heuristic logic — free, no API keys.
================================================================ */

// A dictionary of skills we know how to detect. Each entry maps a canonical
// label to the substrings that count as a mention. Extend freely.
const SKILL_DICTIONARY = {
  JavaScript: ['javascript', 'js', 'es6'],
  TypeScript: ['typescript', 'ts'],
  Python: ['python'],
  Java: ['java'],
  'C++': ['c++', 'cpp'],
  'C#': ['c#', '.net', 'dotnet', 'asp.net'],
  Go: ['golang', 'go', 'go language'],
  Ruby: ['ruby', 'rails', 'ruby on rails'],
  PHP: ['php', 'laravel'],
  React: ['react', 'reactjs', 'react.js', 'react js'],
  Angular: ['angular'],
  'Vue.js': ['vue', 'vuejs', 'vue.js', 'vue js'],
  'Node.js': ['node', 'nodejs', 'node.js', 'node js'],
  Express: ['express'],
  Django: ['django'],
  Flask: ['flask'],
  Spring: ['spring boot', 'spring'],
  HTML: ['html', 'hypertext markup language'],
  CSS: ['css', 'scss', 'sass', 'tailwind', 'cascading style sheets'],
  SQL: ['sql', 'rdbms', 'database', 'databases'],
  MySQL: ['mysql'],
  PostgreSQL: ['postgres', 'postgresql'],
  MongoDB: ['mongodb', 'mongo'],
  Redis: ['redis'],
  GraphQL: ['graphql'],
  'REST API': ['rest', 'restful', 'api', 'apis', 'web services'],
  AWS: ['aws', 'amazon web services', 'amazon cloud'],
  Azure: ['azure', 'microsoft azure'],
  GCP: ['gcp', 'google cloud', 'google cloud platform'],
  Docker: ['docker', 'docker container', 'docker containers'],
  Kubernetes: ['kubernetes', 'k8s'],
  'CI/CD': ['ci/cd', 'ci / cd', 'jenkins', 'github actions', 'gitlab ci', 'continuous integration', 'continuous delivery'],
  Git: ['git', 'github', 'gitlab'],
  Linux: ['linux', 'unix'],
  'Machine Learning': ['machine learning', 'ml', 'deep learning', 'dl', 'tensorflow', 'pytorch', 'scikit', 'neural networks'],
  'Data Analysis': ['data analysis', 'pandas', 'numpy'],
  Flutter: ['flutter', 'dart'],
  'React Native': ['react native'],
  Swift: ['swift', 'ios'],
  Kotlin: ['kotlin', 'android'],
};

function normalize(text) {
  return ` ${String(text || '').toLowerCase().replace(/[\n\r\t]+/g, ' ')} `;
}

// Escape a needle for use inside a RegExp.
function escapeRe(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

// Match a needle only at alphanumeric boundaries, so "java" does NOT match
// inside "javascript" and "go" does NOT match inside "golang".
// Handles special characters like .net, c++, c# correctly.
function hasNeedle(hay, needle) {
  let pattern;
  const escaped = escapeRe(needle);
  if (needle.startsWith('.')) {
    pattern = `(?<![a-z0-9](?<!asp))${escaped}(?![a-z0-9])`;
  } else if (needle.endsWith('++') || needle.endsWith('#')) {
    pattern = `(?<![a-z0-9])${escaped}`;
  } else {
    pattern = `(?<![a-z0-9])${escaped}(?![a-z0-9])`;
  }
  const re = new RegExp(pattern, 'i');
  return re.test(hay);
}

// Detect which canonical skills appear in a blob of text.
function detectSkills(text) {
  const hay = normalize(text);
  const found = new Set();
  for (const [label, needles] of Object.entries(SKILL_DICTIONARY)) {
    if (needles.some(n => hasNeedle(hay, n))) found.add(label);
  }
  return found;
}

/**
 * Build the set of skills the user has, from their structured skills list
 * plus anything detectable in their raw resume text.
 */
function getUserSkills(profile = {}) {
  const skills = new Set();

  // Structured skills (JSON array of strings) — map each onto canonical labels.
  let list = profile.skills;
  if (typeof list === 'string') { try { list = JSON.parse(list); } catch { list = []; } }
  if (Array.isArray(list)) {
    const joined = list.join(' ');
    detectSkills(joined).forEach(s => skills.add(s));
    // also keep any raw skill the dictionary didn't recognise
    list.forEach(s => { if (s && String(s).trim()) skills.add(String(s).trim()); });
  }

  // Free-text resume
  if (profile.resume_text) detectSkills(profile.resume_text).forEach(s => skills.add(s));

  return skills;
}

/**
 * Derive a job-search query from the user's profile when they don't type one.
 * Priority: headline → most relevant skill + role word → generic fallback.
 */
function deriveSearchQuery(user = {}, profile = {}) {
  if (profile.headline && profile.headline.trim()) {
    return profile.headline.trim().slice(0, 80);
  }
  const skills = [...getUserSkills(profile)];
  if (skills.length) {
    // Prefer a language/framework as the anchor of the query.
    const anchor = skills[0];
    return `${anchor} Developer`;
  }
  return 'Software Engineer';
}

/**
 * Score a single job against the user's profile.
 * Returns { fit_score, matched, missing, job_skills }.
 */
function scoreJob(profile, job) {
  const userSkills = getUserSkills(profile);
  const descText = job.description || '';
  const jobText = `${job.title || ''} . ${descText}`;
  const jobSkills = detectSkills(jobText);

  // Some sources (LinkedIn search cards, or Indeed when the detail-page
  // fetch fails/gets blocked) carry little to no real job description —
  // just a title. Skill detection then only sees title words, so a single
  // skill named in the title that the user lacks would otherwise zero out
  // the whole skill score even though we have no real evidence of a gap.
  const sparse = descText.trim().length < 50;

  const matched = [...jobSkills].filter(s => userSkills.has(s));
  const missing = [...jobSkills].filter(s => !userSkills.has(s));

  // ── Skill overlap (max 60 pts) ──────────────────────────────
  // If the job lists no recognisable skills, give a neutral-ish base so it
  // isn't unfairly zeroed out.
  let skillScore;
  if (jobSkills.size === 0) {
    skillScore = 30;
  } else if (sparse) {
    // Not enough text to trust a skill-gap penalty — reward skills the
    // user does have, but don't punish for skills the sparse title
    // happens to name (we can't tell if they're a hard requirement).
    skillScore = Math.min(60, 30 + matched.length * 15);
  } else {
    skillScore = Math.round((matched.length / jobSkills.size) * 60);
  }

  // ── Title relevance (max 25 pts) ────────────────────────────
  // Overlap between the user's skills/headline words and the job title.
  const titleWords = normalize(job.title).split(/\s+/).filter(w => w.length > 1);
  const anchorWords = new Set(
    [...userSkills].map(s => s.toLowerCase())
      .concat(normalize(profile.headline).split(/\s+/))
      .filter(w => w.length > 1 && !['the', 'and', 'for', 'developer', 'engineer', 'senior', 'junior', 'of', 'in'].includes(w))
  );
  const titleHits = titleWords.filter(w => [...anchorWords].some(a => a.includes(w) || w.includes(a)));
  const titleScore = Math.min(25, titleHits.length * 8);

  // ── Experience fit (max 15 pts) ─────────────────────────────
  const userExp = parseFloat(profile.experience_years || 0);
  const reqMatch = jobText.match(/(\d+)\+?\s*years?/i);
  let expScore = 15;
  if (reqMatch) {
    const reqYears = parseInt(reqMatch[1], 10);
    if (userExp >= reqYears) expScore = 15;
    else if (userExp >= reqYears - 1) expScore = 10;
    else expScore = Math.max(0, 15 - (reqYears - userExp) * 3);
  }

  let fit = skillScore + titleScore + expScore;
  fit = Math.max(0, Math.min(100, Math.round(fit)));

  return {
    fit_score: fit,
    matched,
    missing,
    job_skills: [...jobSkills],
  };
}

module.exports = { deriveSearchQuery, scoreJob, getUserSkills, detectSkills };
