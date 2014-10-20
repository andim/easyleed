User's Guide
============

Here is a short step-by-step guide:

- Open the images you want to work with using "File --> Open..." or use "Open" in the toolbar. Only the images selected in the file dialog will be processed later on.
- Navigate through the images using "Process --> Previous Image" and "Process --> Next Image”, or buttons in the status bar, or with the slider until you have found the image at which you want to start the analysis. If you know the energy corresponding to the image of interest, you can enter it to select the corresponding image by pressing the button labeled “eV” and by entering the relative energy. 
- Select the position of the spots by a left click.
- The center of the pattern can be set for an optimized spot tracking with a right click.
- You can change the position of the selected spot with the arrow keys. The size of the integration window can be changed using + or -. (optional)
- Change the tracking parameters using "Process -- Set Parameters" or pressing "Set Parameters" in the toolbar. (Optional)
- Start the tracking of the spots using "Process --> Run" or pressing "Run" in the toolbar. The I(E) plot starts automatically.
- I(E) averages can be plotted directly from the check box in the Plot window.
- Smoothed I(E) averages can be plotted directly from the check box in the Plot window (uses cubic spline).
  * Any change in smoothing parameters in settings is immediately applied in the plot.
- Tooltips in the image in correspondence to the spots show the spot number. The same number is displayed in the legend in the plot.
- Click the stop button in the status bar to stop processing. (optional)
- Save the generated intensities using "File --> Save Intensities..." OR
- Plot the generated intensities using "Process --> Plot" or the "Plot" option in the toolbar.
- Save the generated plot image using "File --> Save Plot"

- Parameter settings can also be saved/loaded
- The selected spot and center positions can also be saved and reloaded for further intensity acquisitions.

File naming policy
------------------

EasyLEED tries to infer the beam energy from the filename. 

Examples of valid file names in the default configuration:

- file30.jpg -->  at 30eV beam energy
- file30.5.jpg -->  at 30.5eV beam energy

For advanced users:
You can change the regular expression that is used for parsing energies from filenames in the config file.

Custom configuration
--------------------

Most of the default parameters of the algorithm as well as many UI tweaks are controlled via a config file. Copy `easyleed/default-config.py` to `config.py` and edit this file (it takes precedence over the former file) for customization.
