# OpenScope Visual Loop

Stimulus presentation code, orderings, and MTrain regimens for the OpenScope
visual loop experiments.

## Experiment Overview

The repository contains two experimental cohorts:

- **Groups A and B (August 2024):** one 115-minute natural-movie session
   followed by receptive-field mapping. The groups see the same movie stimuli
   in different orders.
- **Group C (August 2026):** a control cohort with additional habituation and
   two recording sessions on consecutive days. Session 1 uses natural movies;
   Session 2 combines natural movies, drifting gratings, static gratings, and
   zebra noise.

All natural movie and gray-screen clips are 30 seconds long. `movie00` is the
gray screen, `movie01` and `movie02` are the repeated Phase 1 movies, and
`movie03` through `movie52` form the 50-movie set.

## Requirements

- Windows OS, as required by Camstim and the acquisition hardware
- Python 2.7.18
- PsychoPy 1.82.01
- Camstim 0.2.4
- Matplotlib 2.2.3

The remaining pinned dependencies are listed in `environment.yml`.

## Installation

1. Create and activate the Conda environment:

    ```bash
    conda env create -f environment.yml
    conda activate allen_stimulus
    ```

2. Install the bundled Camstim package and Matplotlib:

    ```bash
    pip install camstim/.
    conda install matplotlib=2.2.3
    ```

## Input Data

Download [full_movies.zip](https://weizmannacil-my.sharepoint.com/:u:/g/personal/daniel_deitch_weizmann_ac_il/EbetUfh76FtBtDkpqd-7gAEB43WxjSCKutxW8sJtvIfCiA?e=LPY5ND)
and extract the raw `.npy` movie clips into `data/full_movies`. Ordering files
are stored under `data/stimulus_orderings`; Group C orderings and its regimen
are under `data/stimulus_orderings/round_2_controls`.

Group C Session 2 also requires the five-minute zebra-noise array
`zebra_allen_screen_tscale_30_scale_10.npy`. By default, the script looks for
this file directly under the configured `data_folder`. The source MP4 is
included at
`data/stimulus_orderings/round_2_controls/zebra_allen_screen_tscale_30_scale_10.mp4`.

The expected production layout is:

```text
data/
|-- full_movies/
|   |-- movie00.npy
|   |-- ...
|   `-- movie52.npy
|-- stimulus_orderings/
|   `-- round_2_controls/
|       |-- movie_order_groupC01.txt
|       |-- movie_order_groupC02.txt
|       |-- rig_hab_day1_groupC.txt
|       |-- rig_hab_day3_groupC.txt
|       |-- rig_hab_day5_groupC.txt
|       `-- regimen.yml
`-- zebra_allen_screen_tscale_30_scale_10.npy
```

## Running the Experiment

Production Group C sessions are defined in
`data/stimulus_orderings/round_2_controls/regimen.yml`. The regimen progresses
through five training stages (`DAY_6` through `DAY_10`), three rig-habituation
stages, and the two ephys sessions:

| Stage | Script | Ordering | Duration |
| --- | --- | --- | ---: |
| `GROUPC_60MIN_DAY1_2` | `stimulus_loop.py` | `rig_hab_day1_groupC` | 60 min |
| `GROUPC_90MIN_DAY3_4` | `stimulus_loop.py` | `rig_hab_day3_groupC` | 90 min |
| `GROUPC_120MIN_DAY5` | `stimulus_loop.py` | `rig_hab_day5_groupC` | 120 min |
| `EPHYS_GROUPC_SESSION1` | `stimulus_loop.py` | `movie_order_groupC01` | 115 min + RF mapping |
| `EPHYS_GROUPC_SESSION2` | `stimulus_loop_second.py` | `movie_order_groupC02` | about 116.5 min + RF mapping |

The scripts can also be launched directly with an MTrain-compatible JSON file:

```bash
python stimulus_loop.py path/to/session_1.json
python stimulus_loop_second.py path/to/session_2.json
```

Session 1 parameters:

```json
{
   "data_folder": "path/to/data",
   "stimulus_orderings": "round_2_controls/movie_order_groupC01",
   "include_rf_mapping": true,
   "dev_mode": false
}
```

Session 2 parameters:

```json
{
   "data_folder": "path/to/data",
   "stimulus_orderings": "round_2_controls/movie_order_groupC02",
   "zebra_movie": "zebra_allen_screen_tscale_30_scale_10.npy",
   "dev_mode": false
}
```

Set `dev_mode` to `true` to use PsychoPy's test monitor instead of the
production gamma-calibrated monitor. Running without a parameter file uses
development defaults and is not intended for production.

## Stimulus Design

### Groups A and B (2024)

Both groups receive 230 movie presentations over 115 minutes, followed by
receptive-field mapping using eight repeats of 20-degree Gabors over a 9 x 9
position grid.

**Group A**

- Phase 1: 50 presentations of `movie01`, 10 gray screens, 50 alternations
   between `movie01` and `movie02`, then 10 gray screens.
- Phase 2: 20 presentations of `movie03`, 10 gray screens, one ascending
   sequence from `movie03` through `movie52`, 10 gray screens, then 20
   alternations between `movie03` and `movie52`.

**Group B**

- Phase 1: 50 alternations between `movie01` and `movie02`, 10 gray screens,
   50 presentations of `movie01`, then 10 gray screens.
- Phase 2: 20 presentations of `movie03`, 10 gray screens, 50 presentations of
   `movie52`, 10 gray screens, then 20 alternations between `movie03` and
   `movie52`.

### Group C (2026)

#### Session 1: Natural Movies

The 115-minute session contains 230 movie presentations:

- Phase 1 (60 min): 50 presentations of `movie01`, 10 gray screens, 50
   alternations between `movie01` and `movie02`, then 10 gray screens.
- Phase 2 (55 min): 20 presentations of `movie52`, 10 gray screens, one
   descending sequence from `movie52` through `movie03`, 10 gray screens, then
   20 alternations between `movie52` and `movie03`.
- Receptive-field mapping (8.1 min, after the recording session): eight repeats
   of 20-degree Gabors over a 9 x 9 position grid.

#### Session 2: Control Stimuli

The approximately 116.5-minute recording session is followed by 8.1 minutes of
receptive-field mapping:

- Phase 1 (57.5 min): 20 presentations of `movie52`, 10 gray screens, one
   pseudorandom presentation of `movie03` through `movie52`, 10 gray screens,
   20 alternations between `movie52` and `movie03`, then 5 gray screens.
- Phase 2 (about 24 min): drifting gratings at 0.04 cycles/degree and 80%
   contrast, using eight directions and temporal frequencies of 1, 2, 4, 8,
   and 15 Hz. Each condition has 16 repeats of 2 seconds, followed by a
   2.5-minute gray screen.
- Phase 3 (22.5 min): static gratings using six orientations, five spatial
   frequencies (0.02, 0.04, 0.08, 0.16, and 0.32 cycles/degree), and four
   phases. Each condition has 40 repeats of 0.25 seconds with no intervening
   gray, followed by a 2.5-minute gray screen.
- Phase 4 (12.5 min): two presentations of the same five-minute zebra-noise
   movie, separated by a 2.5-minute gray screen.
- Receptive-field mapping (8.1 min, after the recording session): eight repeats
   of 20-degree Gabors over a 9 x 9 position grid.
