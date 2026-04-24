# PsychoPy Demo: Dual-Window Experiment Setup

This demo shows how to run a PsychoPy experiment with **two separate windows**:

- **Participant window** – the main experiment display.
- **Experimenter window** – a monitoring display showing trial progress and accuracy.

This is useful when an experimenter needs to observe performance without interrupting the participant's task.

The task used in the demo is a Stroop task, but you can adapt the demo as needed to be used in any task!

---

## How it works

At the start of the task, PsychoPy creates two windows.  
The experimenter window updates in real time with:

- Current progress
- Accuracy (overall performance)

The participant window functions as a standard stimulus display.

---

## Screen assignment

By default:

| Window               | Screen index | Behaviour |
|----------------------|--------------|-----------|
| Experimenter window  | `screen=0`   | Uses the same screen where PsychoPy is running. |
| Participant window   | `screen=1`   | Uses the next available screen (if connected). |

> If only **one screen** is available, both windows will appear on that screen.

---

## Full-screen behaviour

The participant window is **not fullscreen by default** (useful while testing locally).

To enable fullscreen:

1. Open **Experiment Settings**
2. Go to the **Screen** tab
3. Tick **Full-screen window**

---

## Online compatibility

> **Note:** This demo works **locally only**.  

---

## Requirements

- Local desktop / laptop (not browser)
- Optional: second display for separate experimenter/participant screens

---