'''
Allow an appropriate (design, model) combination to be chosen by the experimenter,
using a simple GUI.

This code is only intended to be used for the PsychoPy demo, to make it easy.
When you run proper experiments, then you should define your (design, model)
combination in the code to avoid GUI input errors to ensure you are running
exactly what you want to run.
'''


import logging
import numpy as np
import darc_toolbox


# define what is available
expt_type = {'Experiment type':
             ['delayed (Bayesian Adaptive Design)',
             'risky (Bayesian Adaptive Design)',
             'delayed and risky (Bayesian Adaptive Design)',
             'delayed (Griskevicius et al, 2011)',
             'delayed (Du, Green, & Myerson, 2002)',
             'delayed (Kirby 2009)',
             'delayed (Frye et al, 2016)',
             'risky (Griskevicius et al, 2011)',
             'risky (Du, Green, & Myerson, 2002)',
             ]}

delayed_design_set = {'delayed (Bayesian Adaptive Design)',
                      'delayed (Kirby 2009)',
                      'delayed (Griskevicius et al, 2011)',
                      'delayed (Frye et al, 2016)',
                      'delayed (Du, Green, & Myerson, 2002)'}

risky_design_set = {'risky (Griskevicius et al, 2011)',
                    'risky (Bayesian Adaptive Design)',
                    'risky (Du, Green, & Myerson, 2002)'}

delayed_and_risky_design_set = {'delayed and risky (Bayesian Adaptive Design)'}

delay_models_available = ['Hyperbolic', 'Exponential',
                          'HyperbolicMagnitudeEffect',
                          'ExponentialMagnitudeEffect',
                          'MyersonHyperboloid',
                          'ModifiedRachlin']

risky_models_available = ['Hyperbolic',
                          'ProportionalDifference',
                          'LinearInLogOdds']

delayed_and_risky_models_available = ['MultiplicativeHyperbolic']


def gui_chooser_for_demo(win, gui, core, event, expInfo):
    '''
    Get user choices about (design, model) combination and generate
    the appropriate objects
    '''
    mouse = event.Mouse(win=win)
    hide_window(win, mouse)
    desired_experiment_type = gui_get_desired_experiment_type(gui, core)
    desired_model = gui_get_desired_model(gui, core)
    design_thing, model = act_on_choices(
        desired_experiment_type, desired_model, expInfo)
    show_window(win, mouse)
    return (design_thing, model)


def hide_window(win, mouse):
    mouse.setVisible(1)  # ensure mouse is visible
    win.fullscr = False  # not sure if this is necessary
    win.winHandle.set_fullscreen(False)
    win.winHandle.minimize()
    win.flip()

def show_window(win, mouse):
    win.winHandle.maximize()
    win.winHandle.activate()
    win.fullscr=True
    win.winHandle.set_fullscreen(True)
    win.flip()
    # hide the mouse for the rest of the experiment
    mouse.setVisible(0)


def gui_get_desired_experiment_type(gui, core):
    # expt_type = {'Experiment type': ['delayed', 'risky', 'delayed and risky']}
    dlg = gui.DlgFromDict(dictionary=expt_type,
                          title='Choose your experiment type')
    if dlg.OK == False:
        core.quit()  # user pressed cancel

    desired_experiment_type = expt_type['Experiment type']
    logging.debug(desired_experiment_type)
    return desired_experiment_type



def gui_get_desired_model(gui, core):
    if expt_type['Experiment type'] in delayed_design_set:
        models_available = delay_models_available

    elif expt_type['Experiment type'] in risky_design_set:
        models_available = risky_models_available

    elif expt_type['Experiment type'] in delayed_and_risky_design_set:
        models_available = delayed_and_risky_models_available

    else:
        expt_type_value = expt_type['Experiment type']
        print(expt_type_value)
        logging.error(f'Value of experiment type ({expt_type_value}) not recognised')
        raise ValueError('Filed to identify selected experiment type')

    model_type = {'Model': models_available}
    dlg = gui.DlgFromDict(dictionary=model_type, title='Choose your model')
    if dlg.OK == False:
        core.quit()  # user pressed cancel

    desired_model = model_type['Model']
    logging.debug(desired_model)
    return desired_model


