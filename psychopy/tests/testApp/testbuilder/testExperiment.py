

def testExperiment_SaveLoadCompile():
    import psychopy.app.builder.experiment
    exp = psychopy.app.builder.experiment.Experiment()
    #add some routines etc
    exp.addRoutine('instructions')
#    exp.routines['instructions'].AddComponent(
#    exp.Add