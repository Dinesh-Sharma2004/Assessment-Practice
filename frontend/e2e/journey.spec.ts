import { expect, test, type Page } from '@playwright/test'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

const bank = JSON.parse(readFileSync(resolve(process.cwd(), '../assessment-01.json'), 'utf-8'))
const refOf = (qid: string): string =>
  bank.sections.flatMap((s: any) => s.questions).find((q: any) => q.id === qid).solution.referenceSolution

async function advance(page: Page, seconds: number) {
  const r = await page.request.post('/api/test/clock', { data: { seconds } })
  expect(r.ok()).toBeTruthy()
}
async function setCode(page: Page, code: string) {
  const ed = page.locator('[data-testid=editor] .cm-content')
  await ed.click()
  await page.keyboard.press('Control+A')
  await page.keyboard.press('Delete')
  await ed.fill(code)
}
const timerSeconds = async (page: Page) => {
  const t = (await page.getByTestId('timer').innerText()).split(':').map(Number)
  return t.length === 3 ? t[0] * 3600 + t[1] * 60 + t[2] : t[0] * 60 + t[1]
}

test('full journey: six sections, hints, charts, early finish, timers, results', async ({ page }) => {
  // dashboard: five OAs with a difficulty ladder
  await page.goto('/')
  await expect(page.locator('[data-testid^=card-]')).toHaveCount(5)
  await expect(page.getByTestId('level-oa01')).toContainText('Easy')
  await expect(page.getByTestId('level-oa02')).toContainText('Easy to Medium')
  await expect(page.getByTestId('level-oa05')).toContainText('Hard')
  await page.getByTestId('start-oa01').click()
  await expect(page.getByTestId('schedule').locator('tbody tr')).toHaveCount(6)
  await page.getByTestId('begin').click()

  // ---- Section 1 (30 min): hint, persistence, timer survives refresh
  expect(await timerSeconds(page)).toBeGreaterThan(1780)
  await page.getByTestId('hint-btn').click()
  await expect(page.getByTestId('hint-1')).toBeVisible()
  await page.getByTestId('opt-B').click()
  await expect(page.getByTestId('pal-1')).toHaveAttribute('data-state', 'answered')
  await expect(page.getByTestId('save-state')).toHaveText('All changes saved')
  await expect(page.getByTestId('finish-section')).toBeDisabled()
  await expect(page.getByTestId('finish-section')).toContainText('24 left')
  await advance(page, 120)
  await page.reload()
  await page.getByTestId('pal-1').click()
  await expect(page.locator('[data-testid=opt-B] input')).toBeChecked()
  const left = await timerSeconds(page)
  expect(left).toBeLessThan(1690); expect(left).toBeGreaterThan(1640)
  await expect(page.getByTestId('sec-apt')).toHaveAttribute('data-status', 'locked')
  await expect(page.locator('body')).not.toContainText('Reference solution')

  // answer everything -> Finish Section unlocks -> next section starts immediately, old one is locked
  for (let i = 2; i <= 25; i++) {
    await page.getByTestId(`pal-${i}`).click()
    await page.locator('[data-testid=opt-B]').click()
  }
  await expect(page.getByTestId('progress')).toContainText('Answered 25/25')
  await expect(page.getByTestId('finish-section')).toBeEnabled()
  await page.getByTestId('finish-section').click()
  await page.getByTestId('confirm-finish').click()
  await expect(page.getByTestId('transition-notice')).toContainText('locked')
  await expect(page.getByTestId('sec-mcq')).toHaveAttribute('data-status', 'finalized')
  await expect(page.getByTestId('sec-apt')).toHaveAttribute('data-status', 'active')
  expect(await timerSeconds(page)).toBeGreaterThan(880)                              // fresh 15 minutes
  await expect(page.getByTestId('pal-15')).toBeVisible(); await expect(page.getByTestId('pal-16')).toHaveCount(0)

  // ---- Aptitude: let the clock run out -> automatic transition to Data Analysis (charts)
  await advance(page, 901)
  await expect(page.getByTestId('sec-da')).toHaveAttribute('data-status', 'active', { timeout: 15000 })
  await expect(page.getByTestId('chart-0')).toBeVisible()
  await expect(page.getByTestId('chart-0').locator('svg, table').first()).toBeVisible()
  await expect(page.getByTestId('pal-12')).toBeVisible()

  // ---- Data analysis -> SQL (time out)
  await advance(page, 1201)
  await expect(page.getByTestId('sec-sql')).toHaveAttribute('data-status', 'active', { timeout: 15000 })
  await expect(page.getByTestId('sql-example')).toContainText('Input table: Trades')
  await expect(page.getByTestId('sql-example').locator('table').first()).toBeVisible()
  for (const n of [1, 2, 3]) {                                                       // LeetCode-style progressive hints
    await page.getByTestId('hint-btn').click()
    await expect(page.getByTestId(`hint-${n}`)).toBeVisible()
  }
  await setCode(page, 'SELEC broken')
  await page.getByTestId('run-sql').click()
  await expect(page.getByTestId('sql-error')).toContainText('syntax error')
  await setCode(page, refOf('oa01-sql-01'))
  await page.getByTestId('run-sql').click()
  await expect(page.getByTestId('sql-output')).toContainText('101')
  await page.getByTestId('run-tests').click()
  await expect(page.getByTestId('run-result')).toContainText('2/2 passed')
  await page.getByTestId('submit-code').click()
  await expect(page.getByTestId('submit-result')).toContainText('score 100 / 100')
  await expect(page.getByTestId('finish-section')).toBeDisabled()                    // second SQL question still open
  await page.getByTestId('pal-2').click()
  await setCode(page, refOf('oa01-sql-02'))
  await page.getByTestId('submit-code').click()
  await expect(page.getByTestId('submit-result')).toContainText('score 200 / 200')
  await expect(page.getByTestId('finish-section')).toBeEnabled()
  await page.getByTestId('finish-section').click()                                   // early finish of SQL -> pandas starts now
  await page.getByTestId('confirm-finish').click()
  await expect(page.getByTestId('sec-pandas')).toHaveAttribute('data-status', 'active', { timeout: 15000 })
  await expect(page.getByTestId('sec-sql')).toHaveAttribute('data-status', 'finalized')

  // ---- pandas: explained example, execution, runtime error shown
  await expect(page.getByTestId('walkthrough')).toContainText('Trades 1, 4 and 5')
  await setCode(page, refOf('oa01-pd-01'))
  await page.getByTestId('run-tests').click()
  await expect(page.getByTestId('run-result')).toContainText('2/2 passed', { timeout: 60000 })
  await page.getByTestId('submit-code').click()
  await expect(page.getByTestId('submit-result')).toContainText('score 60 / 60', { timeout: 90000 })
  await page.getByTestId('pal-2').click()
  await setCode(page, 'import pandas as pd\ndef add_notional(trades):\n    raise ValueError("oops")\n')
  await page.getByTestId('run-tests').click()
  await expect(page.getByTestId('run-result')).toContainText('0/2 passed', { timeout: 60000 })
  await expect(page.getByTestId('run-result')).toContainText('ValueError: oops')

  // ---- DSA: pandas time runs out; submit both, End Test early
  await advance(page, 1801)
  await expect(page.getByTestId('sec-dsa')).toHaveAttribute('data-status', 'active', { timeout: 15000 })
  await expect(page.getByTestId('dsa-examples')).toContainText('Sort the prices')
  await setCode(page, refOf('oa01-dsa-01'))
  await page.getByTestId('submit-code').click()
  await expect(page.getByTestId('submit-result')).toContainText('score 100 / 100', { timeout: 90000 })
  await expect(page.getByTestId('finish-section')).toContainText('End Test')
  await expect(page.getByTestId('finish-section')).toBeDisabled()
  await page.getByTestId('pal-2').click()
  await setCode(page, refOf('oa01-dsa-02'))
  await page.getByTestId('submit-code').click()
  await expect(page.getByTestId('submit-result')).toContainText('score 160 / 160', { timeout: 90000 })
  await expect(page.getByTestId('finish-section')).toBeEnabled()
  await page.getByTestId('finish-section').click()
  await page.getByTestId('confirm-finish').click()
  await expect(page).toHaveURL(/\/results\//, { timeout: 20000 })

  // ---- results
  await expect(page.getByTestId('total-score')).toContainText('/ 1800')
  const total = Number((await page.getByTestId('total-score').innerText()).split('/')[0])
  expect(total).toBeGreaterThanOrEqual(100 + 200 + 60 + 100 + 160)                   // submitted SQL + pandas + DSA answers (MCQs add 'B' guesses)
  expect(total).toBeLessThan(1800)
  await page.getByTestId('review-oa01-dsa-01').locator('summary').first().click()
  await expect(page.getByTestId('review-oa01-dsa-01')).toContainText('Reference solution')
  await page.getByTestId('review-oa01-mcq-01').locator('summary').first().click()
  await expect(page.getByTestId('review-oa01-mcq-01')).toContainText('Explanation')
  await expect(page.locator('body')).toContainText('finished early')

  // browser Back cannot reopen the finished attempt; retake starts a separate attempt
  const attemptId = page.url().split('/').pop()!
  await page.goto(`/attempt/${attemptId}`)
  await expect(page).toHaveURL(/\/results\//)
  await page.getByTestId('retake').click()
  await page.getByTestId('begin').click()
  await expect(page).toHaveURL(/\/attempt\//)
  expect(page.url()).not.toContain(attemptId)
  await page.goto('/')
  await expect(page.getByTestId('card-oa01')).toContainText('Attempts: 2')
})

test('OA 4 has no hint buttons', async ({ page }) => {
  await page.goto('/')
  await page.getByTestId('start-oa04').click()
  await page.getByTestId('begin').click()
  await expect(page.getByTestId('timer')).toBeVisible()
  await expect(page.getByTestId('hint-btn')).toHaveCount(0)
  await expect(page.getByTestId('hint-box')).toHaveCount(0)
})
