/**
 * Visual component of psychoJS
 *
 *
 * This file is part of the PsychoJS javascript engine of PsychoPy.
 * Copyright (c) 2016 Ilixa Ltd. (www.ilixa.com)
 *
 * Distributed under the terms of the GNU General Public License (GPL).
 */


/**
 * @namespace
 */
psychoJS.visual = {};
psychoJS.core.openWindows = [];

/**
 * Utility function. Sets the value of an object's attribute.
 * @param obj the object posessing the attribute
 * @param attrib the attribute's name
 * @param value the value the object's attribute will take
 * @param log if true will log the operation
 * @param stealth not used for the moment
 */
psychoJS.attributeSet = function(obj, attrib, value, log, stealth) {
	if (!stealth && (log || obj.autoLog)) {
		var message = obj.name + ": " + attrib + " = " + JSON.stringify(value);
		try {
			obj.win.logOnFlip(message, psychoJS.logging.EXP, obj);
		}
		catch (e) {
			psychoJS.logging.log(message, psychoJS.logging.EXP, obj);
		}
	}

	obj[attrib] = value;
}

/**
 * Used to set up a context in which to draw objects.
 * @constructor
 */
psychoJS.visual.Window = function(attribs) {
	this.dim = psychoJS.getAttrib(attribs, 'dim');
	this._units = psychoJS.getAttrib(attribs, 'units', 'norm');
	this._fullscr = psychoJS.getAttrib(attribs, 'fullscr');

	this._renderer = PIXI.autoDetectRenderer(800, 600, {backgroundColor:0x00000});

	this._renderer.view.style["transform"] = "translatez(0)"; // what does this do?
	document.body.appendChild(this._renderer.view);
	this._renderer.view.style.position = "absolute";
	this._container = new PIXI.Container();
	//psychoJS.onResize(this._renderer, this.stats, this._container);

	if (psychoJS.debug) {
		this.stats = new Stats();
		document.body.appendChild(this.stats.domElement);
		this.stats.domElement.style.position = "absolute";
		this.stats.domElement.style.top = "0px";
	}

	this._drawList = []; // list of all elements, in the order they are currently drawn

	this._logMessagesOnFlip = [];

	this.setUnits = function(value) {
		this._units = value;
	}

	Object.defineProperty(this, 'units', {
		configurable: true,
		get : function() { return this._units; },
		set : function(value) { this.setUnits(value); }
	});

	Object.defineProperty(this, 'size', {
		configurable: true,
		get : function() { return [this._renderer.width, this._renderer.height]; },
		set : function(value) { /* read only */ }
	});

	psychoJS.core.openWindows.push(this);

	this._renderer.view.addEventListener("mousedown", psychoJS.event._onMouseDown, false);
	this._renderer.view.addEventListener("mouseup", psychoJS.event._onMouseUp, false);
	this._renderer.view.addEventListener("mousemove", psychoJS.event._onMouseMove, false);
	this._renderer.view.addEventListener("mousewheel", psychoJS.event._onMouseWheel, false);
}



/**
 * "Closes" the window. This actually only removes the canvas used to render components.
 */
psychoJS.visual.Window.prototype.close = function() {
	document.body.removeChild(this._renderer.view);
}

/**
 * Recomputes the window's _drawList and _container children for the next animation frame.
 */
psychoJS.visual.Window.prototype._refresh = function() {
	var newDrawList = [];
	for(var i = 0; i < this._drawList.length; ++i) {
		var stim = this._drawList[i];
		if (!stim.autoDraw) {
			this._container.removeChild(stim.pixiRep);
		}
		else {
			newDrawList.push(stim);
			if (stim._updateIfNeeded && stim._needUpdate) {
				console.log(stim.name + " needs udate");
				this._container.removeChild(stim.pixiRep);
				stim._updateIfNeeded(); // TODO: testing the presence of the method not useful once it's in a base class
				this._container.addChild(stim.pixiRep);
			}
		}
	}
	this._drawList = newDrawList;
}

/**
 * Measures the actual fps for the screen.
 * Currently unimplemented - always returns 60.
 * @param autoDraw
 */
psychoJS.visual.Window.prototype.getActualFrameRate = function() {
	// TODO
	return 60.0;
}

/**
 * Send a log message that should be time-stamped at the next requestAnimationFrame call.
 * @param {String} msg the message to be logged
 * @param {number} level the level of importance for the message
 * @param {object} obj (optional) the object that might be associated with this message if desired
 */
psychoJS.visual.Window.prototype.logOnFlip = function(msg, level, obj) {
	this._logMessagesOnFlip.push({msg:msg, level:level, obj:obj});
}

