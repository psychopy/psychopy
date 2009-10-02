def testExperiment_SaveLoadCompile():
    from psychopy.builder import experiment
    exp = experiment.Experiment()
    #add some routines etc
    exp.AddRoutine('instructions')
    exp.routines['instructions'].AddComponent(
    exp.Add