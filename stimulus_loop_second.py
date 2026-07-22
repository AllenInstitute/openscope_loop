# -*- coding: utf-8 -*-
# Stimulus design
#
# Group C, Session 2 (day 2; 116.5 min plus 8.1 min RF mapping):
#   - Phase 1 (57.5 min):
#       - 20 presentations of movie52 (10 min)
#       - 10 presentations of movie00 (5 min)
#       - 50 presentations of movies 03-52 in pseudorandom order (25 min)
#       - 10 presentations of movie00 (5 min)
#       - 20 alternations between movie52 and movie03 (10 min)
#       - 5 presentations of movie00 (2.5 min)
#
#   - Phase 2 (24 min):
#       - Drifting gratings with a spatial frequency of 0.04 cycles/deg, 80% contrast,
#         8 directions (0º, 45º, 90º, 135º, 180º, 225º, 270º, and 315º; clockwise
#         from 0º = right-to-left), and 5 temporal frequencies (1, 2, 4, 8, and 15 Hz),
#         with 16 repeats per condition, presented in random order for 2 seconds each
#       - Gray screen (2.5 min)
#
#   - Phase 3 (22.5 min):
#       - Static gratings at 6 orientations (0º, 30º, 60º, 90º, 120º, and 150º;
#         clockwise from 0º = vertical), 5 spatial frequencies (0.02, 0.04, 0.08,
#         0.16, and 0.32 cycles/degree), and 4 phases (0, 0.25, 0.5, and 0.75), with
#         40 repeats per condition, presented in random order for 0.25 seconds with
#         no intervening gray period
#       - Gray screen (2.5 min)
#
#   - Phase 4 (12.5 min):
#       - Two 5-minute blocks of the same zebra-noise movie sequence, separated by
#         a 2.5-minute gray screen
#
#   - Receptive-field mapping (8.1 min):
#       - 8 repeats of 20-degree Gabors across a 9 x 9 position grid


import argparse
import glob
import logging
import os

import numpy as np
import yaml
from psychopy import monitors, visual
from camstim import Foraging, MovieStim, Stimulus, SweepStim, Window, Warp


MOVIE_LENGTH_SECONDS = 30.0
MOVIE_FRAME_RATE = 30.0
DISPLAY_SIZE = (1920, 1080)
SESSION_2_MOVIE_PRESENTATIONS = 115
GRAY_SCREEN_SECONDS = 150.0

DRIFTING_DIRECTIONS = range(0, 360, 45)
DRIFTING_TEMPORAL_FREQUENCIES = [1.0, 2.0, 4.0, 8.0, 15.0]
DRIFTING_REPEATS = 16
DRIFTING_SWEEP_SECONDS = 2.0

STATIC_ORIENTATIONS = range(0, 180, 30)
STATIC_SPATIAL_FREQUENCIES = [0.02, 0.04, 0.08, 0.16, 0.32]
STATIC_PHASES = [0.0, 0.25, 0.5, 0.75]
STATIC_REPEATS = 40
STATIC_SWEEP_SECONDS = 0.25

ZEBRA_MOVIE_FILENAME = "zebra_allen_screen_tscale_30_scale_10.npy"
ZEBRA_BLOCK_SECONDS = 300.0

RF_GRID_COORDINATES = range(-40, 45, 10)
RF_ORIENTATIONS = [0, 45, 90]
RF_REPEATS = 8
RF_SWEEP_SECONDS = 0.25


def get_session_timeline(movie_count):
    """Return the Group C Session 2 stimulus intervals in seconds."""
    movie_end = movie_count * MOVIE_LENGTH_SECONDS

    drifting_duration = (len(DRIFTING_DIRECTIONS) *
                         len(DRIFTING_TEMPORAL_FREQUENCIES) *
                         DRIFTING_REPEATS * DRIFTING_SWEEP_SECONDS)
    drifting_interval = (movie_end, movie_end + drifting_duration)

    static_start = drifting_interval[1] + GRAY_SCREEN_SECONDS
    static_duration = (len(STATIC_ORIENTATIONS) *
                       len(STATIC_SPATIAL_FREQUENCIES) *
                       len(STATIC_PHASES) * STATIC_REPEATS *
                       STATIC_SWEEP_SECONDS)
    static_interval = (static_start, static_start + static_duration)

    zebra_start = static_interval[1] + GRAY_SCREEN_SECONDS
    zebra_intervals = [
        (zebra_start, zebra_start + ZEBRA_BLOCK_SECONDS),
        (zebra_start + ZEBRA_BLOCK_SECONDS + GRAY_SCREEN_SECONDS,
         zebra_start + 2 * ZEBRA_BLOCK_SECONDS + GRAY_SCREEN_SECONDS),
    ]

    rf_start = zebra_intervals[1][1]
    rf_duration = (len(RF_GRID_COORDINATES) * len(RF_GRID_COORDINATES) *
                   len(RF_ORIENTATIONS) * RF_REPEATS * RF_SWEEP_SECONDS)
    rf_interval = (rf_start, rf_start + rf_duration)

    return {
        "movies": (0.0, movie_end),
        "drifting_gratings": drifting_interval,
        "drifting_gray": (drifting_interval[1], static_start),
        "static_gratings": static_interval,
        "static_gray": (static_interval[1], zebra_start),
        "zebra_noise": zebra_intervals,
        "zebra_gray": (zebra_intervals[0][1], zebra_intervals[1][0]),
        "rf_mapping": rf_interval,
        "session_end": rf_interval[1],
    }


