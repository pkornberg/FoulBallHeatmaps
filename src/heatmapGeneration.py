"""
Utility Functions for Heatmap Generation and Visualization
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
from scipy.stats import gaussian_kde

def filterData(data, condition) -> pd.DataFrame:
    """
    Function to Filter Data Frame Based on Condition

    Parameters
    ----------
    data : pd.DataFrame
        Data Frame Returned by hitChartData() 

    condition : str
        Condition that Specifies Inning, Runners on Base, and Batter Handedness

        Format ("Inning/Runner1st/Runner2nd/Runner3rd/BatterHandedness")

        Inning: Put "T" or "B" in Front of Number for "Top" and "Bottom" 
            ("T1") for Top 1st

        Runner1st / Runner2nd / Runner3rd: Put "0" or "1" to Specifiy If Runner on That Base
            ("1/0/0") for Runner on 1st, Nobody on 2nd or 3rd

        BatterHandedness: Put "L" or "R" for "Left" or "Right" Handed

    Returns
    -------
    filteredData : pd.DataFrame
        Final Data Frame Filtered Based on Condition
    """

    # Extracting Infromation From Condition
    halfInning = condition[0]
    inning = int(condition[1])
    firstBase = int(condition[3])
    secondBase = int(condition[5])
    thirdBase = int(condition[7])
    batterHand = condition[9]

    # Converting Half Inning Labels to Ones that Match Original Data Frame
    if halfInning == "B":
        halfInning = "Bottom"
    else:
        halfInning = "Top"

     # Filtering Original Data Frame By Inning
    filteredData = data[data["half_inning"] == halfInning]
    filteredData = filteredData[filteredData["inning"] == inning]

    # Filtering Data Frame By Which Bases Are Occupied
    if firstBase == 0:
        filteredData = filteredData[filteredData['on_1b'].isna()]
    else:
        filteredData = filteredData[filteredData['on_1b'].notna()]
    
    if secondBase == 0:
        filteredData = filteredData[filteredData['on_2b'].isna()]
    else:
        filteredData = filteredData[filteredData['on_2b'].notna()]
   
    if thirdBase == 0:
        filteredData = filteredData[filteredData['on_3b'].isna()]
    else:
        filteredData = filteredData[filteredData['on_3b'].notna()]

    # Filtering Data Frame By Batter Handedness (Since Batter Handeness is Unkown, Artificially Modify Hit Data)
    if batterHand == "L":

        # Extract Left and Right Field Data
        leftField = filteredData[filteredData['ball_position_x'] <= 0]
        rightField = filteredData[filteredData['ball_position_x'] > 0]

        # For Left Handed Batter, Artificially Modify to Keep Only 40% of Left Field Hit Data 
        leftField = leftField.sample(frac = 0.4, random_state = 42)

        # Concatenate Final Data 
        filteredData = pd.concat([leftField, rightField])
        batterHand = "Left"

    if batterHand == "R":

        # Extract Left and Right Field Data
        leftField = filteredData[filteredData['ball_position_x'] <= 0]
        rightField = filteredData[filteredData['ball_position_x'] > 0]
        
        # For Right Handed Batter, Artificially Modify to Keep Only 40% of Right Field Hit Data 
        rightField = rightField.sample(frac = 0.4, random_state = 42)

        # Concatenate Final Data 
        filteredData = pd.concat([leftField, rightField])
        batterHand = "Right"

    # Filter Data Frame By Batter Handedness
    filteredData['handed'] = batterHand

    # Return Filtered Data
    return filteredData


def drawHeatmap(data) -> None:
    """
    Function to Conduct 2 Dimensional Gaussian Kernel Density Estimation (KDE) and Draw Heatmap on Field

    Parameters
    ----------
    data : pd.DataFrame
        Data Frame Returned By FilterData()
    
    Returns
    -------
    None 
        Displays Matplotlib Visualization
    """

    # Manipulating Ball Position Data to Fit on Field Image Dimensions
    xData = data["ball_position_x"] / 1.7
    yData = (data["ball_position_y"] / 2.2) + 180

    # Vertically Stacking X and Y Data
    kdeData = np.vstack([xData, yData])

    # Create 2 Dimensional Gaussian Kernel Density Estimator (KDE) To Identify Where Hits Are Concentrated
    kde = gaussian_kde(kdeData, bw_method = 0.9)

    # Load Field Image and Find Dimensions
    fieldImg = mpimg.imread("field.jpg")
    imgHeight, imgWidth, _ = fieldImg.shape

    # Create a Grid Covering Every Pixel of the Image
    yGrid, xGrid = np.mgrid[0:imgHeight, 0:imgWidth]

    # Convert Pixel Coordinates Into Ones that Match the Ball Position Data
    plotX = -250 + (xGrid / imgWidth) * 500
    plotY = (1 - yGrid / imgHeight) * 500  

    # Flatten Coordinates So Gaussian Kernel Density Estimator (KDE) Can Evaluate Every Point
    gridCoord = np.vstack([plotX.ravel(), plotY.ravel()])

    # Evaluate Gaussian Kernel Density Estimator (KDE) at Every Point 
    zDensity = kde(gridCoord).reshape(xGrid.shape)

    # Normalizing Density Values From 0 to 100 Range for Better Visualization
    zDensity = (zDensity - zDensity.min()) / (zDensity.max() - zDensity.min()) * 100

    # Create High DPI Figure for Visualization 
    fig, ax = plt.subplots(figsize = (8, 8), dpi = 1000)

    # Convert Image Dimensions To Floats Between 0 and 1 
    img = fieldImg.astype(float) / 255.0

    # Find Where Seating Stands Are By Seeing Where There is More Blue Than Red and Blue Is Over Certain Threshold
    blueColor = img[:, :, 2]
    redColor = img[:, :, 0]
    stands = (blueColor > redColor + 0.15) & (blueColor > 0.4)

    # Finding The Areas With High KDE Density (>70%) and When KDE Overlaps Stands
    threshold = np.percentile(zDensity, 65)
    overlap = (zDensity >= threshold) & stands
    
    # Create a Copy of the Image for Highlighting
    highlightStands = img.copy()

    # Highlight Overlapping Stands In Bright Red to Contrast With Blue     
    if np.any(overlap):
        highlightStands[overlap, 0] = 0.85 
        highlightStands[overlap, 1] = highlightStands[overlap, 1] * 0.1
        highlightStands[overlap, 2] = highlightStands[overlap, 2] * 0.1

    # Drawing Highlighted Stands Area
    ax.imshow(highlightStands, extent = [-250, 250, 0, 500], origin = 'upper', zorder = 0)

    # Drawing Dashed Boundary Around Highlighted Stands to See Better 
    if np.any(overlap):
        overlapNumbers = overlap.astype(int)
        ax.contour(plotX, plotY, overlapNumbers, levels = [0.5], colors = 'red',  linestyles = 'dashed', linewidths = 1.5, zorder = 5)
        
        # Placing Text Box That Says "Foul Zone" With Outline
        ax.text(0.5, 35, "Foul Zone", color = 'black', fontsize = 10, ha = 'center', va = 'center', zorder = 7,
            bbox = dict(boxstyle = 'round,pad=0.3', facecolor = 'white', alpha = 1, edgecolor = 'red', linewidth = 1, linestyle = 'dashed'))

    # Set the Number of Countour Levels to 10
    numLevels = 10
    zMask = np.ma.masked_less(zDensity, threshold)
    levels = np.linspace(threshold, zDensity.max(), numLevels)

    # Plotting Countour Levels Generated by KDE in Red
    ax.contourf(plotX, plotY, zMask, levels = levels, cmap = 'Reds', alpha = 0.5, zorder = 4)

    # Plotting Hit Data in Red as Scatter Plot
    ax.scatter(xData, yData, s = 15, color = 'red', linewidths = 0.5, zorder = 6, alpha = 0.8)

    # Setting Final Dimensions of Image
    ax.set_xlim(-250, 250)
    ax.set_ylim(0, 500)
    ax.set_aspect('equal')
    ax.axis('off')

    # Extracting Contextual Game Information
    halfInning = data["half_inning"].iloc[0]
    inningNumber = data['inning'].iloc[0]
    firstBase = data['on_1b'].iloc[0]
    secondBase = data['on_2b'].iloc[0]
    thirdBase = data['on_3b'].iloc[0]

    # Displaying Game Situation Of How Many Runners on Base and Which Base
    text = "Runner On "
    labels = ((firstBase, "1st"), (secondBase, "2nd"), (thirdBase, "3rd"),)
    text += ", ".join(label for base, label in labels if pd.notna(base))

    # Updating Label If No Runners on Base
    if len(text) < 12:
        text = "No Runners on Base"

    # Adding Plot Titles
    plt.title(f"\nLive Foul Ball Heatmap", fontsize = 20)
    fig.text(0.5, 0.85, f"{halfInning} {inningNumber} {text}", ha = 'center', fontsize = 10)
    fig.text(0.1, 0.1, f'Player A ({data['handed'].iloc[0]})', fontsize = 10)
