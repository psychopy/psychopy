# PsychoJS for PsychoPy experiments online

This folder contains the code for _PsychoJS)_, a JavaScript port of (parts of) the _PsychoPy_ (i.e. Python), written by http://www.ilixa.com

## Why is this good?

The idea is that you'll be able to run your PsychoPy experiments from a web page, and that means you can run it from any portable device that has a browser (we're talking about your iPad or Android tablet. Heck you can use your phone!)

Builder will output the web scripts you need, you can upload them to a web server and download the data when you're done. Many of your existing Builder experiments will "just work", subject to the currently supported Components.

## How does this work?

A variety of technologies are used to run experiments online.

**JavaScript:** The most obvious part is that there's a JavaScript web page that's needed to present stimuli and collect responses. The _PsychoJS_ is pretty much a direct port of the Python PsychoPy library and operates in the same way. That means you get the same level of control, to the level of frame-by-frame updates and you have complete control over the structure of your trials/blocks etc in just the same way that you can under PsychoPy. Under the hood _PsychoJS_ uses `pixi.js` for stimulus presentation and response collection. This will run in any modern browser, using the `WebGL` where supported and silently falling back to an `HTML5 canvas` where WebGL isn't available. WebGL has some performance advantages (it's more efficient than `canvas` by using the graphics card to do the work rather than the CPU) but the features should be the same.

JavaScript runs in the browser of the participant in your study (programmers call this "client-side") and it will need to download the various resources from the web site

**PHP:** PHP is used "server-side" to control the sending/receiving of resources (that means your images to be downloaded and the data being saved) between the browser and the server.

**Open Science Framework:** PsychoPy supports synchronising projects with OSF.io and if you use this then all you need to upload to your experiment server is the PHP file. It can go and fetch the files from osf.io and will save them back there when it's done. The contents of the PHP file include a key to allow the experiment access to the OSF project even if it's a private project. Don't worry; because the PHP file is "server-side" it can't be read by people viewing the file through a browser (i.e. participants and nosey parkers don't have access to the key that allows project access).

**PsychoPy Builder:** Just as PsychoPy Builder currently generates a Python script for you using the PsychoPy Python library, the new version is going to write generate the HTML/PHP

PsychoPy Builder interface code to export the necessary PsychoJS (HTML and PHP) files isn't finished yet but you can already use it to see roughly what experiments look like converted to JavaScript.

## Can I write my own JS experiments using PsychoJS?

The _PsychoJS_ library looks much like the PsychoPy equivalents; it has classes like `Window` and `ImageStim` and these have the same attributes as their Python equivalents. So, from that aspect, things are relatively similar and you can probably hack your PsychoJS script if you're fairly familiar with the PsychoPy lib.

The main difference between PsychoJS and PsychoPy is that web pages don't wait for each line to complete before continuing to the next whereas Python commands typically do (a web page should carry on creating itself while images are downloaded, for instance). As a result of this difference, PsychoJS adds the concept of `Scheduler`s which are used to determine when things occur. For instance, you could think of the Flow in PsychoPy as being a Schedule with various items on it, but then some of those, such as trial loops also schedule further events (the individual trials to be run). If you export a script from one of your Builder experiments you can examine this to see how it works.

## Where does my data go?

Your data will be saved to a data folder on the web server that you were using to run the experiment and, optionally, they will also be pushed to an OSF project if you have connected one with the experiment.

## What parts of my Builder experiment are supported?

So far PsychoJS contains ports of the following PsychoPy features and so experiments limited to these will work as of PsychoPy version 1.85 (soon):

* Window class
* TextStim class
* ImageStim class
* TrialHandler class
* Keyboard class
* Mouse class
* Dialog boxes
* Data saving
* Automated logging

In addition, Code Components will write their code into the JS file, just as they write their code into the Python script. Of course, you'll need to convert your code to be JS syntax rather than Python syntax though!
