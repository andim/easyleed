User's Guide
============

.. warning:: This guide is incomplete and not always up-to-date with the newest version of the software.
    If you are running into trouble using the software we are happy to provide further assistance via email.

    We would also be happy about volunteers who want to contribute to EasyLEED by extending this guide!

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

Parameter settings
------------------

It might be useful to get a rough understanding of the underlying algorithm for intuition into how to set parameters. We recommend you read our paper for an introduction to the ideas behind EasyLEED.

Broadly in the algorithm there is a trade-off between how much to rely on the fitted vs predicted positions. Fitted positions are roughly the maxima of intensity of the spots. The prediction comes from a simple dynamical model of the spots moving towards the center as beam energy is increased. How much the algorithm relies on one over the other depends on an assumed variance of both predictions. The variance of predictions increases if there is more "process noise", i.e. the larger you set those parameters the more the algorithm is going to rely on its fitted position.

The algorithm also uses the user input of initial spot positions (and if set center position). The weight put on this information is controlled by the parameter "User input precision". Larger values of this parameter lead to less weight being put on this prior information.

Sometimes spots vanish so they cannot be fit accurately. The algorithm should then purely rely on the prediction. The "Minimal R^2 to accept fit" specifies the quality of fit below which to reject the position from the fit. Similarly the fit might go awry and converge to a different spot. The parameter "Size of the validation region" sets a cutoff on how much the fitted position can differ from the predicted position, before it is discarded.

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

Qt Wrapper
----------

There exist to different python wrappers for the `Qt` library (`PyQt4` and `PySide`). Both can be used with EasyLEED. To select which one to use set the `QT_API` environment variable to either `pyqt` or `pyside`.
