# -*- coding: utf-8 -*-
# Stimulus design
#
# The experiment consists of two phases in which different sets of 30 sec long natural movies will be presented:
#   - Phase 1 consists of two natural movies (i.e., movie01 and movie02) and a constant gray screen (i.e., movie00).
#   - Phase 2 consists of 50 natural movies (i.e., movie03-movie52) and a constant gray screen (i.e., movie00).
#
# Animals are assigned into two groups (A and B), each presented with the movies in different order.
# In both groups, a total of 230 movies will be presented for a total time of 115 min:
#   1. For group A:
#           - Phase 1:
#               - 50 presentations of movie01 (25 min)
#               - 10 presentations of movie00 (5 min)
#               - 50 alternations between movie01 and movie02 (25 min)
#               - 10 presentations of movie00 (5 min)
#
#           - Phase 2:
#               - 20 presentations of movie03 (10 min)
#               - 10 presentations of movie00 (5 min)
#               - 50 sequential presentations of movie03 to movie52 (25 min)
#               - 10 presentations of movie00 (5 min)
#               - 20 alternations between movie03 and movie52 (10 min)
#
#   2. For group B:
#           - Phase 1:
#               - 50 alternations between movie01 and movie02 (25 min)
#               - 10 presentations of movie00 (5 min)
#               - 50 presentations of movie01 (25 min)
#               - 10 presentations of movie00 (5 min)
#
#           - Phase 2:
#               - 20 presentations of movie03 (10 min)
#               - 10 presentations of movie00 (5 min)
#               - 50 presentations of movie52 (25 min)
#               - 10 presentations of movie00 (5 min)
#               - 20 alternations between movie03 and movie52 (10 min)
#   3. For group C (new experiment, August 2026):
#           - Session 1 (day 1; 115 min):
#               - Phase 1 (60 min):
#                   - 50 presentations of movie01 (25 min)
#                   - 10 presentations of movie00 (5 min)
#                   - 50 alternations between movie01 and movie02 (25 min)
#                   - 10 presentations of movie00 (5 min)
#
#               - Phase 2 (55 min):
#                   - 20 presentations of movie52 (10 min)
#                   - 10 presentations of movie00 (5 min)
#                   - 50 sequential presentations from movie52 to movie03 (25 min)
#                   - 10 presentations of movie00 (5 min)
#                   - 20 alternations between movie52 and movie03 (10 min)
#
#               - Receptive-field mapping (8.1 min):
#                   - 8 repeats of 20-degree Gabors across a 9 x 9 position grid

import argparse
import glob
import numpy as np
from psychopy import monitors, visual
from camstim import SweepStim, Foraging, Window, Warp, MovieStim, Stimulus
import logging
import yaml
import os


def make_movie_stimulus(movie_paths, order, window):
    """Generate a Stimulus that plays a series of movie clips in a specified order."""

    # Convert the order into a list of display sequence tuples. There should be one display sequence list per movie
    # clip. Each display sequence list contains a set of tuples of the form (start_second, stop_second). Theses tuples
    # define the start and stop time for when to play the clip and are determined by the order vector
    movie_length = 30   # in seconds
    frame_rate = 30.0

    all_starts = np.arange(0, movie_length * len(order), movie_length).astype(float)
    display_sequences = []
    for i in np.unique(order):
        display_sequences.append(list(zip(all_starts[order == i], all_starts[order == i] + movie_length)))

    # Load each movie clip into its own MovieStim object. The display sequence will be set later so the clips play
    # in the correct order.
    stims = []
    unique_movies = np.unique(order)
    num_movies = len(unique_movies)
    for i in range(num_movies):
        current_movie_id = unique_movies[i]
        # If the order index is less than the number of movie clips, load the movie clip.
        if i < len(movie_paths):

            # The movie clips should be 30 seconds long and should be played at 30 fps.
            s = MovieStim(movie_path=movie_paths[current_movie_id],
                          window=window,
                          frame_length=1.0 / frame_rate,
                          size=(1920, 1080),
                          start_time=0.0,
                          stop_time=None,
                          flip_v=True, runs=len(display_sequences[i]))
            s.set_display_sequence(display_sequences[i])

        else:
            raise ValueError("Order index is greater than the number of movie clips.")

        stims.append(s)

    last_time = all_starts[-1] + movie_length

    return stims, last_time