def act_on_choices(desired_experiment_type, desired_model, expInfo):

    # create desired experiment object ========================================

    if desired_experiment_type == 'delayed (Bayesian Adaptive Design)':
        from darc_toolbox.designs import BayesianAdaptiveDesignGeneratorDARC, DesignSpaceBuilder
        # regular, or magnitude effect
        if (desired_model == 'HyperbolicMagnitudeEffect') or (desired_model == 'ExponentialMagnitudeEffect'):
            D = DesignSpaceBuilder.delay_magnitude_effect().build()
            design_thing = BayesianAdaptiveDesignGeneratorDARC(D,
                max_trials=expInfo['trials'])
        else:
            D = DesignSpaceBuilder.delayed().build()
            design_thing = BayesianAdaptiveDesignGeneratorDARC(D,
                max_trials=expInfo['trials'])

        # import the appropriate set of models
        from darc_toolbox.delayed import models


    elif desired_experiment_type == 'delayed (Kirby 2009)':
        from darc_toolbox.delayed.designs import Kirby2009
        design_thing = Kirby2009()
        from darc_toolbox.delayed import models

    elif desired_experiment_type == 'delayed (Griskevicius et al, 2011)':
        from darc_toolbox.delayed.designs import Griskevicius2011
        design_thing = Griskevicius2011()
        from darc_toolbox.delayed import models

    elif desired_experiment_type == 'delayed (Frye et al, 2016)':
        from darc_toolbox.delayed.designs import Frye
        design_thing = Frye()
        from darc_toolbox.delayed import models

    elif desired_experiment_type == 'delayed (Du, Green, & Myerson, 2002)':
        from darc_toolbox.delayed.designs import DuGreenMyerson2002
        design_thing = DuGreenMyerson2002()
        from darc_toolbox.delayed import models

    elif desired_experiment_type == 'risky (Du, Green, & Myerson, 2002)':
        from darc_toolbox.risky.designs import DuGreenMyerson2002
        design_thing = DuGreenMyerson2002()
        from darc_toolbox.risky import models

    elif desired_experiment_type == 'risky (Griskevicius et al, 2011)':
        from darc_toolbox.risky.designs import Griskevicius2011
        design_thing = Griskevicius2011()
        from darc_toolbox.risky import models

    elif desired_experiment_type == 'risky (Bayesian Adaptive Design)':
        from darc_toolbox.designs import BayesianAdaptiveDesignGeneratorDARC, DesignSpaceBuilder
        # create an appropriate design object
        D = DesignSpaceBuilder.risky().build()
        design_thing = BayesianAdaptiveDesignGeneratorDARC(D,
            max_trials=expInfo['trials'])
        # import the appropriate set of models
        from darc_toolbox.risky import models

    elif desired_experiment_type == 'delayed and risky (Bayesian Adaptive Design)':
        from darc_toolbox.designs import BayesianAdaptiveDesignGeneratorDARC
        # create an appropriate design object
        D = DesignSpaceBuilder.delayed_and_risky().build()
        design_thing = BayesianAdaptiveDesignGeneratorDARC(D,
            max_trials=expInfo['trials'])
        # import the appropriate set of models
        from darc_toolbox.delayed_and_risky import models


    # chose the desired model here ============================================
    if desired_model == 'Hyperbolic':
        model = models.Hyperbolic(n_particles=expInfo['particles'])

    elif desired_model == 'Exponential':
        model = models.Exponential(n_particles=expInfo['particles'])

    elif desired_model == 'MyersonHyperboloid':
        model = models.MyersonHyperboloid(n_particles=expInfo['particles'])

    elif desired_model == 'ModifiedRachlin':
        model = models.ModifiedRachlin(n_particles=expInfo['particles'])

    elif desired_model == 'HyperbolicMagnitudeEffect':
        model = models.HyperbolicMagnitudeEffect(n_particles=expInfo['particles'])

    elif desired_model == 'ExponentialMagnitudeEffect':
        model = models.ExponentialMagnitudeEffect(
            n_particles=expInfo['particles'])

    elif desired_model == 'HyperbolicNonLinearUtility':
        model = models.HyperbolicNonLinearUtility(
            n_particles=expInfo['particles'])

    elif desired_model == 'MultiplicativeHyperbolic':
        model = models.MultiplicativeHyperbolic(
            n_particles=expInfo['particles'])

    elif desired_model == 'LinearInLogOdds':
        model = models.LinearInLogOdds(n_particles=expInfo['particles'])

    else:
        logging.error(f'Value of desired_model ({desired_model}) not recognised')
        raise ValueError('Filed to act on desired_model')


    return (design_thing, model)