psychoJS.visual.Window.prototype._writeLogOnFlip = function() {
	var logTime = psychoJS.core.getTime();
	for(var i = 0; i < this._logMessagesOnFlip.length; ++i) {
		var entry = this._logMessagesOnFlip[i];
		psychoJS.logging.log(entry.msg, entry.level, logTime, entry.obj);
	}

	this._logMessagesOnFlip = [];
}

/**
 * Non-visual methods and attributes for BaseVisualStim.
 * Includes: name, autoDraw, autoLog.
 * @constructor
 * @param {Object} attribs Associative array used to store the following parameters:
 * @param {String} attribs.name String or undefined. The name of the object to be using during logged messages about this stim. If you have multiple stimuli in your experiment this really helps to make sense of log files!
 * @param {String} attribs.autoDraw Determines whether the stimulus should be automatically drawn on every frame flip.
 * @param {boolean} attribs.autoLog Whether every change in this stimulus should be auto logged.
 */
psychoJS.visual.MinimalStim = function(attribs) {

	this._name = psychoJS.getAttrib(attribs, 'name', "");
	this._autoDraw = psychoJS.getAttrib(attribs, 'autoDraw', false);
	this._autoLog = psychoJS.getAttrib(attribs, 'autoLog', false);

	Object.defineProperty(this, 'name', {
		configurable: true,
		get : function() { return this._name; },
		set : function(name) { this._name = name; }
	});

	Object.defineProperty(this, 'autoDraw', {
		configurable: true,
		get : function() { return this._autoDraw; },
		set : function(autoDraw) { this.setAutoDraw(autoDraw); }
	});

	Object.defineProperty(this, 'autoLog', {
		configurable: true,
		get : function() { return this._autoLog; },
		set : function(autoLog) { this.setAutoLog(autoLog); }
	});
}

/**
 * Sets autoDraw
 * @param autoDraw
 */
psychoJS.visual.MinimalStim.prototype.setAutoDraw = function(autoDraw) {
	this._updateIfNeeded();

	this._autoDraw = autoDraw;
	if (this._autoDraw) {
		if (this.win) {
			if (this.win._drawList.indexOf(this) < 0) {
				if (this.pixiRep) {
					this.win._container.addChild(this.pixiRep);
					this.win._drawList.push(this);
				}
				else {
					if (psychoJS.debug) console.log("autoDraw true for " + this + " but pixiRep undefined");
				}
			}
		}
		this.status = psychoJS.STARTED;
	}
	else {
		if (this.win) {
			var index = this.win._drawList.indexOf(this);
			if (index >= 0 && this.pixiRep) {
				this.win._container.removeChild(this.pixiRep);
				this.win._drawList.splice(index, 1); // remove from list
			}
		}
		this.status = psychoJS.STOPPED;
	}
}

/**
 * Draws this component on the next frame draw.
 */
psychoJS.visual.MinimalStim.prototype.draw = function() {
	this._updateIfNeeded();

	if (this.win && this.win._drawList.indexOf(this) < 0) {
		this.win._container.addChild(this.pixiRep);
		this.win._drawList.push(this);
	}
}

/**
 * Whether every change in this stimulus should be auto logged.
 * Value should be: `true` or `false`. Set to `false` if your
 * stimulus is updating frequently (e.g. updating its position every
 * frame) and you want to avoid swamping the log file with
 * messages that aren't likely to be useful.
 * @param autoLog true to log, false not to log
 */
psychoJS.visual.MinimalStim.prototype.setAutoLog = function(autoLog) {
	this._autoLog = autoLog;
}


/**
 * A template for a visual stimulus class.
 * @constructor
 * @param {Object} attribs Associative array used to store the following parameters:
 * @param {Object} attribs.win Window in which this stimulus is displayed.
 * @param {Array} attribs.size Size of the stimulus.
 * @param {number} attribs.opacity Determines how visible the stimulus is relative to background.
 * @param {Array} attribs.pos Position of the stimulus in the Window.
 */
psychoJS.visual.BaseVisualStim = function(attribs) {

	this._autoLog = false;
	this.win = psychoJS.getAttrib(attribs, 'win');

	// units?
	this._rotationMatrix = [[1, 0], [0, 1]];
	this._size = psychoJS.getAttrib(attribs, 'size');
	this._ori = psychoJS.getAttrib(attribs, 'ori', 0);
	this._opacity = psychoJS.getAttrib(attribs, 'opacity', 1.0);
	this._pos = psychoJS.getAttrib(attribs, 'pos', [0, 0]);

	psychoJS.visual.MinimalStim.call(this, attribs);

	Object.defineProperty(this, 'ori', {
		configurable: true,
		get : function() { return this._ori; },
		set : function(value) { this.setOri(value); }
	});

	Object.defineProperty(this, 'size', {
		configurable: true,
		get : function() { return this._size; },
		set : function(value) { this.setSize(psychoJS.val2array(value)); }
	});

	Object.defineProperty(this, 'pos', {
		configurable: true,
		get : function() { return this._pos; },
		set : function(value) { this.setPos(value); }
	});

	Object.defineProperty(this, 'opacity', {
		configurable: true,
		get : function() { return this._opacity; },
		set : function(value) { this.setOpacity(value); }
	});


	this._needUpdate = true;
	this._needVertexUpdate = true;
}

