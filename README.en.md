# Implicit Association Test (Chinese)

[简体中文](README.md) · **English**

![license](https://img.shields.io/badge/license-GPLv3-white)
![python](https://img.shields.io/badge/python-3.10%20~%203.12-white)
![psychopy](https://img.shields.io/badge/psychopy-2021%2B-white)

A ready-to-run implementation of the Implicit Association Test in Chinese, built with Python 3 and
PsychoPy. All experimental content — stimuli, instructions, response keys, block structure, scoring
parameters — lives in a single `config.yaml`. Changing the materials never requires touching code.

It scores D using the improved algorithm of Greenwald, Nosek and Banaji (2003), runs a 180-trial
seven-block design, and writes one row per trial to disk. It has no setup wizard, no analysis charts,
and makes no network requests.

[User manual (Chinese)](使用说明.md) · [Design notes (Chinese)](docs/design.md) ·
[Upstream archive](README.upstream.md)

---

## Background

Most open-source IAT implementations on GitHub are artefacts of an earlier PsychoPy era: written for
Python 2, unopenable in current PsychoPy, with stimuli scattered across three spreadsheets and
left/right assignment left to convention. A mistake there raises no error — it silently corrupts data.

This repository began as one of them. It ran, but every change of materials meant re-reading the
source, and success was never certain.

The rewrite rests on one judgement: **experimental content belongs in configuration, not in code.**
Swapping stimuli, rewriting instructions, changing keys or trial counts should be an edit to a text
file plus a validation pass.

## Design

Seven blocks, 180 trials, about four and a half minutes. Blocks 1 and 2 practise the two dimensions
separately; blocks 3 and 4 pair them in the compatible arrangement; blocks 5 to 7 repeat with left and
right reversed. Participant IDs starting with T run the compatible pairing first, F the incompatible,
alternating to counterbalance order effects.

Blocks 1, 2 and 5 show a red X and require the correct key. Blocks 3, 4, 6 and 7 advance on error.
Both rules are recorded trial by trial, so scoring follows the data rather than the current config.

## Timing

Response time starts at the frame on which the stimulus actually appeared, taken from the value
returned by `win.flip()`. The nominal 0.3 s inter-stimulus delay is used only to schedule presentation;
measuring against it would introduce a systematic offset of tens of milliseconds. Keypress timestamps
come from `getKeys` event times. Measured error is under 1 ms.

## Usage

```
check.cmd    validate config, print the trial layout, open no window
run.cmd      run a session; asks for participant ID
score.cmd    score every csv under data/, write processed.csv
edit.cmd     open config.yaml in Notepad
```

Requirements: Windows 10+, Python 3.10–3.12, `pip install psychopy pyyaml`.

Always run `check.cmd` after editing the configuration. It reports the offending block and line rather
than letting a session run to completion with invalid settings.

## Scoring

```bash
python score.py                      # whole data directory
python score.py data/T001_xxx.csv    # one participant
```

Twelve steps of Greenwald et al. (2003) Table 4: blocks 3, 4, 6 and 7 only; trials above the latency
ceiling and participants with too many fast trials removed; pooled standard deviations computed from
correct trials; error trials replaced by the block mean plus 600 ms; the two differences standardised
and averaged.

Output is `processed.csv`, one row per participant, with D1, its two components, accuracy, share of
fast trials, and the exclusion reason.

## Notes

- Chinese text requires a CJK font on the system; Microsoft YaHei and SimHei are probed in that order.
- Do not edit `config.yaml` mid-session. It is read once at startup, and the stored config snapshot
  would no longer describe what actually ran.
- Do not open data files in Excel or WPS and save them; the encoding and date formats will change.
- Error-rate exclusion is off by default. If your methods section declares it, set
  `scoring.error_rate_exclude` to 0.10 or 0.20, otherwise the step is skipped.

## Development

```bash
python tests/test_core.py        # config validation, block generation, scoring
python iat/run.py --check-only   # validate config only
```

Tests do not import PsychoPy. Timing accuracy is verified by injecting keypresses at fixed offsets;
see section 9 of the design notes.

## Attribution

The implementation reworks the approach of [ianhussey/IAT](https://github.com/ianhussey/IAT)
(Ian Hussey, 2016); upstream files are preserved unmodified. The paradigm follows Greenwald, McGhee
and Schwartz (1998), the block design follows the seven-block scheme published by the Institute of
Psychology, Chinese Academy of Sciences, and scoring follows Greenwald, Nosek and Banaji (2003).

## License

[GPLv3](LICENSE)
