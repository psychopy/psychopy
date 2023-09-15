# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import importlib
import socket
import os
import numbers  # numbers.Integral is like (int, long) but supports Py3
from psychopy import colors
from psychopy.tools import arraytools
from ..util import yload, yLoader, module_directory, getSupportedConfigSettings
from ..errors import print2err

# Takes a device configuration yaml dict and processes it based on the devices
# support_settings_values.yaml (which must be in the same directory as the
# Device class) to ensure all entries for the device setting are valid values.

class ValidationError(Exception):
    """Base class for exceptions in this module."""
    pass


class BooleanValueError(ValidationError):
    """Exception raised for errors when a bool was expected for the settings
    parameter value.

    Attributes:
        device_config_setting_name -- The name of the Device configuration parameter that has the error.
        value_given  -- the value read from the experiment configuration file.
        msg -- explanation of the error

    """

    def __init__(self, device_param_name, value_given):
        self.msg = 'A bool value is required for the given Device configuration parameter'
        self.device_config_param_name = device_param_name
        self.value_given = value_given

    def __str__(self):
        return '\n{0}:\n\tmsg: {1}\n\tparam_name: {2}\n\tvalue: {3}\n'.format(
            self.__class__.__name__, self.msg, self.device_config_param_name, self.value_given)


class StringValueError(ValidationError):
    """Exception raised for errors when a str was expected for the settings
    parameter value.

    Attributes:
        device_config_param_name -- The name of the Device configuration parameter that has the error.
        value_given  -- the value read from the experiment configuration file.
        device_config_param_constraints  -- the set of constraints that apply to the parameter.
        msg -- explanation of the error
    """

    def __init__(
            self,
            device_config_param_name,
            value_given,
            device_config_param_constraints):
        self.msg = 'A str value is required for the given Device configuration parameter that meets the specified constraints'
        self.device_config_param_name = device_config_param_name
        self.value_given = value_given
        self.device_config_param_constraints = device_config_param_constraints

    def __str__(self):
        return '\n{0}:\n\tmsg: {1}\n\tparam_name: {2}\n\tvalue: {3}\n'.format(
            self.__class__.__name__, self.msg, self.device_config_param_name, self.value_given)


class FloatValueError(ValidationError):
    """Exception raised for errors when a float was expected for the settings
    parameter value.

    Attributes:
        device_config_param_name -- The name of the Device configuration parameter that has the error.
        value_given  -- the value read from the experiment configuration file.
        device_config_param_constraints  -- the set of constraints that apply to the parameter.
        msg -- explanation of the error

    """

    def __init__(
            self,
            device_config_param_name,
            value_given,
            device_config_param_constraints):
        self.msg = 'A float value is required for the given Device configuration parameter that meets the specified constraints'
        self.device_config_param_name = device_config_param_name
        self.value_given = value_given
        self.device_config_param_constraints = device_config_param_constraints

    def __str__(self):
        return '\n{0}:\n\tmsg: {1}\n\tparam_name: {2}\n\tvalue: {3}\n'.format(
            self.__class__.__name__, self.msg, self.device_config_param_name, self.value_given)


class IntValueError(ValidationError):
    """Exception raised for errors when an int was expected for the settings
    parameter value.

    Attributes:
        device_config_param_name -- The name of the Device configuration parameter that has the error.
        value_given  -- the value read from the experiment configuration file.
        device_config_param_constraints  -- the set of constraints that apply to the parameter.
        msg -- explanation of the error

    """

    def __init__(
            self,
            device_config_param_name,
            value_given,
            device_config_param_constraints):
        self.msg = 'An int value is required for the given Device configuration parameter that meets the specified constraints'
        self.device_config_param_name = device_config_param_name
        self.value_given = value_given
        self.device_config_param_constraints = device_config_param_constraints

    def __str__(self):
        return '\n{0}:\n\tmsg: {1}\n\tparam_name: {2}\n\tvalue: {3}\n'.format(
            self.__class__.__name__, self.msg, self.device_config_param_name, self.value_given)