psychoJS.visual.BaseVisualStim.prototype = Object.create(psychoJS.visual.MinimalStim.prototype);


/**
 * Sets the orientation of the stimulus (in degrees).
 * @param {float} value Orientation convention is like a clock: 0 is vertical, and positive values rotate clockwise. Beyond 360 and below zero values wrap appropriately.
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.BaseVisualStim.prototype.setOri = function(value, log) {
	psychoJS.attributeSet(this, "_ori", value, log);

	var radians = value * 0.017453292519943295;
	this._rotationMatrix = [[Math.cos(radians), -Math.sin(radians)],
							[Math.sin(radians), Math.cos(radians)]];
	this._needVertexUpdate = true ; // need to update update vertices
	this._needUpdate = true;
}

/**
 * Sets the size (width, height) of the stimulus in the stimulus units.
 * @param {Array} value size of the stimulus. Size can be negative (causing a mirror-image reversal) and can extend beyond the window.
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.BaseVisualStim.prototype.setSize = function(value, log) {
	psychoJS.attributeSet(this, "_size", value, log);

	this._needVertexUpdate = true ; // need to update update vertices
	this._needUpdate = true;
}

/**
 * Sets position of the center of the stimulus in the stimulus in the stimulus units.
 * @param {Array} value position of the stimulus.
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.BaseVisualStim.prototype.setPos = function(value, log) {
	psychoJS.attributeSet(this, "_pos", value, log);

	this._needVertexUpdate = true ; // need to update update vertices
	this._needUpdate = true;
}

/**
 * Determines how visible the stimulus is relative to background
 * @param {float} value should range between 1.0 (opaque) and 0.0 (transparent).
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.BaseVisualStim.prototype.setOpacity = function(value, log) {
	psychoJS.attributeSet(this, "_opacity", value, log);

	this._needUpdate = true;
}

/**
 * Utility function. Converts a color in colorSpace to a RGB triplet.
 * @param {object} color the color as a string, array or integer.
 * @param {String} colorSpace the color space
 * @return the RGB value as a triplet of components with value ranging from -1 to 1.
 */
psychoJS.visual.getRGB = function(color, colorSpace) {
	colorSpace = colorSpace || 'rgb';

	if (typeof(color) === "string") {
		color = color.toLowerCase();

		if (color[0] === '#' || color.indexOf('Ox')>=0) {
			return hex2rgb(color);
		}
		else {
			var rgb = psychoJS.colors[color];
//			console.log("in getRGB got from dict: " + JSON.stringify(rgb));
			if (rgb) {
				return rgb;
			}
			else {
				throw "psychoJS can't interpret the color string '" + color + "'";
			}
		}
	}
	else if (color instanceof Array) {
		if (color.length == 3) {
			if (colorSpace === 'rgb255') {
				return [color[0]/127.5-1, color[1]/127.5-1, color[2]/127.5-1];
			}
			else if (colorSpace === 'hsv') {
				return psychoJS.hsvToRgb(color);
			}
			else { // assume the colorSpace is 'rgb'
				return color;
			}
		}
		else {
			throw "color array length is not 3.";
		}
	}
	else if (typeof(color) === "number") {
		return [color, color, color];
	}
	else {
		return [0, 0, 0];
	}
}

/**
 * Implementation notice:
 * Equivalent of psychoPY's ColorMixin.
 * Functional Mixin as seen here: https://javascriptweblog.wordpress.com/2011/05/31/a-fresh-look-at-javascript-mixins/
 *
 * Color and contrast related attributes and methods.
 */
