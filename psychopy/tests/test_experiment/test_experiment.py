from psychopy import experiment
from psychopy.tests.utils import TESTS_DATA_PATH
from pathlib import Path
import esprima


class TestExperiment:
    def test_resources(self):
        def getResources(handled):
            """
            Get a list of resources which appear in the JS file.

            Parameters
            ----------
            handled : bool
                If True, include a Routine with a Resource Manager in.
            """
            # make experiment with handled resources
            exp = experiment.Experiment()
            exp.loadFromXML(Path(TESTS_DATA_PATH) / "test_resources.psyexp")
            # if not handled, remove handling routine
            if not handled:
                exp.flow.pop(0)
            # compile JS
            script = exp.writeScript(target="PsychoJS")
            # parse JS to get resource spec
            tree = esprima.tokenize(script)
            for i, node in enumerate(tree):
                # we're looking for the "start" call specifically
                if all((
                    node.type == "Identifier", node.value == "start",
                    tree[i-1].type == "Punctuator", tree[i-1].value == ".",
                    tree[i-2].type == "Identifier", tree[i-2].value == "psychoJS"
                )):
                    startIndex = i
                    break

            # within the start call, find the declaration of "resources"
            for i, node in enumerate(tree[startIndex:]):
                i += startIndex
                if all((
                    node.type == "Identifier", node.value == "resources",
                    tree[i+1].type == "Punctuator", tree[i+1].value == ":"
                )):
                    startIndex = i + 3
                    break
            # get everything inside resources
            resources = []
            for i, node in enumerate(tree[startIndex:]):
                # break on closing
                if node.type == "Punctuator" and node.value == "]":
                    break
                # append node
                resources.append(node.value)
            # unparse back to raw code
            resources = "".join(resources)

            return resources

        """
        Case structure
        ==============
        value : str
            Value to look for
        handled : bool
            Whether or not this value should be present when handled
        unhandled : bool
            Whether or not this value should be present when unhandled
        """
        cases = [
            # default stim should always be present
            {'value': "pavlovia.org/assets/default/default.png", 'handled': True, 'unhandled': True},
            {'value': "pavlovia.org/assets/default/default.mp3", 'handled': True, 'unhandled': True},
            {'value': "pavlovia.org/assets/default/default.mp4", 'handled': True, 'unhandled': True},
            {'value': "pavlovia.org/assets/default/creditCard.png", 'handled': True, 'unhandled': True},
            {'value': "pavlovia.org/assets/default/USB.png", 'handled': True, 'unhandled': True},
            {'value': "pavlovia.org/assets/default/USB-C.png", 'handled': True, 'unhandled': True},
            # regular stim should only be present when unhandled
            {'value': "testpixels.png", 'handled': False, 'unhandled': True},
            {'value': "testMovie.mp4", 'handled': False, 'unhandled': True},
            {'value': "Electronic_Chime-KevanGC-495939803.wav", 'handled': False, 'unhandled': True},
            # survey ID and lib should always be present
            {'value': "1906fa4a-e009-49aa-b63d-798d8bf46c22", 'handled': True, 'unhandled': True},
            {'value': "'surveyLibrary':true", 'handled': True, 'unhandled': True},
        ]

        # get resources present when handled
        handledResources = getResources(True)
        # get resources present when unhandled
        unhandledResources = getResources(False)

        for case in cases:
            # check presence in handled resources
            if case['handled']:
                assert case['value'] in handledResources
            else:
                assert case['value'] not in handledResources
            # check presence in unhandled resources
            if case['unhandled']:
                assert case['value'] in unhandledResources
            else:
                assert case['value'] not in unhandledResources

    def test_loaded_namespace(self):

        exp = experiment.Experiment()
        allRoutines = experiment.getAllStandaloneRoutines(fetchIcons=False) 

        """
        Case structure
        ==============
        file : str
            Experiment file to load
        expectedSet : Set[str]
            The expected names in the user namespace after routines are loaded and added
        names : List[str]
            Name of each routine to be added after experiment is loaded, paired with tags
        tags : List[str]
            Type of each routine to be added after experiment is loaded, paired with names
            Can be 'CounterbalanceRoutine', 'EyetrackerCalibrationRoutine', 'EyetrackerValidationRoutine'
        """

        cases = [
            {"file": "test_counterbalance.psyexp",
             "expectedSet": {'trial', 'counterbalance', 'counterbalance_2', 'counterbalance_3',
                             'counterbalance_4', 'counterbalance_5', 'calibration', 'calibration_2'},
             "names": ['counterbalance', 'counterbalance', 'calibration', 'calibration'],
             "tags": ['CounterbalanceRoutine', 'CounterbalanceRoutine', 'EyetrackerCalibrationRoutine',
                      'EyetrackerCalibrationRoutine']},
            
            {"file": "test_counterbalance.psyexp",
             "expectedSet": {'trial', 'counterbalance', 'counterbalance_2', 'counterbalance_3',
                             'calibration', 'counterbalance_4', 'calibration_2'},
             "names": ['calibration', 'counterbalance', 'calibration'],
             "tags": ['EyetrackerCalibrationRoutine', 'EyetrackerCalibrationRoutine', 'EyetrackerCalibrationRoutine']},
            
            {"file": "test_custom_missing.psyexp",
             "expectedSet": {'trial', 'custom_2', 'counterbalance_2', 'counterbalance',
                             'counterbalance_3', 'calibration', 'calibration_2'},
             "names": ['counterbalance', 'counterbalance', 'calibration', 'calibration'],
             "tags": ['CounterbalanceRoutine', 'CounterbalanceRoutine', 'EyetrackerCalibrationRoutine',
                      'EyetrackerCalibrationRoutine']},
            
            {"file": "test_missing_counterbalance.psyexp",
             "expectedSet": {'trial', 'counterbalance_2', 'counterbalance', 'counterbalance_3'},
             "names": ['counterbalance', 'counterbalance'],
             "tags": ['CounterbalanceRoutine', 'EyetrackerCalibrationRoutine']},
            
            {"file": "test_mix_exp.psyexp",
             "expectedSet": {'trial', 'counterbalance', 'calibration', 'counterbalance_2',
                             'validation', 'counterbalance_3', 'calibration_2', 'validation_2'},
             "names": ['counterbalance', 'calibration', 'validation'],
             "tags": ['CounterbalanceRoutine', 'EyetrackerCalibrationRoutine', 'EyetrackerValidationRoutine']},
            
            {"file": "test_mix_missing.psyexp",
             "expectedSet": {'trial', 'calibration_2', 'counterbalance_2', 'calibration',
                             'counterbalance', 'calibration_3', 'counterbalance_3'},
             "names": ['calibration_2', 'counterbalance_2', 'calibration', 'counterbalance'],
             "tags": ['EyetrackerCalibrationRoutine', 'CounterbalanceRoutine', 'EyetrackerCalibrationRoutine',
                      'CounterbalanceRoutine']},
            
            {"file": "test_mix_name_calibration.psyexp",
             "expectedSet": {'trial', 'calibration_2', 'custom_2', 'counterbalance_2',
                             'calibration', 'calibration_3', 'custom_3', 'custom'},
             "names": ['calibration', 'calibration', 'custom_2', 'custom'],
             "tags": ['EyetrackerCalibrationRoutine', 'CounterbalanceRoutine', 'CounterbalanceRoutine',
                      'EyetrackerCalibrationRoutine']},
        ]

        for case in cases:
            exp.loadFromXML(Path(TESTS_DATA_PATH) / "test_loaded_namespace" / case['file'])

            # add new routines to the experiment and their names to namespace
            namespace = exp.namespace
            for (name, tag) in zip(case["names"], case["tags"]):   
                routine = allRoutines[tag](exp=exp, name=name)
                rtGoodName = routine.params['name'].val = namespace.makeValid(
                    routine.params['name'].val)
                namespace.add(rtGoodName)
                exp.addStandaloneRoutine(routineName=rtGoodName, routine=routine)

            actualSet = set(namespace.user)
            expectedSet = case["expectedSet"]
            print()
            print(case['file'])
            print(actualSet)
            print(expectedSet)
            print()

            # check for no duplicate names in the namespace.user list
            assert len(actualSet) == len(expectedSet)

            # check that expected names in namespace.user list is 
            # equivalent to the actual names in namespace.user
            assert len(actualSet) == len(actualSet.intersection(expectedSet))




