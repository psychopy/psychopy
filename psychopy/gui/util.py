from psychopy.data.utils import parsePipeSyntax


def makeDisplayParams(expInfo, sortKeys=True):
    # get keys as a list
    keys = list(expInfo)
    # sort alphabetically if requested
    if sortKeys:
        keys.sort()
    # arrays for config and regular params
    sortedParams = []
    unsortedParams = []
    sortedConfig = []
    unsortedConfig = []
    # iterate through keys
    for key in keys:
        # parse key
        label, flags = parsePipeSyntax(key)
        # work out index
        i = None
        for flag in flags:
            if flag.isnumeric():
                i = int(flag)
        # construct display param
        param = {
            'key': key,
            'label': label,
            'value': expInfo[key],
            'required': "req" in flags,
            'fixed': "fix" in flags,
            'index': i,
        }
        # decide which list to add to
        if "cfg" in flags and i is not None:
            sortedConfig.append(param)
        elif "cfg" in flags:
            unsortedConfig.append(param)
        elif i is not None:
            sortedParams.append(param)
        else:
            unsortedParams.append(param)
    # sort the sorted params/config by index
    sortedParams.sort(key=lambda x: x['index'])
    sortedConfig.sort(key=lambda x: x['index'])
    # return all params and configs
    if len(sortedConfig + unsortedConfig):
        # return with readmore line if there are configs
        return sortedParams + unsortedParams + ["---"] + sortedConfig + unsortedConfig
    else:
        # return without if there aren't
        return sortedParams + unsortedParams