psychoJS.visual.asColor = function() {
	Object.defineProperty(this, 'color', {
		configurable: true,
		get : function() { return this._color; },
		set : function(value) { this.setColor(value); }
	});
	Object.defineProperty(this, 'colorSpace', {
		configurable: true,
		get : function() { return this._colorSpace; },
		set : function(value) { this.setColorSpace(value); }
	});
	Object.defineProperty(this, 'contrast', {
		configurable: true,
		get : function() { return this._contrast; },
		set : function(value) { this.setContrast(value); }
	});

	this.setColor = function(value, colorSpace, log) {
		psychoJS.attributeSet(this, "_color", value, log);
		psychoJS.attributeSet(this, "_colorSpace", colorSpace, log);

		this._rgb = psychoJS.visual.getRGB(this._color, this._colorSpace);

//		console.log("setColor color=" + JSON.stringify(this._color) + " rgb=" + JSON.stringify(this._rgb));
		this._needUpdate = true;
	};

	this.setColorSpace = function(value, log) {
		psychoJS.attributeSet(this, "_colorSpace", value, log);

		this._needUpdate = true;
	};

	this.setContrast = function(value, log) {
		psychoJS.attributeSet(this, "_contrast", value, log);

		this._needUpdate = true;
	};

	/**
	 * Convert color to RGB while adding contrast. Requires self.rgb, self.colorSpace and self.contrast
	 */
	this._getDesiredRGB = function(rgb, colorSpace, contrast) {
		// TODO: not sure what this is meant to do:
		// Ensure that we work on 0-centered color (to make negative contrast
        // values work)
// 		 if (['rgb', 'dkl', 'lms', 'hsv'].indexOf(colorSpace) < 0) {
//             rgb = (rgb / 255.0) * 2 - 1;
// 		 }

		var desiredRGB = [
			(rgb[0] * contrast + 1) / 2.0,
			(rgb[1] * contrast + 1) / 2.0,
			(rgb[2] * contrast + 1) / 2.0 ];

		return desiredRGB

	}


}


/**
 * Implementation notice:
 * Equivalent of psychoPY's WindowMixin.
 * Functional Mixin as seen here: https://javascriptweblog.wordpress.com/2011/05/31/a-fresh-look-at-javascript-mixins/
 *
 * Window-related attributes and methods.
 */
psychoJS.visual.asWindowRelated = function() {
	Object.defineProperty(this, 'units', {
		configurable: true,
		get : function() { return this._color; },
		set : function(value) { this.setUnits(value); }
	});

	this.setUnits = function(value, log) {
		this._units = value || this.win.units;
	}

	/**
	 * sets posVar.x and posVar.y after converting pos to pixel values after taking units into account
	 */
	this._setPosPix = function(posVar, pos) {
		if (this._units === 'pix') {
			posVar.x = pos[0];
			posVar.y = pos[1];
		}
		else if (this._units === undefined || this._units === 'norm') {
			var winSize = this.win.size;
			posVar.x = pos[0] * winSize[0]/2;
			posVar.y = pos[1] * winSize[1]/2;
		}
		else if (this._units === 'height') {
			var winHeight = this.win.size[1];
			posVar.x = pos[0] * winHeight;
			posVar.y = pos[1] * winHeight;
		}
		else {
			throw 'Unit ' + this._units + ' is not implemented.';
		}
	}

	/**
	 * returns length in pixels after taking units into account
	 */
	this._getLengthPix = function(length) {
		if (this._units === 'pix') {
			return length;
		}
		else if (this._units === undefined || this._units === 'norm') {
			var winSize = this.win.size;
			return length * winSize[1]/2; // TODO: how do we handle norm when width != height?
		}
		else if (this._units === 'height') {
			var winHeight = this.win.size[1];
			return length * winHeight;
		}
		else {
			throw 'Unit ' + this._units + ' is not implemented.';
		}
	}

	/**
	 * returns a horizontal length in pixels after taking units into account
	 */
	this._getHorLengthPix = function(length) {
		if (this._units === 'pix') {
			return length;
		}
		else if (this._units === undefined || this._units === 'norm') {
			var winSize = this.win.size;
			return length * winSize[0]/2;
		}
		else if (this._units === 'height') {
			var winHeight = this.win.size[1];
			return length * winHeight;
		}
		else {
			throw 'Unit ' + this._units + ' is not implemented.';
		}
	}

	/**
	 * returns length in units from a length in pixels
	 */
	this._getLengthUnits = function(lengthInPix) {
		if (this._units === 'pix') {
			return length;
		}
		else if (this._units === undefined || this._units === 'norm') {
			var winSize = this.win.size;
			return lengthInPix / (winSize[1]/2); // TODO: how do we handle norm when width != height?
		}
		else if (this._units === 'height') {
			var winHeight = this.win.size[1];
			return lengthInPix / winHeight;
		}
		else {
			throw 'Unit ' + this._units + ' is not implemented.';
		}
	}

}




/**
 * Circle with a given radius.
 * @constructor
 * @param {Array} attribs.size Size of the stimulus.
 * @param {number} attribs.opacity Determines how visible the stimulus is relative to background.
 * @param {Array} attribs.pos Position of the stimulus in the Window.
 */
