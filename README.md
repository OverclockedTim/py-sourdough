# py-sourdough

## Description
py-sourdough is a hobby project that uses computer vision to help with the process of making great sourdough by watching rising sourdough in a container and even potentially alarming by sending the user an email to alert them that the sourdough starter rise is complete and now ready to use. It can also be used to create some very cool visualizations and timelapse videos of the sourdough rising.  In fact, the alert email automatically attaches an animated gif of the sourdough rise (compressed down to 10s) so that every alert email is accompanied with a super cool visual.

### Important Warning
This is a hobby project, and as such, no extensive work has been done to make it work on computers of a different configuration. It is designed to be used on a Windows machine with a webcam, and a WSL2 partition. If you need it to work on a computer of a different configuration, you will likely need to make the changes yourself (pull requests happily accepted!)

## Pre-Setup / Tips & Tricks

Webcam: I used a Logitech Brio 4k, and it's...OK by 2024 standards. I have also used an old iPhone via Camo Studio, but the connection was oddly flakely. In either case, I do recommend using something like Camo Studio which enables you to have easy previews, image modification controls, and, vitally, manual focus controls.  It makes the camera setup nice and visual fast. I tend to just set it up in the background and then point the python at the Camo virtual device. Not necessary, but it makes things easier.

Sourdough Vessel & Lighting: The SAM model seems to have trouble with gradients and rounded corners. As such, I've found it easiest to use square glass vessels to hold the sourdough in. Ideally, the vessel should be small enough that the amount of sourdough starter you are working with takes up a fair amount of vertical space, in other words a very wide jar isn't going to work the best. Rounded jars tend to have shiny glare spots around the curves, so square jars are the best. Finally, make sure that the jar is wide enough that when the sourdough starter is fully risen, you will still be able to easily see the whole video in one webcam shot. 

## Getting Started


* First up, you will need a Segment-Anything model ready environment. See that project for details, but it means things like getting an environment set up where you can run pytorch and cv2.
* Second up, this project manages most dependencies with poetry. Do the standard poetry steps, like running poetry shell before trying to execute scripts. `poetry install --no-root`
* The notebook has the same dependencies, make sure that you set up your notebook environment (jupter/vscode/etc) to use the poetry environment. (for vscode, that may require making sure that your poetry virtual environment is set up to be inside the project [See Stack Overflow](https://stackoverflow.com/questions/59882884/vscode-doesnt-show-poetry-virtualenvs-in-select-interpreter-option))
* Set up an 'env.sh' with your local variables. It needs a 'GMAIL_APP_PASSWORD' (you must get that from your google account) and 'EMAIL' (as in email address, which will be used as both the from and the to address for the alarm email.)

## Starting a Sourdough Run

These next few steps, you will need to do each type you alarm for a sourdough.  

1. Make sure that you have this repo pulled both to a directory in windows, and also to a directory in WSL2. You will use record_from_windows.py to capture screenshots from the windows side, but all the other code will run in WSL2
2.  Go ahead and get started with your sourdough. Put your starter in front of the camera, and run record_from_windows.py from powershell on your windows side.
3. Execute the sourdough_notebook.ipynb notebook through the "Save configuration" step.  The purpose of this step is to ensure that your sourdough starter vessel is in the right spot in front of the camera, and that the coordinates for the SAM "prompt" are working to get you a good solid outline of the sourdough. Every one of the stars should be solidly inside the sourdough image being picked up by your webcam.  If it's not, just update the config variables and re-run the notebook from that point. Once the "configuration testing" cell gives you a good solid image, you're all configured.
4. In a WSL2 shell (and inside the poetry shell for the project), execute alarm.py. 
5. (Optional) if you feel like making cool videos at some point (such as after the alarm has sounded and your sourdough has risen completely), execute the remaining cells in the sourdough notebook to create videos like the ones shown here.