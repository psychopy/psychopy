/**
 * String component of psychoJS
 * 
 * 
 * This file is part of the psychoJS javascript engine of PsychoPy.
 * Copyright (c) 2016 Ilixa Ltd. (www.ilixa.com)
 * 
 * Distributed under the terms of the GNU General Public License (GPL).
 */


if (!String.prototype.format) {
  String.prototype.format = function() {
    var args = arguments;
    return this
		.replace(/{(\d+)}/g, function(match, number) { 
			return typeof args[number] != 'undefined'
			? args[number]
			: match
			;
		})
		.replace(/{([$_a-zA-Z][$_a-zA-Z0-9]*)}/g, function(match, name) {
			//console.log("n=" + name + " args[0][name]=" + args[0][name]);
			return args.length > 0 &&  args[0][name] !== undefined
			? args[0][name]
			: match
			;
		});
  };
}


/**
 * Returns the value associated with the key name in the attribs associative array, or a default value.
 * @param {Object} attribs the associative array.
 * @param {string} name the key.
 * @param def the default value.
 */
getAttrib = function(attribs, name, def) {
	if (!attribs) return def;
	
	var val = attribs[name];
	return val ? val : def;
}


/**
 * Converts a value to an array containing two instances of the value if the value is not an array.
 * @param value a float or an array.
 * @return an array of 2 values.
 */
psychoJS.val2array = function(value) {
	if (value instanceof Array) {
		return value;
	}
	else {
		return [value, value];
	}
}
	
	
/**
 * Converts a value to a string representation.
 */
str = JSON.stringify;


/**
 * Tests if x is an 'empty' value.
 * @param x the value to test
 * @return true if x one of the following: undefined, [], [undefined]
 */
isEmpty = function(x) {
	if (x === undefined) return true;
	if (! (x instanceof Array)) return false;
	if (x.length == 0) return true;
	if (x.length == 1 && x[0] === undefined) return true;
	return false;
}


createHtml = function(htmlCode) {
	var fragment = document.createDocumentFragment();
	var element = document.createElement('div');
	element.innerHTML = htmlCode;
	while (element.firstChild) {
		fragment.appendChild(element.firstChild);
	}
	return fragment;
}