class NumberValueError(ValidationError):
    """Exception raised for errors when an int OR float was expected for the
    settings parameter value.

    Attributes:
        device_config_param_name -- The name of the Device configuration parameter that has the error.
        value_given  -- the value read from the experiment configuration file.
        device_config_param_constraints  -- the set of constraints that apply to the parameter.
        msg -- explanation of the error

    """

    def __init__(
            self,
            device_config_param_name,
            value_given,
            device_config_param_constraints):
        self.msg = 'An int or float value is required for the given Device configuration parameter that meets the specified constraints'
        self.device_config_param_name = device_config_param_name
        self.value_given = value_given
        self.device_config_param_constraints = device_config_param_constraints

    def __str__(self):
        return '\n{0}:\n\tmsg: {1}\n\tparam_name: {2}\n\tvalue: {3}\n'.format(
            self.__class__.__name__, self.msg, self.device_config_param_name, self.value_given)


class IpValueError(ValidationError):
    """Exception raised for errors when an IP address was expected for the
    settings parameter value.

    Attributes:
        device_config_param_name -- The name of the Device configuration parameter that has the error.
        value_given  -- the value read from the experiment configuration file.
        msg -- explanation of the error

    """

    def __init__(self, device_config_param_name, value_given):
        self.msg = 'An IP address value is required for the given Device configuration parameter.'
        self.device_config_param_name = device_config_param_name
        self.value_given = value_given

    def __str__(self):
        return '\n{0}:\n\tmsg: {1}\n\tparam_name: {2}\n\tvalue: {3}\n'.format(
            self.__class__.__name__, self.msg, self.device_config_param_name, self.value_given)


class ColorValueError(ValidationError):
    """Exception raised for errors when a color was expected for the settings
    parameter value.

    Attributes:
        device_config_param_name -- The name of the Device configuration parameter that has the error.
        value_given  -- the value read from the experiment configuration file.
        msg -- explanation of the error

    """

    def __init__(self, device_config_param_name, value_given):
        self.msg = 'A color value is required for the given Device configuration parameter.'
        self.device_config_param_name = device_config_param_name
        self.value_given = value_given

    def __str__(self):
        return '\n{0}:\n\tmsg: {1}\n\tparam_name: {2}\n\tvalue: {3}\n'.format(
            self.__class__.__name__, self.msg, self.device_config_param_name, self.value_given)


class DateStringValueError(ValidationError):
    """Exception raised for errors when a date string was expected for the
    settings parameter value.

    Attributes:
        device_config_param_name -- The name of the Device configuration parameter that has the error.
        value_given  -- the value read from the experiment configuration file.
        msg -- explanation of the error

    """

    def __init__(self, device_config_param_name, value_given):
        self.msg = 'A date string value is required for the given Device configuration parameter.'
        self.device_config_param_name = device_config_param_name
        self.value_given = value_given

    def __str__(self):
        return '\n{0}:\n\tmsg: {1}\n\tparam_name: {2}\n\tvalue: {3}\n'.format(
            self.__class__.__name__, self.msg, self.device_config_param_name, self.value_given)


class NonSupportedValueError(ValidationError):
    """Exception raised when the configuration value provided does not match
    one of the possible valid Device configuration parameter values.

    Attributes:
        device_config_setting_name -- The name of the Device configuration parameter that has the error.
        value_given  -- the value read from the experiment configuration file.
        valid_values  -- the valid options for the configuration setting.
        msg -- explanation of the error

    """

    def __init__(self, device_param_name, value_given, valid_values):
        self.msg = 'A the provided value is not supported for the given Device configuration parameter'
        self.device_config_param_name = device_param_name
        self.value_given = value_given
        self.valid_values = valid_values

    def __str__(self):
        return '\n{0}:\n\tmsg: {1}\n\tparam_name: {2}\n\tvalue: {3}\n\tconstraints: {4}'.format(
            self.__class__.__name__,
            self.msg,
            self.device_config_param_name,
            self.value_given,
            self.valid_values)

MIN_VALID_STR_LENGTH = 1
MAX_VALID_STR_LENGTH = 1024

MIN_VALID_FLOAT_VALUE = 0.0
MAX_VALID_FLOAT_VALUE = 1000000.0

MIN_VALID_INT_VALUE = 0
MAX_VALID_INT_VALUE = 1000000

def is_sequence(arg):
    return hasattr(arg, "__getitem__") or hasattr(arg, "__iter__")

