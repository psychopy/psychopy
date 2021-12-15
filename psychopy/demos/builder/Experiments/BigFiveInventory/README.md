# Personality Inventories - Form Class Demonstration

## The experiment

This is a demonstration of how to create forms in PsychoPy. We're doing a personality inventory as a demonstration. We've included a few options, all measuring the Big Five (Openness, Conscientiousness, Extraversion, Agreeableness and Neuroticism; Goldberg 1993). The options we provide have different lengths though:

 - TIPI: The Ten Item Personality Inventory (Gosling et al, 2003)
 - mini_IPIP: The mini IPIP (Donnellan et al, 2006) with 20 items abbrieviated from the IPIP (Goldberg 1999)
 - The Big Five Inventory (John & Srivastava, 1999) with 44-items

## Implementation

The forms are included as different Routines so you can add/remove them from the Flow easily if you want to switch to a different one.
    
Each of the forms has been given a "Continue" button using the Code Component but that only becomes active when the form is marked "complete" as you can see in the Each Frame code of the Code Component.

## References:

> Gosling, S. D., Rentfrow, P. J., & Swann, W. B., Jr. (2003). A Very Brief Measure of the Big Five Personality Domains. Journal of Research in Personality, 37, 504-528.

> Donnellan, M. B., Oswald, F. L., Baird, B. M., & Lucas, R. E. (2006). The Mini-IPIP Scales: Tiny-yet-effective measures of the Big Five Factors of Personality. Psychological Assessment, 18(2), 192–203. https://doi.org/10.1037/1040-3590.18.2.192

> John, O. P., & Srivastava, S. (1999). The Big-Five trait taxonomy: History, measurement, and theoretical perspectives. In L. A. Pervin & O. P. John (Eds.), Handbook of personality: Theory and research (Vol. 2, pp. 102-138). New York: Guilford Press. https://pdfs.semanticscholar.org/0898/fc9f1068d99eaf18011c14913f6530144794.pdf