psychoJS.visual.Circle = function(attribs) {
	psychoJS.visual.BaseVisualStim.call(this, attribs);
	psychoJS.visual.asColor.call(this);
	psychoJS.visual.asWindowRelated.call(this);

	this.win = psychoJS.getAttrib(attribs ,'win', undefined);
// 	this._color = psychoJS.getAttrib(attribs ,'color', 0xFFFFFF);
	this._lineRGB = [1, 1, 1];
	this._fillRGB = [0, 0, 0];
	this._lineColorSpace = psychoJS.getAttrib(attribs, 'lineColorSpace', 'rgb');
	this._fillColorSpace = psychoJS.getAttrib(attribs, 'fillColorSpace', 'rgb');
	this._contrast = psychoJS.getAttrib(attribs, 'contrast', 1);
	this._lineColor = psychoJS.getAttrib(attribs ,'lineColor', 'white');
	this._fillColor = psychoJS.getAttrib(attribs ,'fillColor', 'black');
	this._lineWidth = psychoJS.getAttrib(attribs ,'lineWidth', 1);

	Object.defineProperty(this, 'lineColor', {
		configurable: true,
		get : function() { return this._lineColor; },
		set : function(value) { this.setLineColor(value); }
	});

	Object.defineProperty(this, 'fillColor', {
		configurable: true,
		get : function() { return this._fillColor; },
		set : function(value) { this.setFillColor(value); }
	});

	Object.defineProperty(this, 'lineWidth', {
		configurable: true,
		get : function() { return this._lineWidth; },
		set : function(value) { this.setLineWidth(value); }
	});

}

psychoJS.visual.Circle.prototype = Object.create(psychoJS.visual.BaseVisualStim.prototype);

psychoJS.visual.Circle.prototype._updateIfNeeded = function() {
	if (this._needUpdate) {
		var lineRGB = this._getDesiredRGB(this._lineRGB, this._colorSpace, this._contrast);
		var fillRGB = this._getDesiredRGB(this._fillRGB, this._colorSpace, this._contrast);

		console.log("lineRGB = " + lineRGB + "(" + psychoJS.rgb2int(lineRGB) + ") fillRGB=" + fillRGB + "(" + psychoJS.rgb2int(fillRGB) + ")");

		this.pixiRep = new PIXI.Graphics();
		this.pixiRep.lineStyle(this._lineWidth , psychoJS.rgb2int(lineRGB), 1);
 		this.pixiRep.beginFill(psychoJS.rgb2int(fillRGB));

		this.pixiRep.drawCircle(0, 0, this._size/2);

		this.pixiRep.position.x = this._pos[0];
		this.pixiRep.position.y = this._pos[1];

		this.pixiRep.alpha = this._opacity;

		this._needUpdate = false;
	}
}

psychoJS.visual.Circle.prototype.setLineColor = function(value, colorSpace, log) {
	psychoJS.attributeSet(this, "_lineColor", value, log);
	psychoJS.attributeSet(this, "_lineColorSpace", colorSpace, log);

	this._lineRGB = psychoJS.visual.getRGB(this._lineColor, this._lineColorSpace);
	console.log("setColor lineColor=" + JSON.stringify(this._lineColor) + " rgb=" + JSON.stringify(this._lineRGB));
	this._needUpdate = true;
}

psychoJS.visual.Circle.prototype.setFillColor = function(value, colorSpace, log) {
	psychoJS.attributeSet(this, "_fillColor", value, log);
	psychoJS.attributeSet(this, "_fillColorSpace", colorSpace, log);

	this._fillRGB = psychoJS.visual.getRGB(this._fillColor, this._fillColorSpace);
	console.log("setColor fillColor=" + JSON.stringify(this._fillColor) + " rgb=" + JSON.stringify(this._fillRGB));
	this._needUpdate = true;
}

psychoJS.visual.Circle.prototype.setLineWidth = function(value, log) {
	psychoJS.attributeSet(this, "_lineWidth", value, log);

	this._needUpdate = true;
}





/**
 * Class of text stimuli to be displayed in a Window.
 * @constructor
 * @param {Object} attribs Associative array used to store the following parameters:
 * @param {Object} attribs.win the Window that should display this TextStim.
 * @param {String} attribs.name Name of this TextStim.
 * @param {Array} attribs.size Size of the stimulus.
 * @param {number} attribs.opacity Determines how visible the stimulus is relative to background.
 * @param {Array} attribs.pos Position of the stimulus in the Window.
 * @param {number} attribs.contrast Contrast of this TextStim.
 * @param {Object} attribs.color Color of this TextStim.
 * @param {String} attribs.colorSpace ColorSpace of this ImageStim.
 * @param {String} attribs.text Text of this TextStim.
 * @param {String} attribs.font Font of this TextStim.
 * @param {String} attribs.alignHoriz Horizontal alignment of this TextStim.
 * @param {String} attribs.alignVert Vertical alignment of this TextStim.
 * @param {number} attribs.height Height of this TextStim.
 * @param {number} attribs.wrapWidth Wrap width of this TextStim.
 * @param {boolean} attribs.italic Text will be italicized if true.
 * @param {boolean} attribs.bold Text will be bold if true.
 * @param {boolean} attribs.flipVert Flips the text vertically if true.
 * @param {boolean} attribs.flipHoriz Flips the text horizontally if true.
 */
