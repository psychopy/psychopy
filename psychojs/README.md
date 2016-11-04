# PsychoJS for PsychoPy experiments online

This folder contains the code for _PsychoJS_, a JavaScript port of the _PsychoPy_ Python library, written by http://www.ilixa.com

## Why is this good?

The idea is that your PsychoPy experiment will be available to your participants from a web page. That means they can run it from any device equipped with a browser (we're talking about desktop, laptop, iPads or Android tablets. Heck they can use their phone!)

Builder will output the web files you need, you can upload them to an experiment server, send the server’s URL to your participants, and download the experiment data when they are done. Many of your existing Builder experiments will "just work", subject to the currently supported Components.

## How does this work?

A variety of technologies are used to run PsychoPy experiments online.

**JavaScript:** The most obvious part is that there's an HTML web page and a JavaScript library that are needed to present stimuli and collect responses. _PsychoJS_ is pretty much a direct JavaScript port of the PsychoPy Python library and operates in a very similar way. That means you get the same level of control, to the level of frame-by-frame updates, and you have complete control over the structure of your trials/blocks, etc. in just the same way that you can under PsychoPy. Under the hood _PsychoJS_ uses `pixi.js` for stimulus presentation and response collection. `pixi.js` is a multi-platform, accelerated, 2-D renderer, that runs in most modern browsers. It uses `WebGL` where supported and silently falling back to an `HTML5 canvas` where not. WebGL has some performance advantages (it's more efficient than `canvas` by using the graphics card to do the work rather than the CPU) but the features should be the same.

The JavaScript code runs in the browser of the participant in your study (programmers call this "client-side"), and communicates with the experiment server to download resources and upload data and logs.

**PHP:** PHP is used "server-side" to control the transfer of resources. That means downloading the experiment’s conditions and images to the participant’s browser and uploading theirs data and logs to the experiment server at the end of the experiment.

**Open Science Framework:** PsychoPy now supports synchronising projects with OSF.io. If you use this then all you need to do is to upload your experiment’s resources to your OSF project page, and upload the PsychoJS  PHP script, HTML file and JavaScript library to your experiment server. To access your OSF project even when it is private, the PHP experiment server needs the project’s private key. But don't worry: because communications with OSF are done "server-side", they are invisible to participants (i.e. participants and nosey parkers don't have access to the key that allows project access). The PHP script also enables you to download the resources from the OSF project page to store them locally, which makes it possible to change the resources via the OSF.io platform, without having to bother your web admin with access to the server.

**PsychoPy Builder:** Just as PsychoPy Builder currently automatically generates a Python script for you using the PsychoPy Python library, the new version is going to automatically generate the required HTML and PHP files.

The PsychoPy Builder interface code to export the necessary PsychoJS (HTML and PHP) files isn't finished yet but you can already use it to see roughly what experiments look like converted to JavaScript.

## Can I write my own online experiments using PsychoJS?

The _PsychoJS_ library looks much like its PsychoPy equivalents; it has classes like `Window` and `ImageStim` and these have the same attributes as their Python equivalents. So, from that aspect, things are relatively similar and you can probably hack your PsychoJS script if you're fairly familiar with the PsychoPy lib.

The main difference between PsychoJS and PsychoPy is that the former is not as sequential as the latter. A typical web page will carry on creating itself while its images are downloading, for instance. As a result, PsychoJS adds the concept of `Scheduler`s, which are used to determine when things occur. For instance, you could think of the Flow in PsychoPy as being a Schedule with various items on it, but then some of those, such as trial loops also schedule further events (the individual trials to be run). If you export a script from one of your Builder experiments you can examine this to see how it works.

## Where do the participant’s data go?

The participant’s data and logs are saved to a data folder on the experiment server. Optionally, they can also be pushed to your OSF project if you have connected one with the experiment.

## What parts of my Builder experiment are supported?

See http://www.psychopy.org/online/status.html for more information.
