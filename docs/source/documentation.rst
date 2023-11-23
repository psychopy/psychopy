Documentation
=====================================

This page is full of helpful documentation if you know about any more please let us know so we can add them!

What do you want to do?
------------------------


.. raw:: html

   <div>
     <h1 class="clickable" onclick="toggleContent('content1')">I want to learn how to use PsychoPy</h1>
     <div id="content1" class="content hidden">
       <p>If you're new to PsychoPy, there are plenty of resources to help you get started!</p>
       <h2>PsychoPy Manual:</h2>
       <p>A PDF copy of the current manual is available at: <a href="https://www.psychopy.org/PsychoPyManual.pdf">https://www.psychopy.org/PsychoPyManual.pdf</a></p>
       <h3>Contents:</h3>
       <ul>
         <li><a href="https://psychopy.org/about/index.html">About PsychoPy - how to cite, testimonials etc.</a></li>
         <li><a href="https://psychopy.org/general/index.html">General PsychoPy guidance - useful information for both builder and coder views</a></li>
         <li><a href="https://psychopy.org/general/timing/index.html">Timing considerations - important information on PsychoPy's temporal precision</a></li>
         <li><a href="https://psychopy.org/download.html">How to download - guidance on how to download PsychoPy</a></li>
         <li><a href="https://psychopy.org/gettingStarted.html">Getting started - How to get started with PsychoPy</a></li>
         <li><a href="https://psychopy.org/builder/index.html">Builder - building experiments in a GUI</a></li>
         <li><a href="https://psychopy.org/coder/index.html">Coder - writing experiments using scripts</a></li>
         <li><a href="https://psychopy.org/online/index.html">Online - running experiments on the web</a></li>
         <li><a href="https://psychopy.org/hardware/index.html">Hardware - interacting with external hardware</a></li>
       </ul>
       <h2>YouTube channels</h2>
       <p>Our own <a href="https://www.youtube.com/channel/UCQo2aB6cXJasHyXJp0afaWg">PsychoPy Official YouTube channel</a> contains lots of helpful tutorials!</p>
       <p>There are many more useful channels too, see our teaching resources section for just a few of them.</p>
     </div>
   </div>


.. raw:: html

   <div>
     <h1 class="clickable" onclick="toggleContent('content2')">I want to troubleshoot a problem</h1>
     <div id="content2" class="content hidden">
       <ul>
         <li><a href="https://psychopy.org/troubleshooting.html">You can take a look at common problems on our troubleshooting page</a></li>
         <li><a href="https://psychopy.org/tutorials/index.html">If you're wondering how to do something, you can take a look at our 'How do I...' page</a></li>
         <li><a href="https://psychopy.org/alerts/index.html">If you have an alert code and want to find out what it means, take a look at our alerts page</a></li>
         <li><a href="https://psychopy.org/consultancy.html">If you'd like one-to-one help from our team, or want us to build your experiment for you, take a look at our consultancy services</a></li>
       </ul>
       <p>If you have a problem, chances are someone else has already solved it! Search or post on our <a href="https://discourse.psychopy.org/">forum</a>.</p>
     </div>
   </div>


.. raw:: html

   <div>
     <h1 class="clickable" onclick="toggleContent('content3')">I want to help develop PsychoPy</h1>
     <div id="content3" class="content hidden">
       <ul>
         <li><a href="https://psychopy.org/developers/index.html">Developers - Information for those interested in contributing to PsychoPy development</a></li>
         <li><a href="https://psychopy.org/psyexp.html">PsychoPy Coder - Contributing to the PsychoPy Coder project</a></li>
       </ul>
     </div>
   </div>

.. raw:: html

   <style>
     .hidden {
       display: none;
     }
     h1.clickable {
       font-size: 18px;
       cursor: pointer;
       text-decoration: underline;
       color: #6495ED;
     }
   </style>

   <script>
     function toggleContent(contentId) {
       var content = document.getElementById(contentId);
       var isHidden = content.classList.contains("hidden");
       content.classList.toggle("hidden", !isHidden);
     }
   </script>