psychoJS.visual.TextStim = function(attribs) {
	psychoJS.visual.BaseVisualStim.call(this, attribs);
	psychoJS.visual.asColor.call(this);
	psychoJS.visual.asWindowRelated.call(this);

	this.win = psychoJS.getAttrib(attribs ,'win', undefined);
	this.name = psychoJS.getAttrib(attribs ,'name', undefined);
	//this.depth = psychoJS.getAttrib(attribs, 'depth', 0); // deprecated attribute, just drop it?
	this.status = undefined;

// 	this._color = psychoJS.getAttrib(attribs ,'color', 0xFFFFFF);
// 	this._colorSpace = psychoJS.getAttrib(attribs, 'colorSpace', 'rgb');
	this._contrast = psychoJS.getAttrib(attribs, 'contrast', 1);
	this.setColor(psychoJS.getAttrib(attribs ,'color', 0xFFFFFF), psychoJS.getAttrib(attribs, 'colorSpace', 'rgb'));

	this._text = psychoJS.getAttrib(attribs, 'text', '');

	this._font = psychoJS.getAttrib(attribs, 'font', 'Arial');
	this._alignHoriz = psychoJS.getAttrib(attribs, 'alignHoriz', 'center');
	this._alignVert = psychoJS.getAttrib(attribs, 'alignVert', 'center');
	this._height = psychoJS.getAttrib(attribs, 'height', undefined);
	this._wrapWidth = psychoJS.getAttrib(attribs, 'wrapWidth', undefined);
	this._italic = psychoJS.getAttrib(attribs, 'italic', false);
	this._bold = psychoJS.getAttrib(attribs, 'bold', false);
	this._flipVert = psychoJS.getAttrib(attribs, 'flipVert', false);
	this._flipHoriz = psychoJS.getAttrib(attribs, 'flipHoriz', false);


	Object.defineProperty(this, 'text', {
		configurable: true,
		get : function() { return this._text; },
		set : function(value) { this.setText(value); }
	});

	Object.defineProperty(this, 'alignHoriz', {
		configurable: true,
		get : function() { return this._alignHoriz; },
		set : function(value) { this.setAlignHoriz(value); }
	});

	Object.defineProperty(this, 'wrapWidth', {
		configurable: true,
		get : function() { return this._wrapWidth; },
		set : function(value) { this.setWrapWidth(value); }
	});

	Object.defineProperty(this, 'height', {
		configurable: true,
		get : function() { return this._height; },
		set : function(value) { this.setHeight(value); }
	});

	Object.defineProperty(this, 'italic', {
		configurable: true,
		get : function() { return this._italic; },
		set : function(value) { this.setItalic(value); }
	});

	Object.defineProperty(this, 'bold', {
		configurable: true,
		get : function() { return this._bold; },
		set : function(value) { this.setBold(value); }
	});

	Object.defineProperty(this, 'flipVert', {
		configurable: true,
		get : function() { return this._bold; },
		set : function(value) { this.setFlipVert(value); }
	});

	Object.defineProperty(this, 'flipHoriz', {
		configurable: true,
		get : function() { return this._bold; },
		set : function(value) { this.setFlipHoriz(value); }
	});

	this._needUpdate = true;
}

psychoJS.visual.TextStim.prototype = Object.create(psychoJS.visual.BaseVisualStim.prototype);

psychoJS.visual.TextStim.prototype._computeHeightPix = function() {
	var height = this._height || 0.1;
	this._heightPix = this._getLengthPix(height);
}

psychoJS.visual.TextStim.prototype._updateIfNeeded = function() {
	if (this._needUpdate) {
		this._computeHeightPix();


// 		var gameObjectText = new GameObject ("testText");
// 		pixiObjectContainer =gameObject.getPixiContainer();
// 		gameObject.size.width = pixiObjectContainer.context.measureText(pixiObjectContainer.text).width;
// 		gameObject.size.height = pixiObjectContainer.context.measureText(pixiObjectContainer.text).height;

		var fontSize = Math.round(this._heightPix);
		var rgb = this._getDesiredRGB(this._rgb, this._colorSpace, this._contrast);
// 		console.log("Text._updateIfNeeded color: " + JSON.stringify(rgb) + " from " + JSON.stringify(this._rgb));
		var font =
				(this._bold ? 'bold ' : '') +
				(this._italic ? 'italic ' : '') +
				fontSize + 'px ' + this._font;
		this.pixiRep = new PIXI.Text(this._text, {
			font : font,
			fill : psychoJS.rgb2hex(rgb),
			align : this._alignHoriz,
			wordWrap : this._wrapWidth != undefined,
			wordWrapWidth : this._wrapWidth ? this._getHorLengthPix(this._wrapWidth) : 0
		});

		//console.log("********** wrapWidth = " + (this._wrapWidth ? this._getHorLengthPix(this._wrapWidth) : 0));

		this.pixiRep.anchor.x = 0.5;
		this.pixiRep.anchor.y = 0.5;

		this.pixiRep.scale.x = this._flipHoriz ? -1 : 1;
		this.pixiRep.scale.y = this._flipVert ? 1 : -1;

		// scales bitmap so not great
// 		this.pixiRep.scale.x = this._size;
// 		this.pixiRep.scale.y = this._size;

		this.pixiRep.rotation = this._ori * Math.PI/180;

		this._setPosPix(this.pixiRep.position, this._pos);
		//this.pixiRep.position.x = this._pos[0];
		//this.pixiRep.position.y = this._pos[1];

		this.pixiRep.alpha = this._opacity;

		this._size = [
				this._getLengthUnits(Math.abs(this.pixiRep.width)),
				this._getLengthUnits(Math.abs(this.pixiRep.height)) ];

		this._needUpdate = false;
	}
}