def isValidColor(config_param_name, color, constraints):
    """
    Return color if it is a valid psychopy color (regardless of color space)
    , otherwise raise error. Color value can be in hex, name, rgb, rgb255 format.
    """
    if isinstance(color, str):
        if color[0] == '#' or color[0:2].lower() == '0x':
            rgb255color = colors.hex2rgb255(color)
            if rgb255color is not None:
                return color
            else:
                raise ColorValueError(config_param_name, color)

        if color.lower() in colors.colorNames.keys():
            return color
        else:
            raise ColorValueError(config_param_name, color)
    if isinstance(color, (float, int)) or (is_sequence(color) and len(color) == 3):
        colorarray = arraytools.val2array(color, length=3)
        if colorarray is not None:
            return color
        else:
            raise ColorValueError(config_param_name, color)
    raise ColorValueError(config_param_name, color)

def isValidString(config_param_name, value, constraints):
    if isinstance(value, str):
        if value == constraints:
            # static string
            return value
        constraints.setdefault('min_length', MIN_VALID_STR_LENGTH)
        constraints.setdefault('max_length', MAX_VALID_STR_LENGTH)
        constraints.setdefault('first_char_alpha', False)
        min_length = int(constraints.get('min_length'))
        max_length = int(constraints.get('max_length'))
        first_char_alpha = bool(constraints.get('first_char_alpha'))

        if len(value) >= min_length:
            if len(value) <= max_length:
                if first_char_alpha is True and value[0].isalpha() is False:
                    raise StringValueError(
                        config_param_name, value, constraints)
                else:
                    return value

    elif int(constraints.get('min_length')) == 0 and value is None:
        return value

    raise StringValueError(config_param_name, value, constraints)


def isValidFloat(config_param_name, value, constraints):
    if isinstance(value, float):
        constraints.setdefault('min', MIN_VALID_FLOAT_VALUE)
        constraints.setdefault('max', MAX_VALID_FLOAT_VALUE)
        minv = float(constraints.get('min'))
        maxv = float(constraints.get('max'))

        if value >= minv:
            if value <= maxv:
                return value

    raise FloatValueError(config_param_name, value, constraints)


def isValidInt(config_param_name, value, constraints):
    if isinstance(value, numbers.Integral):
        constraints.setdefault('min', MIN_VALID_INT_VALUE)
        constraints.setdefault('max', MAX_VALID_INT_VALUE)
        minv = int(constraints.get('min'))
        maxv = int(constraints.get('max'))

        if value >= minv:
            if value <= maxv:
                return value

    raise IntValueError(config_param_name, value, constraints)

def isBool(config_param_name, value, valid_value):
    try:
        value = bool(value)
        return value
    except Exception:
        raise BooleanValueError(config_param_name, value)


def isValidIpAddress(config_param_name, value, valid_value):
    try:
        socket.inet_aton(value)
        return value
    except Exception:
        raise IpValueError(config_param_name, value)


def isValidList(config_param_name, value, constraints):
    try:
        min_length = constraints.get('min_length', 1)
        max_length = constraints.get('max_length', 128)

        if min_length == 0 and value is None or value == 'None':
            return value

        valid_values = constraints.get('valid_values', [])

        if len(valid_values) == 0:
            return value

        if not isinstance(value, (list, tuple)):
            if value not in valid_values:
                raise NonSupportedValueError(
                    config_param_name, value, constraints)
            elif min_length in [0, 1]:
                return value

        current_length = len(value)

        if current_length < min_length or current_length > max_length:
            raise NonSupportedValueError(config_param_name, value, constraints)

        for v in value:
            if v not in valid_values:
                raise NonSupportedValueError(config_param_name, v, valid_values)

        return value

    except Exception:
        raise NonSupportedValueError(config_param_name, value, constraints)


def isValueValid(config_param_name, value, valid_values):
    if isinstance(value, (list, tuple)):
        for v in value:
            if v not in valid_values:
                raise NonSupportedValueError(config_param_name, value, valid_values)
    elif value not in valid_values:
        raise NonSupportedValueError(config_param_name, value, valid_values)
    return value

CONFIG_VALIDATION_KEY_WORD_MAPPINGS = dict(
    IOHUB_STRING=isValidString,
    IOHUB_BOOL=isBool,
    IOHUB_FLOAT=isValidFloat,
    IOHUB_INT=isValidInt,
    IOHUB_LIST=isValidList,
    IOHUB_COLOR=isValidColor,
    IOHUB_IP_ADDRESS_V4=isValidIpAddress)
