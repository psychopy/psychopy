from psychopy.data.utils import parsePipeSyntax


def makeDisplayParams(expInfo, sortKeys=True, labels=None, tooltips=None, fixed=None, order=None):
    # copy dict so nothing we do here affects it
    expInfo = expInfo.copy()
    # default blank dict for labels and tooltips
    if labels is None:
        labels = {}
    if tooltips is None:
        tooltips = {}
    # convert fixed list to pipe syntax
    if fixed is not None:
        for key in fixed:
            if key in expInfo:
                expInfo[f"{key}|fix"] = expInfo.pop(key)
    # convert order list to pipe syntax
    if order is not None:
        for key in order:
            i = order.index(key)
            if key in expInfo:
                expInfo[f"{key}|{i}"] = expInfo.pop(key)
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
        # if given a label, use it
        if key in labels:
            label = labels[key]
        # if given a tooltip, use it
        tip = ""
        if key in tooltips:
            tip = tooltips[key]
        # work out index
        i = None
        for flag in flags:
            if flag.isnumeric():
                i = int(flag)
        # construct display param
        param = {
            'key': key,
            'label': label,
            'tip': tip,
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