/**
 * Sets the text of this TextStim
 * @param {String} text value of this TextStim.
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.TextStim.prototype.setText = function(text, log) {
	psychoJS.attributeSet(this, "_text", text, log);

//	this.pixiRep.text = this._text;
// 	this.pixiRep.position.x = -this.pixiRep.width/2;
// 	this.pixiRep.position.y = -this.pixiRep.height/2;

	this._needUpdate = true;
	this._needVertexUpdate = true;
}


/**
 * Sets the alignHoriz property of this TextStim
 * @param {String} value alignHoriz value of this TextStim.
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.TextStim.prototype.setAlignHoriz = function(value, log) {
	psychoJS.attributeSet(this, "_alignHoriz", value, log);

	this._needUpdate = true;
	this._needVertexUpdate = true;
}


/**
 * Sets the wrapWidth property of this TextStim
 * @param {String} value wrapWidth value of this TextStim.
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.TextStim.prototype.setWrapWidth = function(value, log) {
	psychoJS.attributeSet(this, "_wrapWidth", value, log);

	this._needUpdate = true;
	this._needVertexUpdate = true;
}

/**
 * Sets the height of the text.
 * @param {String} value height value of this TextStim.
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.TextStim.prototype.setHeight = function(value, log) {
	psychoJS.attributeSet(this, "_height", value, log);

	this._needUpdate = true;
	this._needVertexUpdate = true;
}

/**
 * Sets the height of the text.
 * @param {String} value height value of this TextStim.
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.TextStim.prototype.setItalic = function(value, log) {
	psychoJS.attributeSet(this, "_italic", value, log);

	this._needUpdate = true;
	this._needVertexUpdate = true;
}

/**
 * Sets the bold value of the text.
 * @param {String} value bold value of this TextStim.
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.TextStim.prototype.setBold = function(value, log) {
	psychoJS.attributeSet(this, "_bold", value, log);

	this._needUpdate = true;
	this._needVertexUpdate = true;
}

/**
 * Sets the flipVert of the text.
 * @param {String} value flipVert value of this TextStim.
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.TextStim.prototype.setFlipVert = function(value, log) {
	psychoJS.attributeSet(this, "_flipVert", value, log);

	this._needUpdate = true;
	this._needVertexUpdate = true;
}

/**
 * Sets the flipHoriz of the text.
 * @param {String} value flipHoriz value of this TextStim.
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.TextStim.prototype.setFlipHoriz = function(value, log) {
	psychoJS.attributeSet(this, "_flipHoriz", value, log);

	this._needUpdate = true;
	this._needVertexUpdate = true;
}



/**
 * Class of image stimuli to be displayed in a Window.
 * @constructor
 * @param {Object} attribs Associative array used to store the following parameters:
 * @param {Object} attribs.win the Window that should display this ImageStim.
 * @param {String} attribs.name Name of this ImageStim.
 * @param {Array} attribs.size Size of the stimulus.
 * @param {number} attribs.opacity Determines how visible the stimulus is relative to background.
 * @param {Array} attribs.pos Position of the stimulus in the Window.
 * @param {String} attribs.image Path to the source image to be displayed in this ImageStim.
 * @param {number} attribs.mask Path to the mask image to be used in this ImageStim.
 * @param {Object} attribs.color Color of this ImageStim.
 * @param {String} attribs.colorSpace ColorSpace of this ImageStim.
 * @param {boolean} attribs.flipVert Flips the text vertically if true.
 * @param {boolean} attribs.flipHoriz Flips the text horizontally if true.
 */