###############################################

_current_dir = module_directory(isValidString)


def buildConfigParamValidatorMapping(
        device_setting_validation_dict,
        param_validation_func_mapping,
        parent_name):
    for param_name, param_config in device_setting_validation_dict.items():
        current_param_path = None
        if parent_name is None:
            current_param_path = param_name
        else:
            current_param_path = '%s.%s' % (parent_name, param_name)

        keyword_validator_function = None
        if isinstance(param_name, str):
            keyword_validator_function = CONFIG_VALIDATION_KEY_WORD_MAPPINGS.get(
                param_name, None)

        if keyword_validator_function:
            param_validation_func_mapping[
                parent_name] = keyword_validator_function, param_config
            #print2err('ADDED MAPPING1: ', current_param_path, " ", isValueValid, " ", param_config)
        elif isinstance(param_config, str):
            keyword_validator_function = CONFIG_VALIDATION_KEY_WORD_MAPPINGS.get(
                param_config, None)
            if keyword_validator_function:
                param_validation_func_mapping[
                    current_param_path] = keyword_validator_function, {}
                #print2err('ADDED MAPPING2: ', current_param_path, " ", isValueValid, " ", param_config)
            else:
                param_validation_func_mapping[
                    current_param_path] = isValueValid, [param_config, ]
                #print2err('ADDED MAPPING3: ', current_param_path, " ", isValueValid, " ", param_config)
        elif isinstance(param_config, dict):
            buildConfigParamValidatorMapping(
                param_config,
                param_validation_func_mapping,
                current_param_path)
        elif isinstance(param_config, (list, tuple)):
            param_validation_func_mapping[
                current_param_path] = isValueValid, param_config
            #print2err('ADDED MAPPING4: ', current_param_path, " ", isValueValid, " ", param_config)
        else:
            param_validation_func_mapping[
                current_param_path] = isValueValid, [param_config, ]
            #print2err('ADDED MAPPING5: ', current_param_path, " ", isValueValid, " ", param_config)


def validateConfigDictToFuncMapping(
        param_validation_func_mapping,
        current_device_config,
        parent_param_path):
    validation_results = dict(errors=[], not_found=[])
    for config_param, config_value in current_device_config.items():
        if parent_param_path is None:
            current_param_path = config_param
        else:
            current_param_path = '%s.%s' % (parent_param_path, config_param)

        param_validation = param_validation_func_mapping.get(
            current_param_path, None)
        if param_validation:
            param_validation_func, constraints = param_validation
            try:
                param_value = param_validation_func(
                    current_param_path, config_value, constraints)
                current_device_config[config_param] = param_value
#                print2err("PARAM {0}, VALUE {1} is VALID.".format(current_param_path,param_value))
            except ValidationError:
                validation_results['errors'].append(
                    (config_param, config_value))
                #print2err("Device Config Validation Error: param: {0}, value: {1}\nError: {2}".format(config_param,config_value,e))

        elif isinstance(config_value, dict):
            validateConfigDictToFuncMapping(
                param_validation_func_mapping,
                config_value,
                current_param_path)
        else:
            validation_results['not_found'].append(
                (config_param, config_value))
    return validation_results


def validateDeviceConfiguration(
        relative_module_path,
        device_class_name,
        current_device_config):
    """Validate the device configuration settings provided.
    """
    validation_module = importlib.import_module(relative_module_path)
    validation_file_path = getSupportedConfigSettings(validation_module)

    # use a default config if we can't get the YAML file
    if not os.path.exists(validation_file_path):
        validation_file_path = os.path.join(
            _current_dir, 
            relative_module_path[len('psychopy.iohub.devices.'):].replace(
                '.', os.path.sep),
        'supported_config_settings.yaml')

    device_settings_validation_dict = yload(
        open(validation_file_path, 'r'), Loader=yLoader)
    device_settings_validation_dict = device_settings_validation_dict[
        list(device_settings_validation_dict.keys())[0]]

    param_validation_func_mapping = dict()
    parent_config_param_path = None
    buildConfigParamValidatorMapping(
        device_settings_validation_dict, 
        param_validation_func_mapping,
        parent_config_param_path)

    validation_results = validateConfigDictToFuncMapping(
        param_validation_func_mapping, current_device_config, None)

    return validation_results
