/**
 * Scheduler component of psychoJS
 * 
 * 
 * This file is part of the PsychoJS javascript engine of PsychoPy.
 * Copyright (c) 2016 Ilixa Ltd. (www.ilixa.com)
 * 
 * Distributed under the terms of the GNU General Public License (GPL).
 */


psychoJS.NEXT = "NEXT";
psychoJS.FLIP_REPEAT = "FLIP_REPEAT";
psychoJS.FLIP_NEXT = "FLIP_NEXT";
psychoJS.QUIT = "QUIT";


/**
 * A scheduler helps run the main loop by managing scheduled functions,
 * called tasks, after each frame is displayed.
 * 
 * <p>
 * Tasks are either another [Scheduler]{@link psychoJS.Scheduler}, or a
 * javascript functions returning one of the following codes:
 * <ul>
 * <li>psychoJS.NEXT: </li>
 * <li>psychoJS.FLIP_REPEAT: </li>
 * <li>psychoJS.FLIP_NEXT: </li>
 * <li>psychoJS.QUIT: </li>
 * </ul>
 * </p>
 * 
 * <p> It is possible to create sub-schedulers, e.g. to handle loops.
 * Sub-schedulers are added to a parent scheduler as a normal
 * task would be by calling [scheduler.add(subScheduler)]{@link psychoJS.Scheduler.add}.</p>
 * 
 * <p> Conditional branching is also available by calling
 * [scheduler.addConditionalBranches]{@link psychoJS.Scheduler.addConditionalBranches}</p>
 * 
 * @constructor
 */
psychoJS.Scheduler = function() {
	this.taskList = [];
	this.currentTask = undefined;
	this.argsList = [];
	this.currentArgs = undefined;
}


/**
 * Schedule a task.
 * 
 * @param task - the task to be scheduled
 */
psychoJS.Scheduler.prototype.add = function(task, args) {
	this.taskList.push(task);
	this.argsList.push(args);
}


/**
 * Schedule two conditional branches.
 * 
 * <p> The branches are [sub-schedulers]{@link psychoJS.Scheduler}.</p>
 * 
 * @param condition - the condition
 * @param {psychoJS.Scheduler} thenScheduler - the [Scheduler]{@link psychoJS.Scheduler} to be run if the condition is satisfied
 * @param {psychoJS.Scheduler} elseScheduler - the [Scheduler]{@link psychoJS.Scheduler} to be run if the condition is not satisfied
 */
psychoJS.Scheduler.prototype.addConditionalBranches = function(condition, thenScheduler, elseScheduler) {
	var self = this;
	var task = function() {
		if (condition())
			self.add(thenScheduler);
		else
			self.add(elseScheduler)

		return psychoJS.NEXT;
	};
	
	this.add(task);
}



/**
 * Run tasks in sequence until one of them returns something other than NEXT.
 * 
 * @return the current state of the scheduler, i.e. QUIT, FLIP_NEXT or FLIP_REPEAT. 
 */
psychoJS.Scheduler.prototype.run = function() {
	var state = psychoJS.NEXT;

	while (state === psychoJS.NEXT) {
		if (!this.currentTask) {
			if (this.taskList.length > 0) {
				this.currentTask = this.taskList.shift();
				this.currentArgs = this.argsList.shift();
			}
			else {
				this.currentTask = undefined;
				return psychoJS.QUIT;
			}
		}
		if (this.currentTask instanceof Function) {
			state = this.currentTask(this.currentArgs);
		}
		else {
			state = this.currentTask.run();
			if (state === psychoJS.QUIT) state = psychoJS.NEXT;
		}
				
		if (state != psychoJS.FLIP_REPEAT) {
			this.currentTask = undefined;
			this.currentArgs = undefined;
		}
	}

	return state;
}

/**
 * Start this scheduler
 * 
 * <p> Tasks are run after each animation frame.</p>
 * 
 * @param {psychoJS.visual.Window} win - the psychoJS [Window]{@link psychoJS.visual.Window}
 */
psychoJS.Scheduler.prototype.start = function(win) {
	
	// resize the canvas:
	psychoJS.onResize();
	
	var self = this;
	var update = function() {
		if (psychoJS.finished) return;

		++psychoJS.frameCount;
		
		if (win.stats) {
			win.stats.begin();
		}
		win._writeLogOnFlip();
			
		var state = self.run();
		if (state === psychoJS.QUIT) {
			return;
		}
			
		win._renderer.render(win._container);
		win._refresh();
		requestAnimationFrame(update);
		if (win.stats) {
			win.stats.end();
		}
	}
		
	requestAnimationFrame(update);
}