def create_receptive_field_mapping(window, number_runs=8):
    """Create the Gabor receptive-field mapping block used after recording."""
    positions = []
    for x_position in np.arange(-40, 45, 10):
        for y_position in np.arange(-40, 45, 10):
            positions.append([x_position, y_position])

    stimulus = Stimulus(
        visual.GratingStim(window,
                           units='deg',
                           size=20,
                           mask="circle",
                           texRes=256,
                           sf=0.1),
        sweep_params={
            'Pos': (positions, 0),
            'TF': ([4.0], 1),
            'SF': ([0.08], 2),
            'Ori': ([0, 45, 90], 3),
            'Contrast': ([0.8], 4),
        },
        sweep_length=0.25,
        start_time=0.0,
        blank_length=0.0,
        blank_sweeps=0,
        runs=number_runs,
        shuffle=True,
        save_sweep_table=True)
    stimulus.stim_path = (
        r"C:\\not_a_stim_script\\create_receptive_field_mapping.stim")
    return stimulus


if __name__ == "__main__":
    parser = argparse.ArgumentParser("mtrain")
    parser.add_argument("json_path", nargs="?", type=str, default="")

    args, _ = parser.parse_known_args() # <- this ensures that we ignore other arguments that might be needed by camstim
    
    # print args
    if args.json_path == "":
        logging.warning("No json path provided, using default parameters. THIS IS NOT THE EXPECTED BEHAVIOR FOR PRODUCTION RUNS")
        json_params = {}
    else:
        with open(args.json_path, 'r') as f:
            # we use the yaml package here because the json package loads as unicode, which prevents using the keys as parameters later
            json_params = yaml.load(f)
            logging.info("Loaded json parameters from mtrain")
            # end of mtrain part

    data_folder = json_params.get('data_folder', os.path.abspath("data"))
    
    # An integer representing the experiment group. Defaults to test group (value of 2).
    group = json_params.get('stimulus_orderings', 'movie_order_groupTEST')
    
    opto_disabled = json_params.get('disable_opto', True)
    dev_mode = json_params.get("dev_mode", True)
    include_rf_mapping = json_params.get("include_rf_mapping", True)

    # Paths to the movie clip files to load.
    movie_clip_files = glob.glob(os.path.join(data_folder, 'full_movies', '*.npy'))

    # Load the movie clip order for each experimental group as provided by the Ziv lab:
    order = (np.loadtxt(os.path.join(data_folder, 'stimulus_orderings', group+".txt")).astype(int))

    dist = 15.0
    wid = 52.0

    # create a monitor
    if dev_mode:
        monitor = monitors.Monitor('testMonitor', distance=dist, width=wid)
    else:
        monitor = "Gamma1.Luminance50"

    # Create display window
    window = Window(fullscr=True,   # Will return an error due to default size. Ignore.
                    monitor=monitor,  # Will be set to a gamma calibrated profile by MPE
                    screen=0,
                    warp=Warp.Spherical
                    )

    stims, last_time = make_movie_stimulus(movie_clip_files, order, window)

    if include_rf_mapping:
        rf_mapping = create_receptive_field_mapping(window, number_runs=8)
        rf_duration = rf_mapping.get_total_time()
        rf_mapping.set_display_sequence(
            [(last_time, last_time + rf_duration)])
        stims.append(rf_mapping)

    ss = SweepStim(window,
                     stimuli=stims,
                     # pre_blank_sec=1,
                     # post_blank_sec=1,
                     params={},
                     )

    # add in foraging so we can track wheel, potentially give rewards, etc
    f = Foraging(window = window,
                    auto_update = False,
                    params= {}
                    )
    
    ss.add_item(f, "foraging")

    ss.run()