def load_movie_order(data_folder, ordering_name):
    """Load and validate the movie ordering for Session 2 Phase 1."""
    order_path = os.path.join(data_folder, "stimulus_orderings",
                              ordering_name + ".txt")
    if not os.path.isfile(order_path):
        raise IOError("Movie ordering does not exist: {}".format(order_path))

    order = np.atleast_1d(np.loadtxt(order_path).astype(int))
    if order.ndim != 1:
        raise ValueError("Movie ordering must contain one movie ID per row.")
    if len(order) != SESSION_2_MOVIE_PRESENTATIONS:
        raise ValueError("Session 2 requires {} movie presentations; found {}."
                         .format(SESSION_2_MOVIE_PRESENTATIONS, len(order)))
    if (order < 0).any():
        raise ValueError("Movie IDs cannot be negative.")

    return order


def make_movie_stimuli(movie_paths, order, window):
    """Create the natural-movie stimuli for the supplied presentation order."""
    all_starts = np.arange(len(order), dtype=float) * MOVIE_LENGTH_SECONDS
    stims = []
    unique_movies = np.unique(order)
    for i in range(len(unique_movies)):
        current_movie_id = unique_movies[i]
        if i < len(movie_paths):
            starts = all_starts[order == current_movie_id]
            display_sequence = list(zip(
                starts, starts + MOVIE_LENGTH_SECONDS))
            stimulus = MovieStim(movie_path=movie_paths[current_movie_id],
                                 window=window,
                                 frame_length=1.0 / MOVIE_FRAME_RATE,
                                 size=DISPLAY_SIZE,
                                 start_time=0.0,
                                 stop_time=None,
                                 flip_v=True,
                                 runs=len(display_sequence))
            stimulus.set_display_sequence(display_sequence)
            stims.append(stimulus)
        else:
            raise ValueError(
                "Order index is greater than the number of movie clips.")

    return stims, all_starts[-1] + MOVIE_LENGTH_SECONDS


def make_grating_stimulus(window, sweep_params, sweep_length, runs,
                          display_interval):
    """Create a full-screen grating stimulus in one scheduled interval."""
    stimulus = Stimulus(
        visual.GratingStim(window,
                           pos=(0, 0),
                           units="deg",
                           size=(250, 250),
                           mask="None",
                           texRes=256,
                           sf=0.1),
        sweep_params=sweep_params,
        sweep_length=sweep_length,
        start_time=0.0,
        blank_length=0.0,
        blank_sweeps=0,
        runs=runs,
        shuffle=True,
        save_sweep_table=True)
    stimulus.set_display_sequence([display_interval])
    return stimulus


def make_drifting_gratings(window, display_interval):
    """Create the 40 drifting-grating conditions with 16 repeats each."""
    stimulus = make_grating_stimulus(
        window,
        sweep_params={
            "Contrast": ([0.8], 0),
            "TF": (DRIFTING_TEMPORAL_FREQUENCIES, 1),
            "SF": ([0.04], 2),
            "Ori": (DRIFTING_DIRECTIONS, 3),
        },
        sweep_length=DRIFTING_SWEEP_SECONDS,
        runs=DRIFTING_REPEATS,
        display_interval=display_interval)
    stimulus.stim_path = (
        r"C:\\not_a_stim_script\\create_drifting_gratings.stim")
    return stimulus


def make_static_gratings(window, display_interval):
    """Create the 120 static-grating conditions with 40 repeats each."""
    stimulus = make_grating_stimulus(
        window,
        sweep_params={
            "Contrast": ([0.8], 0),
            "SF": (STATIC_SPATIAL_FREQUENCIES, 1),
            "Ori": (STATIC_ORIENTATIONS, 2),
            "Phase": (STATIC_PHASES, 3),
        },
        sweep_length=STATIC_SWEEP_SECONDS,
        runs=STATIC_REPEATS,
        display_interval=display_interval)
    stimulus.stim_path = (
        r"C:\\not_a_stim_script\\create_static_gratings.stim")
    return stimulus


