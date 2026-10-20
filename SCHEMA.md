# Mock OA bank — JSON schema (schemaVersion 2.0)

Files: `assessment-01.json` … `assessment-05.json` (minified). The previous (v1) banks are kept unchanged in `legacy/`.
Practice material only — not official Nasdaq questions.

## The five assessments

| OA | Level | Time (min) MCQ / Apt / Data / SQL / Pandas / DSA | SQL questions (tables) | Hints |
|---|---|---|---|---|
| 1 | Easy | 30 / 15 / 20 / 20 / 30 / 30 = 145 | 2 (1, 2) | yes |
| 2 | Easy to Medium | 30 / 15 / 20 / 20 / 30 / 30 = 145 | 2 (1, 2) | yes |
| 3 | Medium | 25 / 10 / 15 / 25 / 30 / 30 = 135 | 3 (2, 3, 4) | yes |
| 4 | Medium to Hard | 20 / 10 / 15 / 25 / 30 / 40 = 140 | 3 (2, 3, 4) | no |
| 5 | Hard | 20 / 10 / 15 / 25 / 30 / 40 = 140 | 3 (2, 3, 4) | no |

Every OA has 25 CS/AI/ML/statistics/testing MCQs, 15 aptitude MCQs, 12 chart-based data-analysis MCQs, 5 pandas and 2 DSA questions.
Marks are the same in every OA (**1,800**): MCQs 25×16 = 400, aptitude 15×16 = 240, data analysis 12×25 = 300, SQL 300
(OA1/2: 100 + 200; OA3-5: 80 + 100 + 120), pandas 5×60 = 300, DSA 100 + 160 = 260.
Mean difficulty per OA (easy = 1, medium = 2, hard = 3): 1.02, 1.50, 2.01, 2.51, 2.98 — `validate.py` enforces that every section is non-decreasing across the OAs.

## Top level
`schemaVersion, assessmentId, title, level, description, disclaimer, hintsEnabled, totalQuestions, totalMarks,
timing.standard {totalSeconds, sectionSeconds{mcq,apt,da,sql,pandas,dsa}}, revealPolicy, sections[]`.
Section: `{sectionId, type: mcq|apt|da|sql|pandas|dsa, title, questionCount, durationSeconds, totalMarks, questions[]}`.
Private (never sent to the candidate before the attempt ends): `questions[*].solution`, `questions[*].hiddenTests`.

## Questions
Common: `id, type, tags, difficulty (easy|medium|hard), marks, statement, solution, hints?`.
* **mcq-type** (`type: "mcq"`, `kind: concept|aptitude|data-analysis`): `topic, topicCode, options[A-D], solution{correctOptionId, explanation}`; hints = 1 formula/idea hint. Data-analysis questions carry `charts[]`.
* **charts**: `{type: bar|grouped|stacked|line|scatter|pie|table, title, xLabel, yLabel, categories, series[{name, values|points}], slices[], columns/rows}`; rendered as SVG with a "show values as table" fallback.
* **sql**: `subtype, tables[], tableCount, schemaSql, sampleTables[{name,columns,rows}], sampleDataSql, starterQuery, walkthrough, publicTests/hiddenTests{dataSql, expected}, checkQueries` (grading as before: fresh in-memory SQLite per test).
* **pandas**: `functionName, functionSignature, starterCode, inputs[], parameters[], walkthrough, publicTests/hiddenTests{inputs, params, expected}`.
* **dsa**: `functionName, functionSignature, starterCode, constraints[], examples[{description, input, output, steps[]}], publicTests/hiddenTests`.
* OA1-3 coding questions have `hints[3]` (progressive, LeetCode style). `sourceId` records the origin of reused tasks.

## Grading
Unchanged: `earned = marks × Σ(weights of passed tests) / Σ(all weights)`; public tests weigh 30 in total, hidden 70. `oa_lib.grade_question` implements it; MCQ-type questions are all-or-nothing.

## Early finish (new)
A section can be finished before its timer ends only when every question is *submitted* — MCQ-type: an option is chosen; coding: at least one explicit Submit.
`POST /api/attempts/{id}/finish-section` then grades and locks the section, and the next section starts immediately with its full duration.
After the last section the same call ends the test. Locked sections can never be reopened.
