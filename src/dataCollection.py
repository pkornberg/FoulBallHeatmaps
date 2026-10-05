"""
Utility Functions for Data Collection
"""

import os
import glob
import pandas as pd
import numpy as np

def findFiles(teamCode, eventData) -> list:
    """
    Function to Final Either Ball Event or Ball Positions Data For Team

    Parameters
    ----------
    teamCode : str
        Anonymized Team Code to Collect Files

    eventData : bool
        True Fir Ball Event Data, False For Ball Position Data

    Returns
    -------
    files : list
        List Of Data Files
    """

    # Creating Empty Storage Array
    files = []
    
    # Builds the File Path
    if eventData:
        filePath = os.path.join("ball-events", teamCode, "**", "ball_events.csv")
    else: 
        filePath = os.path.join("ball-positions", teamCode, "**", "ball-positions.csv")

    # Getting All File Names
    fileNames = glob.glob(filePath, recursive = True)

    # Appending Each File to Array
    for name in fileNames:
        files.append(name)
    
    # Returning Files
    return files


def hitChartData(teamCodes) -> pd.DataFrame:
    """
    Function to Collect Data on Final Location of All Batted Balls For All Teams

    Parameters
    ----------
    teamCodes : list
        List of All Team Codes (Like 'ANI/ADQ')

    Returns
    -------
    data : pd.DataFrame
        Final Data Frame Containing Hit Location Data For All Teams
    """

    # Extracting Lineups and Hit Data
    lineups = pd.read_csv("lineups.csv")
    hitData = []

    # Looping Through Each Individual Team
    for team in teamCodes: 

        # Finding Files For Ball Event and Ball Position Data
        eventFiles = findFiles(team, True)
        positionFiles = findFiles(team, False)

        # Looping Through Each File
        for eventFile, positionFile in zip(eventFiles, positionFiles):

            # Collecting Ball Event Data For Hits (4) and Homeruns (11)
            eventData = pd.read_csv(eventFile)
            eventData = eventData[eventData['ball_eventcode'].isin([4, 11])]

            # Collecting Ball Position Data
            positionData = pd.read_csv(positionFile)

            # Calculating the Distance that Each Ball Traveled 
            positionData['dist_xy'] = np.sqrt(positionData.ball_position_x**2 + positionData.ball_position_y**2)
            
            # Only Keeping Ball Position With Longest Distance For Landing
            idx = positionData.groupby(['play_per_game'])['dist_xy'].idxmax()
            positionData = positionData.loc[idx]

            # Finding Lineups For Each Game
            gameString = eventData['game_string'].iloc[0]
            lineupsGame = lineups[lineups['game_string'] == gameString]

            # Merging Data Frames To Include Event, Position, and Lineup Data
            firstMerge = pd.merge(eventData, positionData, on = 'play_per_game')
            secondMerge = pd.merge(firstMerge, lineupsGame, on ='play_per_game')

            # Appending Merge to Array
            hitData.append(secondMerge)

    # Concatenating DataFrame to Include All Games
    data = pd.concat(hitData, ignore_index = True)

    # Removing Hit Data That Was Wrongly Classified as Ball Back to Pitcher
    data = data[~((data['ball_position_x'].between(-1, 1)) & (data['ball_position_y'] < 60))]

    # Returning Data Frame 
    return data
    