psychoJS.visual.ImageStim = function(attribs) {
	psychoJS.visual.BaseVisualStim.call(this, attribs);
	psychoJS.visual.asColor.call(this);
	psychoJS.visual.asWindowRelated.call(this);

	this.win = psychoJS.getAttrib(attribs ,'win', undefined);
	this.name = psychoJS.getAttrib(attribs ,'name', undefined);
	this.status = undefined;

	this._image = psychoJS.getAttrib(attribs ,'image', undefined);
	this._mask = psychoJS.getAttrib(attribs ,'mask', undefined);

	this._color = psychoJS.getAttrib(attribs ,'color', 0xFFFFFF);
	this._rgb = [1, 1, 1];
	this._colorSpace = psychoJS.getAttrib(attribs, 'colorSpace', 'rgb');
	this._contrast = psychoJS.getAttrib(attribs, 'contrast', 1);

	this._flipVert = psychoJS.getAttrib(attribs, 'flipVert', false);
	this._flipHoriz = psychoJS.getAttrib(attribs, 'flipHoriz', false);


	Object.defineProperty(this, 'image', {
		configurable: true,
		get : function() { return this._image; },
		set : function(value) { this.setImage(value); }
	});

	Object.defineProperty(this, 'mask', {
		configurable: true,
		get : function() { return this._mask; },
		set : function(value) { this.setMask(value); }
	});

	Object.defineProperty(this, 'flipVert', {
		configurable: true,
		get : function() { return this._bold; },
		set : function(value) { this.setFlipVert(value); }
	});

	Object.defineProperty(this, 'flipHoriz', {
		configurable: true,
		get : function() { return this._bold; },
		set : function(value) { this.setFlipHoriz(value); }
	});
}

psychoJS.visual.ImageStim.prototype = Object.create(psychoJS.visual.BaseVisualStim.prototype);

psychoJS.visual.ImageStim.prototype._updateIfNeeded = function() {
	if (this._needUpdate) {
		if (this._image) {
			this._texture = new PIXI.Texture(new PIXI.BaseTexture(this._image)); //new PIXI.Texture.fromImage(this._image);
			this.pixiRep = new PIXI.Sprite(this._texture);

			if (this._mask) {
				this._maskTexture = new PIXI.Texture(new PIXI.BaseTexture(this._mask));
				this.pixiRep.mask = new PIXI.Sprite(this._maskTexture); //PIXI.Sprite.fromImage(this._mask);

				// the following is required for the mask to be aligned with the image
				this.pixiRep.mask.anchor.x = 0.5;
				this.pixiRep.mask.anchor.y = 0.5;
				this.pixiRep.addChild(this.pixiRep.mask);
			}

			if (this._texture.width == 0) return; // width is not immediately available (following new PIXI.Texture.fromImage) and the following code requires it, so _needUpdate will remain true until we get a non 0 value

			if (!this._size) {
				console.log("texture w=" + this._texture.width);
				this._size = [this._getLengthUnits(this._texture.width), this._getLengthUnits(this._texture.height)];
			}

			this.pixiRep.anchor.x = 0.5;
			this.pixiRep.anchor.y = 0.5;

			var scaleX = this._getLengthPix(this.size[0]) / this._texture.width;
			var scaleY = this._getLengthPix(this.size[1]) / this._texture.height;

			this.pixiRep.scale.x = this._flipHoriz ? -scaleX : scaleX;
			this.pixiRep.scale.y = this._flipVert ? scaleY : -scaleY;

			this.pixiRep.rotation = this._ori * Math.PI/180;

			this._setPosPix(this.pixiRep.position, this._pos);

			this.pixiRep.alpha = this._opacity;
		}
		else {
			this.pixiRep = undefined;
		}
		this._needUpdate = false;
	}
}

/**
 * Sets the flipVert property of the ImageStim.
 * @param {String} value flipVert value of this ImageStim.
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.ImageStim.prototype.setFlipVert = function(value, log) {
	psychoJS.attributeSet(this, "_flipVert", value, log);

	this._needUpdate = true;
	this._needVertexUpdate = true;
}

/**
 * Sets the flipHoriz of the ImageStim.
 * @param {String} value flipHoriz value of this ImageStim.
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.ImageStim.prototype.setFlipHoriz = function(value, log) {
	psychoJS.attributeSet(this, "_flipHoriz", value, log);

	this._needUpdate = true;
	this._needVertexUpdate = true;
}


/**
 * Sets the image in the ImageStim.
 * @param {String} value Path to the source image to be displayed in this ImageStim.
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.ImageStim.prototype.setImage = function(value, log) {
	psychoJS.attributeSet(this, "_image", value, log);

	this._needUpdate = true;
	this._needVertexUpdate = true;
}


/**
 * Sets the mask in the ImageStim.
 * @param {String} value Path to the mask image to be used in this ImageStim.
 * @param {boolean} log true to log a message, false otherwise
 */
psychoJS.visual.ImageStim.prototype.setMask = function(value, log) {
	psychoJS.attributeSet(this, "_mask", value, log);

	this._needUpdate = true;
	this._needVertexUpdate = true;
}