def make_zebra_noise(window, movie_path, display_intervals):
    """Create two presentations of the five-minute zebra-noise movie."""
    if not os.path.isfile(movie_path):
        raise IOError("Zebra-noise movie does not exist: {}".format(movie_path))

    stimulus = MovieStim(movie_path=movie_path,
                         window=window,
                         frame_length=1.0 / MOVIE_FRAME_RATE,
                         size=DISPLAY_SIZE,
                         start_time=0.0,
                         stop_time=None,
                         flip_v=True,
                         runs=len(display_intervals))
    stimulus.set_display_sequence(display_intervals)
    return stimulus


def make_receptive_field_mapping(window, display_interval):
    """Create the Gabor receptive-field mapping block used after recording."""
    positions = []
    for x_position in RF_GRID_COORDINATES:
        for y_position in RF_GRID_COORDINATES:
            positions.append([x_position, y_position])

    stimulus = Stimulus(
        visual.GratingStim(window,
                           units="deg",
                           size=20,
                           mask="circle",
                           texRes=256,
                           sf=0.1),
        sweep_params={
            "Pos": (positions, 0),
            "TF": ([4.0], 1),
            "SF": ([0.08], 2),
            "Ori": (RF_ORIENTATIONS, 3),
            "Contrast": ([0.8], 4),
        },
        sweep_length=RF_SWEEP_SECONDS,
        start_time=0.0,
        blank_length=0.0,
        blank_sweeps=0,
        runs=RF_REPEATS,
        shuffle=True,
        save_sweep_table=True)
    stimulus.stim_path = (
        r"C:\\not_a_stim_script\\create_receptive_field_mapping.stim")
    stimulus.set_display_sequence([display_interval])
    return stimulus


def build_session_stimuli(window, data_folder, ordering_name, zebra_movie_path,
                          include_rf_mapping=True):
    """Build every stimulus in Group C Session 2 in protocol order."""
    order = load_movie_order(data_folder, ordering_name)
    movie_paths = glob.glob(os.path.join(data_folder, "full_movies", "*.npy"))
    stimuli, movie_end = make_movie_stimuli(movie_paths, order, window)
    timeline = get_session_timeline(len(order))

    if movie_end != timeline["movies"][1]:
        raise ValueError("Movie ordering duration does not match the timeline.")

    stimuli.append(make_drifting_gratings(
        window, timeline["drifting_gratings"]))
    stimuli.append(make_static_gratings(
        window, timeline["static_gratings"]))
    stimuli.append(make_zebra_noise(
        window, zebra_movie_path, timeline["zebra_noise"]))
    if include_rf_mapping:
        stimuli.append(make_receptive_field_mapping(
            window, timeline["rf_mapping"]))
    else:
        timeline["session_end"] = timeline["rf_mapping"][0]

    return stimuli, timeline


if __name__ == "__main__":
    parser = argparse.ArgumentParser("mtrain")
    parser.add_argument("json_path", nargs="?", type=str, default="")

    args, _ = parser.parse_known_args()

    if args.json_path == "":
        logging.warning("No JSON path provided; using development defaults.")
        json_params = {}
    else:
        with open(args.json_path, 'r') as f:
            # Mtrain provides JSON, which is also valid YAML.
            json_params = yaml.load(f) or {}
            logging.info("Loaded json parameters from mtrain")

    data_folder = json_params.get('data_folder', os.path.abspath("data"))
    ordering_name = json_params.get(
        'stimulus_orderings',
        'round_2_controls/movie_order_groupC02')
    zebra_movie_path = json_params.get('zebra_movie', ZEBRA_MOVIE_FILENAME)
    if not os.path.isabs(zebra_movie_path):
        zebra_movie_path = os.path.join(data_folder, zebra_movie_path)

    include_rf_mapping = json_params.get("include_rf_mapping", True)
    dev_mode = json_params.get("dev_mode", True)

    dist = 15.0
    wid = 52.0

    if dev_mode:
        monitor = monitors.Monitor('testMonitor', distance=dist, width=wid)
    else:
        monitor = "Gamma1.Luminance50"

    window = Window(fullscr=True,
                    monitor=monitor,
                    screen=0,
                    warp=Warp.Spherical
                    )

    stims, timeline = build_session_stimuli(
        window, data_folder, ordering_name, zebra_movie_path,
        include_rf_mapping=include_rf_mapping)
    logging.info("Expected Session 2 duration: %.1f minutes",
                 timeline["session_end"] / 60.0)

    ss = SweepStim(window,
                   stimuli=stims,
                   params={})

    f = Foraging(window=window,
                 auto_update=False,
                 params={})
    ss.add_item(f, "foraging")

    ss.run()
