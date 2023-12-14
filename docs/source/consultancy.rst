
Consultancy services
======================

.. raw:: html

   <div class="image-carousel" style="display: flex; justify-content: center;">
       <img src="path/to/your/image1.jpg" style="width: 700px; display: block;">
       <img src="path/to/your/image2.jpg" style="width: 700px; display: none;">
       <img src="path/to/your/image3.jpg" style="width: 700px; display: none;">
       <img src="path/to/your/image4.jpg" style="width: 700px; display: none;">
   </div>

   <script>
   var currentIndex = 0;
   var images = document.querySelectorAll('.image-carousel img');

   function cycleImages() {
       var totalImages = images.length;
       images[currentIndex].style.display = 'none';
       currentIndex = (currentIndex + 1) % totalImages;
       images[currentIndex].style.display = 'block';
   }

   setInterval(cycleImages, 3000); // Change image every 3 seconds
   </script>


How much does it cost?
--------------------------------

These are our costs per hour of support:

.. image:: images/pricing_table.png
   :width: 700px
   :align: center


How can I get support?
--------------------------------

Just use the button below to get in touch!

.. raw:: html

    <a href="https://forms.clickup.com/4570406/f/4bf96-7552/ZN8URSTDTWDENY6RP9" style="background-color: lightblue; color: white; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; border-radius: 5px;">Get in touch!</a>
