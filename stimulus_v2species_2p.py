# -*- coding: utf-8 -*-
# Stimulus design
#
# Please write here any comments or notes about the stimulus design
# that are relevant for the experiment.
import psychopy.visual
import camstim
import argparse
import numpy as np
from psychopy import monitors, visual
from camstim import SweepStim, Foraging, Window, Warp
import glob
import logging
import yaml
import os
from camstim.sweepstim import Stimulus
from itertools import product

## This is the RF mapping stim
def create_receptive_field_mapping(window, number_runs = 5):
    x = np.arange(-40,45,10)
    y = np.arange(-40,45,10)
    position = []
    for i in x:
        for j in y:
            position.append([i,j])

    stimulus = Stimulus(visual.GratingStim(window,
                        units='deg',
                        size=20,
                        mask="circle",
                        texRes=256,
                        sf=0.1,
                        ),
        sweep_params={
                'Pos':(position, 0),
                'Contrast': ([0.8], 4),
                'TF': ([4.0], 1),
                'SF': ([0.08], 2),
                'Ori': ([0,45,90, ], 3),
                },
        sweep_length=0.25,
        start_time=0.0,
        blank_length=0.0,
        blank_sweeps=0,
        runs=number_runs,
        shuffle=True,
        save_sweep_table=True,
        )
    stimulus.stim_path = r"C:\\not_a_stim_script\\receptive_field_block.stim"

    return stimulus

## This is drifting gratings
def create_gratingStim(window, number_runs = 5):
    stimulus_grating = Stimulus(visual.GratingStim(
                        window,
                        pos=(0, 0),
                        units='deg',
                        size=(250, 250),
                        mask="None",
                        texRes=256,
                        sf=0.1,
                        ),
        sweep_params={
                'Contrast': ([0.8], 0),
                'TF': ([1.0, 2.0, 4.0, 8.0, 15.0], 1),
                'SF': ([0.02, 0.04, 0.08, 0.16, 0.32], 2),
                'Ori': (range(0, 180, 45), 3),
                },
        sweep_length=1,
        start_time=0.0,
        blank_length=1.25,
        blank_sweeps=0,
        runs=number_runs,
        shuffle=True,
        save_sweep_table=True,
        )
    stimulus_grating.stim_path = r"C:\\not_a_stim_script\\drifting_gratings_field_block.stim"

    return stimulus_grating

#this gets total conditions for stimuli defined above
def count_total_conditions(stimulus):
    """
    Given a camstim Stimulus object, return the number of unique parameter combinations.
    """
    sweep_params = stimulus.sweep_params
    param_values = []

    for key, (values, _) in sweep_params.items():
        # Ensure range is converted to list
        if type(values).__name__ == 'range':
            values = list(values)
        param_values.append(values)

    total_conditions = len(list(product(*param_values)))
    return total_conditions


#this gets trial duration for stimuli defined above
def get_trial_duration_seconds(stimulus):
    """
    Returns the duration of one full trial (sweep + blank) in seconds.
    """
    sweep_length = getattr(stimulus, 'sweep_length', 0)
    blank_length = getattr(stimulus, 'blank_length', 0)
    return sweep_length + blank_length

############################################################################## main code block

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
    
    # An integer representing the experiment group. Defaults to test group (value of 2).
    dev_mode = json_params.get('dev_mode', True)
    num_reps = json_params.get('num_reps', 1) 
    print("num_reps is: ",num_reps)
    inter_block_interval = json_params.get('inter_block_interval', 10)

    dist = 15.0
    wid = 52.0

    if dev_mode:
        my_monitor = monitors.Monitor(name='Test')
        my_monitor.setSizePix((800,600))
        my_monitor.setWidth(wid)
        my_monitor.setDistance(dist)
        my_monitor.saveMon()
        win = Window(size=[800,600], # [1024,768],
            fullscr=False,
            screen=0,
            monitor= my_monitor,
            warp=Warp.Spherical,
            color= "gray",
            units = 'deg'
        )
    else: 
        win = Window(
            fullscr=True,
            screen=0,
            monitor='Gamma1.Luminance50',
            warp=Warp.Spherical,
        )


    #define number of trials for each stim type    
    nb_runs_ephys_rf = 10
    nb_run_gratings = 15


    ephys_rf_stim = create_receptive_field_mapping(win, number_runs=nb_runs_ephys_rf)
    drifting_grating_stim = create_gratingStim(win, number_runs=nb_run_gratings)

    print(
        "ephys_rf, total conditions: ", count_total_conditions(ephys_rf_stim),
        ", and trial duration: ", get_trial_duration_seconds(ephys_rf_stim))    

    print(
        "gratings, total conditions: ", count_total_conditions(drifting_grating_stim),
        ", and trial duration: ", get_trial_duration_seconds(drifting_grating_stim))

    All_stim = []

    # Add RF code from ephys
    current_time = 0
    if num_reps == 1:
        length_rf_seconds = 10 #for testing purposes
    else: 
        length_rf_seconds = (
            count_total_conditions(ephys_rf_stim)
            *get_trial_duration_seconds(ephys_rf_stim)
            *nb_runs_ephys_rf
            )

    ephys_rf_stim.set_display_sequence([(current_time, current_time+length_rf_seconds)])

    All_stim.append(ephys_rf_stim)
    print("length_rf_minutes: ",length_rf_seconds/60)

    # drifting_grating_stim
    if num_reps == 1:
        length_drifting_grating_seconds = 10
    else:
        length_drifting_grating_seconds = (
            count_total_conditions(drifting_grating_stim)
            *get_trial_duration_seconds(drifting_grating_stim)
            *nb_run_gratings
            )

    current_time = current_time+length_rf_seconds+inter_block_interval

    drifting_grating_stim.set_display_sequence([(current_time, current_time+length_drifting_grating_seconds)])
    
    All_stim.append(drifting_grating_stim)
    print("length_drifting_grating_minutes: ",length_drifting_grating_seconds/60)




    pre_blank = 0
    post_blank = 0
    ss = SweepStim(win,
                     stimuli=All_stim,
                     pre_blank_sec= pre_blank,
                     post_blank_sec= post_blank,
                     params={},
                     )

    # add in foraging so we can track wheel, potentially give rewards, etc
    f = Foraging(window = win,
                    auto_update = False,
                    params= {}
                    )
    
    ss.add_item(f, "foraging")

    ss.run()
