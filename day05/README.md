# Hemolysis analysis – testing lesson (day04)

## What this project is
A Flask website that takes a CSV of hemolysis measurements (several groups,
several time points) and returns:
- a table per group and day (N, mean, SD, normality test),
- a one-way ANOVA at each time point (with Tukey post-hoc when significant),
- a graph of every unit over time.


## The tests I wrote

All tests use **fake data** that the test builds itself: 3 groups x 4 units x
2 days = 24 rows. It is the same on every run, so a result can only change if
the code changes.

| # | Test | What it checks | Why it matters |
|---|---|---|---|
| 1 | `test_part1_file_is_found_and_read` | A CSV written to disk is opened and all 24 rows arrive | Rows lost while loading would silently change the statistics |
| 2 | `test_part1_missing_file_gives_an_error` | A wrong path raises `FileNotFoundError` | The failure must be clear, not a wrong answer |
| 3 | `test_part2_columns_are_recognised` | ID, Group, Day and Hemolysis % are identified correctly | Column detection is guesswork based on names, so a mistake would give wrong results with no warning |
| 4 | `test_part3_anova_matches_independent_calculation` | For known numbers, F = 16.2126, df = (2, 9), p = 0.0010385, verdict SIGNIFICANT | Checks the statistics against a trusted answer |
| 5 | `test_part3_identical_groups_are_not_significant` | Two identical groups give F = 0, p = 1, verdict NOT significant | Checks the program doesn't invent a difference |

### Golden values (tests 4 and 5)
The expected F, df and p came from an **independent calculation**: by hand
(numpy), with statsmodels, and with SciPy. All three agreed. `logic.py` uses
SciPy, so comparing it to SciPy proves nothing. Comparing it to a different
method does.

## Extra Learning

**Where tests live.** Tests go in a separate file next to the code, named
`test_<something>.py`. They import the code and call it. Nothing inside
`logic.py` changes. pytest finds every function that starts with `test_`.


## Take-home messages
1. **A crash is not a test.** A test is code that checks a specific result and
   says pass or fail by itself. Many failures don't crash: the code runs but
   gives a wrong answer.
2. **Know the answer before you run the code.** A test needs input with a known
   right answer, which is why tests use fake data that you built.
3. **Don't test a tool with itself.** Get the expected numbers from a different
   method (golden values).
4. **A pass proves only what was tested.** Passing tests mean the code works
   for that kind of data, not for every file. If a real file fails while the
   tests pass, compare the file to the fake data and add a test for the
   difference.
5. **Test each layer for its own job.** Calculations and CSV reading belong to
   `logic.py`; saving and error messages belong to `app.py`.
6. **Trust a test that can fail.** Break the code on purpose once and check
   that the test turns red.
7. **Check your guesses by running them.** Two of my predicted bugs turned out
   to be wrong when I ran the tests. Predictions need confirming.
8. **Flag data problems; don't hide them.** Report suspicious data and let the
   analyst decide, with results shown both ways.
9. **Read the pytest output.** Dots and `PASSED` mean success, `F` and
   `FAILED` mean something broke, and `x` means a known bug failed as expected.

