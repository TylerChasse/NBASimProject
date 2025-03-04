import copy
from nba_api.stats.static import teams
import random
from numpy.random import choice
from datetime import date
from pyFiles.scrape import readScheduleFile
from pyFiles import basicInfo as bi
from basicInfo import debugStats as ds
import pickle
from itertools import groupby


# functions that take into account opp stats
def getTwoPerc(team1, team2):
    team1TwoPerc = (team1.teamTwoPerc + team2.oppTwoPerc) / 2
    team2TwoPerc = (team2.teamTwoPerc + team1.oppTwoPerc) / 2
    return team1TwoPerc, team2TwoPerc

def getThreePerc(team1, team2):
    team1ThreePerc = (team1.teamThreePerc + team2.oppThreePerc) / 2
    team2ThreePerc = (team2.teamThreePerc + team1.oppThreePerc) / 2
    return team1ThreePerc, team2ThreePerc


def getOREBPerc(team1, team2):
    team1OREBPerc = team1.teamOREB / (team1.teamOREB + team2.teamDREB)
    team2OREBPerc = team2.teamOREB / (team2.teamOREB + team1.teamDREB)
    return team1OREBPerc, team2OREBPerc


def getDREBPerc(team1, team2):
    team1DREBPerc = team1.teamDREB / (team1.teamDREB + team2.teamOREB)
    team2DREBPerc = team2.teamDREB / (team2.teamDREB + team1.teamOREB)
    return team1DREBPerc, team2DREBPerc


def getTurnoverPerc(team1, team2):
    team1TurnoverPerc = (team1.teamTurnovers + team2.oppTurnovers) / 2
    team2TurnoverPerc = (team2.teamTurnovers + team1.oppTurnovers) / 2
    return team1TurnoverPerc, team2TurnoverPerc


def getPFPerc(team1, team2):
    team1PFPerc = (team1.teamPF + team2.oppPF) / 2
    team2PFPerc = (team2.teamPF + team1.oppPF) / 2
    return team1PFPerc, team2PFPerc


def getShootingFoulPerc(team1, team2):
    team1ShootingFoulPerc = (team1.shootingFoulChance + team2.shootingFoulDrawnChance) / 2
    team2ShootingFoulPerc = (team2.shootingFoulChance + team1.shootingFoulDrawnChance) / 2
    #print(team1.shootingFoulChance, team2.shootingFoulDrawnChance) ###
    return team1ShootingFoulPerc, team2ShootingFoulPerc

def singleGameSimDebug(team1Abb, team2Abb, team1=None, team2=None):
    ds['games'] += 1
    if team1Abb == 'Select' or team2Abb == 'Select':
        return 'Please select two teams'
    if team1 == None:
        team1 = Teams[team1Abb]
    if team2 == None:
        team2 = Teams[team2Abb]

    # get team stats
    team1TwoPerc, team2TwoPerc = getTwoPerc(team1, team2)
    team1ThreePerc, team2ThreePerc = getThreePerc(team1, team2)
    team1OREBPerc, team2OREBPerc = getOREBPerc(team1, team2)
    team1DREBPerc, team2DREBPerc = getDREBPerc(team1, team2)
    team1TurnoverPerc, team2TurnoverPerc = getTurnoverPerc(team1, team2)
    team1PFPerc, team2PFPerc = getPFPerc(team1, team2)
    team1ShootingFoulPerc, team2ShootingFoulPerc = getShootingFoulPerc(team1, team2)
    team1ShotFrequency = 1 - (team1TurnoverPerc + team2PFPerc)
    team2ShotFrequency = 1 - (team2TurnoverPerc + team1PFPerc)
    # nba avg
    timePerPossession = 14.4

    team1Stats = {"2%": team1TwoPerc, "3%": team1ThreePerc, "OREB%": team1OREBPerc, "DREB%": team1DREBPerc,
                  "TO%": team1TurnoverPerc, "PF%": team1PFPerc, "SF%": team1ShootingFoulPerc,
                  "ShotFreq": team1ShotFrequency}
    team2Stats = {"2%": team2TwoPerc, "3%": team2ThreePerc, "OREB%": team2OREBPerc, "DREB%": team2DREBPerc,
                  "TO%": team2TurnoverPerc, "PF%": team2PFPerc, "SF%": team2ShootingFoulPerc,
                  "ShotFreq": team2ShotFrequency}

    quarter = 1
    team1Score = 0
    team2Score = 0
    possession = random.randint(1, 2)

    # start game
    while quarter <= 4 or (quarter >= 5 and team1Score == team2Score):
        team1Fouls = 0
        team1Last2MinFouls = 0
        team2Fouls = 0
        team2Last2MinFouls = 0
        if quarter <= 4:
            time = 720
            bonus = 5
        # overtime
        elif quarter >= 5 and team1Score == team2Score:
            ds['overtimes'] += 1
            time = 300
            bonus = 4
        while time > 0:
            ds['possessions'] += 1
            possessionPoints = 0
            addTime = False
            # set offensive and defensive teams
            if possession == 1:
                off = team1
                offStats = team1Stats
                defStats = team2Stats
                defFouls = team2Fouls
                defLast2MinFouls = team2Last2MinFouls
            else:
                off = team2
                offStats = team2Stats
                defStats = team1Stats
                defFouls = team1Fouls
                defLast2MinFouls = team1Last2MinFouls
            # sim possession
            outcome = choice(["Shot", "Turnover", "Foul"], 1,
                             p=[offStats['ShotFreq'], offStats['TO%'], defStats['PF%']])
            if outcome == "Shot":
                ds['shots'] += 1
                shotType = choice(["Two", "Three"], 1, p=[off.twoFrequency, off.threeFrequency])
                if shotType == "Two":
                    ds['2s'] += 1
                    shot = choice(["Make", "Miss"], 1, p=[offStats['2%'], (1 - offStats['2%'])])
                    if shot == "Make":
                        ds['made2s'] += 1
                        possessionPoints += 2
                        possession = 2
                    elif shot == "Miss":
                        possession = choice([1, 2], 1, p=[offStats['OREB%'], defStats['DREB%']])
                        if possession == 1:
                            ds['OREBs'] += 1
                            # right now oreb doesn't start new possession, so time and possession taken off for possession
                            # is put back on
                            addTime = True
                        else:
                            ds['DREBs'] += 1
                if shotType == "Three":
                    ds['3s'] += 1
                    shot = choice(["Make", "Miss"], 1, p=[offStats['3%'], (1 - offStats['3%'])])
                    if shot == "Make":
                        ds['made3s'] += 1
                        possessionPoints += 3
                        possession = 2
                    elif shot == "Miss":
                        possession = choice([1, 2], 1, p=[offStats['OREB%'], defStats['DREB%']])
                        if possession == 1:
                            ds['OREBs'] += 1
                            addTime = True
                        else:
                            ds['DREBs'] += 1
            elif outcome == "Turnover":
                ds['turnovers'] += 1
                possession = 2
            elif outcome == "Foul":
                ds['fouls'] += 1
                defFouls += 1
                if time <= 120:
                    defLast2MinFouls += 1
                foulType = choice(["Common", "Shooting"], 1, p=[(1 - defStats['SF%']), defStats['SF%']])
                if foulType == "Shooting":
                    ds['shootingFouls'] += 1
                    foulType = choice(["Shooting", "And1_2", "And1_3"], 1,
                                      p=[(1 - off.twoPointAnd1Chance - off.threePointAnd1Chance),
                                         off.twoPointAnd1Chance, off.threePointAnd1Chance])
                if foulType == "Common" and (defFouls < bonus and defLast2MinFouls < 2):
                    ds['commonFouls'] += 1
                    possession = 1
                elif foulType == "Common" and (defFouls >= bonus or defLast2MinFouls >= 2):
                    ds['commonFouls'] += 1
                    foulType = "Shooting"
                elif foulType == "And1_2":
                    ds['shots'] += 1
                    ds['twoAnd1s'] += 1
                    ds['2s'] += 1
                    ds['made2s'] += 1
                    ds['freeThrows'] += 1
                    possessionPoints += 2
                    freeThrow = choice(["Make", "Miss"], 1,
                                       p=[off.teamFreeThrowPerc, (1 - off.teamFreeThrowPerc)])
                    if freeThrow == "Make":
                        ds['madeFreeThrows'] += 1
                        possessionPoints += 1
                        possession = 2
                    elif freeThrow == "Miss":
                        possession = choice([1, 2], 1, p=[offStats['OREB%'], defStats['DREB%']])
                        if possession == 1:
                            ds['OREBs'] += 1
                            addTime = True
                        else:
                            ds['DREBs'] += 1
                elif foulType == "And1_3":
                    ds['shots'] += 1
                    ds['threeAnd1s'] += 1
                    ds['3s'] += 1
                    ds['made3s'] += 1
                    ds['freeThrows'] += 1
                    possessionPoints += 3
                    freeThrow = choice(["Make", "Miss"], 1,
                                       p=[off.teamFreeThrowPerc, (1 - off.teamFreeThrowPerc)])
                    if freeThrow == "Make":
                        ds['madeFreeThrows'] += 1
                        possessionPoints += 1
                        possession = 2
                    elif freeThrow == "Miss":
                        possession = choice([1, 2], 1, p=[offStats['OREB%'], defStats['DREB%']])
                        if possession == 1:
                            ds['OREBs'] += 1
                            addTime = True
                        else:
                            ds['DREBs'] += 1
                if foulType == "Shooting":
                    ds['freeThrows'] += 2
                    freeThrow1 = choice(["Make", "Miss"], 1,
                                        p=[off.teamFreeThrowPerc, (1 - off.teamFreeThrowPerc)])
                    if freeThrow1 == "Make":
                        ds['madeFreeThrows'] += 1
                        possessionPoints += 1
                    elif freeThrow1 == "Miss":
                        possessionPoints += 0
                    freeThrow2 = choice(["Make", "Miss"], 1,
                                        p=[off.teamFreeThrowPerc, (1 - off.teamFreeThrowPerc)])
                    if freeThrow2 == "Make":
                        ds['madeFreeThrows'] += 1
                        possessionPoints += 1
                        possession = 2
                    elif freeThrow2 == "Miss":
                        possession = choice([1, 2], 1, p=[offStats['OREB%'], defStats['DREB%']])
                        if possession == 1:
                            ds['OREBs'] += 1
                            addTime = True
                        else:
                            ds['DREBs'] += 1
            # add points and handle possession
            if off == team1:
                ds['team1Score'] += 1
                team1Score += possessionPoints
            else:
                ds['team2Score'] += 1
                team2Score += possessionPoints
                # in simPoss, possession is 1 for offense, 2 for defense, not team1 and team2, so it has to be flipped
                # after team2 is on offense
                if possession == 1:
                    possession = 2
                else:
                    possession = 1
            if not addTime:
                time -= timePerPossession
            # if OREB, still same poss, so don't subtract time or add another possession for next
            else:
                ds['possessions'] -= 1
        quarter += 1

    if team1Score > team2Score:
        ds['marginOfVictory'] += (team1Score - team2Score)
        #print(team1Abb + " beat " + team2Abb + " by a score of " + str(team1Score) + " to " + str(team2Score))
        return team1Abb, team1Score, team2Score
    else:
        ds['marginOfVictory'] += (team2Score - team1Score)
        #print(team2Abb + " beat " + team1Abb + " by a score of " + str(team2Score) + " to " + str(team1Score))
        return team2Abb, team1Score, team2Score

def singleGameSim(team1Abb, team2Abb, team1=None, team2=None):
    if team1Abb == 'Select' or team2Abb == 'Select':
        return 'Please select two teams'
    if team1 == None:
        team1 = Teams[team1Abb]
    if team2 == None:
        team2 = Teams[team2Abb]

    # get team stats
    team1TwoPerc, team2TwoPerc = getTwoPerc(team1, team2)
    team1ThreePerc, team2ThreePerc = getThreePerc(team1, team2)
    team1OREBPerc, team2OREBPerc = getOREBPerc(team1, team2)
    team1DREBPerc, team2DREBPerc = getDREBPerc(team1, team2)
    team1TurnoverPerc, team2TurnoverPerc = getTurnoverPerc(team1, team2)
    team1PFPerc, team2PFPerc = getPFPerc(team1, team2)
    team1ShootingFoulPerc, team2ShootingFoulPerc = getShootingFoulPerc(team1, team2)
    team1ShotFrequency = 1 - (team1TurnoverPerc + team2PFPerc)
    team2ShotFrequency = 1 - (team2TurnoverPerc + team1PFPerc)
    #(print(f'shot, to, pf %: {team1ShotFrequency, team1TurnoverPerc, team2PFPerc}'))
    # nba avg
    timePerPossession = 14.4

    team1Stats = {"2%": team1TwoPerc, "3%": team1ThreePerc, "OREB%": team1OREBPerc, "DREB%": team1DREBPerc,
                  "TO%": team1TurnoverPerc, "PF%": team1PFPerc, "SF%": team1ShootingFoulPerc,
                  "ShotFreq": team1ShotFrequency}
    team2Stats = {"2%": team2TwoPerc, "3%": team2ThreePerc, "OREB%": team2OREBPerc, "DREB%": team2DREBPerc,
                  "TO%": team2TurnoverPerc, "PF%": team2PFPerc, "SF%": team2ShootingFoulPerc,
                  "ShotFreq": team2ShotFrequency}

    quarter = 1
    team1Score = 0
    team2Score = 0
    possession = random.randint(1, 2)

    # start game
    while quarter <= 4 or (quarter >= 5 and team1Score == team2Score):
        team1Fouls = 0
        team1Last2MinFouls = 0
        team2Fouls = 0
        team2Last2MinFouls = 0
        if quarter <= 4:
            time = 720
            bonus = 5
        # overtime
        elif quarter >= 5 and team1Score == team2Score:
            time = 300
            bonus = 4
        while time > 0:
            possessionPoints = 0
            addTime = False
            # set offensive and defensive teams
            if possession == 1:
                off = team1
                offStats = team1Stats
                defStats = team2Stats
                defFouls = team2Fouls
                defLast2MinFouls = team2Last2MinFouls
            else:
                off = team2
                offStats = team2Stats
                defStats = team1Stats
                defFouls = team1Fouls
                defLast2MinFouls = team1Last2MinFouls
            # sim possession
            outcome = choice(["Shot", "Turnover", "Foul"], 1,
                             p=[offStats['ShotFreq'], offStats['TO%'], defStats['PF%']])
            if outcome == "Shot":
                shotType = choice(["Two", "Three"], 1, p=[off.twoFrequency, off.threeFrequency])
                if shotType == "Two":
                    shot = choice(["Make", "Miss"], 1, p=[offStats['2%'], (1 - offStats['2%'])])
                    if shot == "Make":
                        possessionPoints += 2
                        possession = 2
                    elif shot == "Miss":
                        possession = choice([1, 2], 1, p=[offStats['OREB%'], defStats['DREB%']])
                        if possession == 1:
                            # right now oreb doesn't start new possession, so time and possession taken off for possession
                            # is put back on
                            addTime = True
                if shotType == "Three":
                    shot = choice(["Make", "Miss"], 1, p=[offStats['3%'], (1 - offStats['3%'])])
                    if shot == "Make":
                        possessionPoints += 3
                        possession = 2
                    elif shot == "Miss":
                        possession = choice([1, 2], 1, p=[offStats['OREB%'], defStats['DREB%']])
                        if possession == 1:
                            addTime = True
            elif outcome == "Turnover":
                possession = 2
            elif outcome == "Foul":
                defFouls += 1
                if time <= 120:
                    defLast2MinFouls += 1
                foulType = choice(["Common", "Shooting"], 1, p=[(1 - defStats['SF%']), defStats['SF%']])
                if foulType == "Shooting":
                    foulType = choice(["Shooting", "And1_2", "And1_3"], 1,
                                      p=[(1 - off.twoPointAnd1Chance - off.threePointAnd1Chance),
                                         off.twoPointAnd1Chance, off.threePointAnd1Chance])
                if foulType == "Common" and (defFouls < bonus and defLast2MinFouls < 2):
                    possession = 1
                elif foulType == "Common" and (defFouls >= bonus or defLast2MinFouls >= 2):
                    foulType = "Shooting"
                elif foulType == "And1_2":
                    possessionPoints += 2
                    freeThrow = choice(["Make", "Miss"], 1,
                                       p=[off.teamFreeThrowPerc, (1 - off.teamFreeThrowPerc)])
                    if freeThrow == "Make":
                        possessionPoints += 1
                        possession = 2
                    elif freeThrow == "Miss":
                        possession = choice([1, 2], 1, p=[offStats['OREB%'], defStats['DREB%']])
                        if possession == 1:
                            addTime = True
                elif foulType == "And1_3":
                    possessionPoints += 3
                    freeThrow = choice(["Make", "Miss"], 1,
                                       p=[off.teamFreeThrowPerc, (1 - off.teamFreeThrowPerc)])
                    if freeThrow == "Make":
                        possessionPoints += 1
                        possession = 2
                    elif freeThrow == "Miss":
                        possession = choice([1, 2], 1, p=[offStats['OREB%'], defStats['DREB%']])
                        if possession == 1:
                            addTime = True
                if foulType == "Shooting":
                    freeThrow1 = choice(["Make", "Miss"], 1,
                                        p=[off.teamFreeThrowPerc, (1 - off.teamFreeThrowPerc)])
                    if freeThrow1 == "Make":
                        possessionPoints += 1
                    elif freeThrow1 == "Miss":
                        possessionPoints += 0
                    freeThrow2 = choice(["Make", "Miss"], 1,
                                        p=[off.teamFreeThrowPerc, (1 - off.teamFreeThrowPerc)])
                    if freeThrow2 == "Make":
                        possessionPoints += 1
                        possession = 2
                    elif freeThrow2 == "Miss":
                        possession = choice([1, 2], 1, p=[offStats['OREB%'], defStats['DREB%']])
                        if possession == 1:
                            # print("OREB")
                            addTime = True
            # add points and handle possession
            if off == team1:
                team1Score += possessionPoints
            else:
                team2Score += possessionPoints
                # in simPoss, possession is 1 for offense, 2 for defense, not team1 and team2, so it has to be flipped
                # after team2 is on offense
                if possession == 1:
                    possession = 2
                else:
                    possession = 1
            # if OREB, still same poss, so don't subtract time
            if not addTime:
                time -= timePerPossession
        quarter += 1

    if team1Score > team2Score:
        #print(team1Abb + " beat " + team2Abb + " by a score of " + str(team1Score) + " to " + str(team2Score))
        return team1Abb, team1Score, team2Score
    else:
        #print(team2Abb + " beat " + team1Abb + " by a score of " + str(team2Score) + " to " + str(team1Score))
        return team2Abb, team1Score, team2Score


def seriesSim(team1Abb, team2Abb, team1=None, team2=None):
    if team1Abb == 'Select' or team2Abb == 'Select':
        return 'Please select two teams'
    if team1 == None:
        team1 = Teams[team1Abb]
    if team2 == None:
        team2 = Teams[team2Abb]
    team1Wins = 0
    team2Wins = 0
    while team1Wins < 4 and team2Wins < 4:
        if bi.DEBUG_STATS:
            winner, team1Score, team2Score = singleGameSimDebug(team1Abb, team2Abb, team1, team2)
        else:
            winner, team1Score, team2Score = singleGameSim(team1Abb, team2Abb, team1, team2)
        if team1Score > team2Score:
            team1Wins += 1
        elif team2Score > team1Score:
            team2Wins += 1
    if team1Wins == 4:
        report = team1Abb + " wins the series vs " + team2Abb + " 4 games to " + str(team2Wins)
        return team1Abb, team1Wins, team2Wins, report
    elif team2Wins == 4:
        report = team2Abb + " wins the series vs " + team1Abb + " 4 games to " + str(team1Wins)
        return team2Abb, team1Wins, team2Wins, report


def seasonSim():
    with open('../pklFiles/scrapeScores.pickle', 'rb') as pklFile:
        scores = pickle.load(pklFile)
    pklFile.close()
    for team in Teams.values():
        team.divisionWinner = False
        team.playoffTeam = False
    seasonReport = ""
    teamsList, eastTeamsList, westTeamsList = initializeTeams()
    if bi.SEASONSTART:
        for key, value in teamsList.items():
            teamsList[key].wins = 0
            teamsList[key].losses = 0
    schedule = readScheduleFile()
    today = date.today()
    today = int(today.strftime("%Y%m%d"))
    # for day in schedule file
    for key, value in schedule.items():
        # if day is already past, skip
        if key < bi.SEASONSTARTDATE or key < today:
            continue
        else:
            teamNames = value
            numOfGames = (len(teamNames) / 2)
            gamesPlayed = 0
            # sim each game in day
            while gamesPlayed < numOfGames:
                team1Name = teamNames[gamesPlayed * 2]
                team2Name = teamNames[(gamesPlayed * 2) + 1]
                team1Abb = convertNameToAbb(team1Name)
                team2Abb = convertNameToAbb(team2Name)
                # sim game
                if bi.DEBUG_STATS:
                    winner, team1Score, team2Score = singleGameSimDebug(team1Abb, team2Abb, teamsList[team1Name],
                                                                   teamsList[team2Name])
                else:
                    winner, team1Score, team2Score = singleGameSim(team1Abb, team2Abb, teamsList[team1Name],
                                                                   teamsList[team2Name])
                # add to team records
                if winner == team1Abb:
                    teamsList[team1Name].wins += 1
                    teamsList[team2Name].losses += 1
                    # add to score log
                    scores.append([team1Abb, team2Abb])
                if winner == team2Abb:
                    teamsList[team2Name].wins += 1
                    teamsList[team1Name].losses += 1
                    # add to score log
                    scores.append([team2Abb, team1Abb])
                # add to teams total points
                teamsList[team1Name].points += team1Score
                teamsList[team2Name].points += team2Score
                gamesPlayed += 1
    seasonReport += "Season Standings:\n"
    if bi.DEBUG_STATS:
        print(scores)
    eastTeamsList, westTeamsList = seedTeams(eastTeamsList, westTeamsList, scores)
    # get team records
    seasonReport += "EAST:\n"
    for team in eastTeamsList:
        seasonReport += team[1].abbreviation + ": " + str(team[1].wins) + "-" + str(team[1].losses) + "\n"
    seasonReport += "\nWEST:\n"
    for team in westTeamsList:
        seasonReport += team[1].abbreviation + ": " + str(team[1].wins) + "-" + str(team[1].losses) + "\n"
    # seed teams

    east1 = eastTeamsList[0][1].abbreviation
    east2 = eastTeamsList[1][1].abbreviation
    east3 = eastTeamsList[2][1].abbreviation
    east4 = eastTeamsList[3][1].abbreviation
    east5 = eastTeamsList[4][1].abbreviation
    east6 = eastTeamsList[5][1].abbreviation
    east7 = eastTeamsList[6][1].abbreviation
    east8 = eastTeamsList[7][1].abbreviation
    east9 = eastTeamsList[8][1].abbreviation
    east10 = eastTeamsList[9][1].abbreviation
    west1 = westTeamsList[0][1].abbreviation
    west2 = westTeamsList[1][1].abbreviation
    west3 = westTeamsList[2][1].abbreviation
    west4 = westTeamsList[3][1].abbreviation
    west5 = westTeamsList[4][1].abbreviation
    west6 = westTeamsList[5][1].abbreviation
    west7 = westTeamsList[6][1].abbreviation
    west8 = westTeamsList[7][1].abbreviation
    west9 = westTeamsList[8][1].abbreviation
    west10 = westTeamsList[9][1].abbreviation

    # EAST PLAY IN
    # 7 vs 8
    seasonReport += "\nEast Play In\n"
    if bi.DEBUG_STATS:
        winner, team1Score, team2Score = singleGameSimDebug(east7, east8, teamsList[convertAbbToName(east7)],
                                                       teamsList[convertAbbToName(east8)])
    else:
        winner, team1Score, team2Score = singleGameSim(east7, east8, teamsList[convertAbbToName(east7)],
                                                       teamsList[convertAbbToName(east8)])
    if winner == east8:
        temp = east7
        east7 = east8
        east8 = temp
    seasonReport += east7 + " beat " + east8 + " to get the 7 seed\n"
    # 9 vs 10
    if bi.DEBUG_STATS:
        winner, team1Score, team2Score = singleGameSimDebug(east9, east10, teamsList[convertAbbToName(east9)],
                                                       teamsList[convertAbbToName(east10)])
    else:
        winner, team1Score, team2Score = singleGameSim(east9, east10, teamsList[convertAbbToName(east9)],
                                                       teamsList[convertAbbToName(east10)])
    if winner == east10:
        temp = east9
        east9 = east10
        east10 = temp
    seasonReport += east9 + " beat " + east10 + " to stay in the play in\n"
    # 8 vs 9
    if bi.DEBUG_STATS:
        winner, team1Score, team2Score = singleGameSimDebug(east8, east9, teamsList[convertAbbToName(east8)],
                                                       teamsList[convertAbbToName(east9)])
    else:
        winner, team1Score, team2Score = singleGameSim(east8, east9, teamsList[convertAbbToName(east8)],
                                                       teamsList[convertAbbToName(east9)])
    if winner == east9:
        temp = east8
        east8 = east9
        east9 = temp
    seasonReport += east8 + " beat " + east9 + " to get the 8 seed\n"
    # WEST PLAY IN
    # 7 vs 8
    seasonReport += "\nWest Play In\n"
    if bi.DEBUG_STATS:
        winner, team1Score, team2Score = singleGameSimDebug(west7, west8, teamsList[convertAbbToName(west7)],
                                                       teamsList[convertAbbToName(west8)])
    else:
        winner, team1Score, team2Score = singleGameSim(west7, west8, teamsList[convertAbbToName(west7)],
                                                       teamsList[convertAbbToName(west8)])
    if winner == west8:
        temp = west7
        west7 = west8
        west8 = temp
    seasonReport += west7 + " beat " + west8 + " to get the 7 seed\n"
    # 9 vs 10
    if bi.DEBUG_STATS:
        winner, team1Score, team2Score = singleGameSimDebug(west9, west10, teamsList[convertAbbToName(west9)],
                                                       teamsList[convertAbbToName(west10)])
    else:
        winner, team1Score, team2Score = singleGameSim(west9, west10, teamsList[convertAbbToName(west9)],
                                                       teamsList[convertAbbToName(west10)])
    if winner == west10:
        temp = west9
        west9 = west10
        west10 = temp
    seasonReport += west9 + " beat " + west10 + " to stay in the play in\n"
    # 8 vs 9
    if bi.DEBUG_STATS:
        winner, team1Score, team2Score = singleGameSimDebug(west8, west9, teamsList[convertAbbToName(west8)],
                                                       teamsList[convertAbbToName(west9)])
    else:
        winner, team1Score, team2Score = singleGameSim(west8, west9, teamsList[convertAbbToName(west8)],
                                                       teamsList[convertAbbToName(west9)])
    if winner == west9:
        temp = west8
        west8 = west9
        west9 = temp
    seasonReport += west8 + " beat " + west9 + " to get the 8 seed\n"
    # EAST 1ST RND
    seasonReport += "\nEast Round 1:\n"
    winnerEast1_8, team1Wins, team2Wins, report = seriesSim(east1, east8, teamsList[convertAbbToName(east1)],
                                                            teamsList[convertAbbToName(east8)])
    seasonReport += report + '\n'
    winnerEast2_7, team1Wins, team2Wins, report = seriesSim(east2, east7, teamsList[convertAbbToName(east2)],
                                                            teamsList[convertAbbToName(east7)])
    seasonReport += report + '\n'
    winnerEast3_6, team1Wins, team2Wins, report = seriesSim(east3, east6, teamsList[convertAbbToName(east3)],
                                                            teamsList[convertAbbToName(east6)])
    seasonReport += report + '\n'
    winnerEast4_5, team1Wins, team2Wins, report = seriesSim(east4, east5, teamsList[convertAbbToName(east4)],
                                                            teamsList[convertAbbToName(east5)])
    seasonReport += report + '\n'
    # WEST 1ST RND
    seasonReport += "\nWest Round 1:\n"
    winnerWest1_8, team1Wins, team2Wins, report = seriesSim(west1, west8, teamsList[convertAbbToName(west1)],
                                                            teamsList[convertAbbToName(west8)])
    seasonReport += report + '\n'
    winnerWest2_7, team1Wins, team2Wins, report = seriesSim(west2, west7, teamsList[convertAbbToName(west2)],
                                                            teamsList[convertAbbToName(west7)])
    seasonReport += report + '\n'
    winnerWest3_6, team1Wins, team2Wins, report = seriesSim(west3, west6, teamsList[convertAbbToName(west3)],
                                                            teamsList[convertAbbToName(west6)])
    seasonReport += report + '\n'
    winnerWest4_5, team1Wins, team2Wins, report = seriesSim(west4, west5, teamsList[convertAbbToName(west4)],
                                                            teamsList[convertAbbToName(west5)])
    seasonReport += report + '\n'
    # EAST 2ND RND
    seasonReport += "\nEast Semifinals:\n"
    winnerEastSemis1, team1Wins, team2Wins, report = seriesSim(winnerEast1_8, winnerEast4_5,
                                                               teamsList[convertAbbToName(winnerEast1_8)],
                                                               teamsList[convertAbbToName(winnerEast4_5)])
    seasonReport += report + '\n'
    winnerEastSemis2, team1Wins, team2Wins, report = seriesSim(winnerEast2_7, winnerEast3_6,
                                                               teamsList[convertAbbToName(winnerEast2_7)],
                                                               teamsList[convertAbbToName(winnerEast3_6)])
    seasonReport += report + '\n'
    # WEST 2ND RND
    seasonReport += "\nWest Semifinals:\n"
    winnerWestSemis1, team1Wins, team2Wins, report = seriesSim(winnerWest1_8, winnerWest4_5,
                                                               teamsList[convertAbbToName(winnerWest1_8)],
                                                               teamsList[convertAbbToName(winnerWest4_5)])
    seasonReport += report + '\n'
    winnerWestSemis2, team1Wins, team2Wins, report = seriesSim(winnerWest2_7, winnerWest3_6,
                                                               teamsList[convertAbbToName(winnerWest2_7)],
                                                               teamsList[convertAbbToName(winnerWest3_6)])
    seasonReport += report + '\n'
    # EAST FINALS
    seasonReport += "\nEast Finals:\n"
    winnerEastFinals, team1Wins, team2Wins, report = seriesSim(winnerEastSemis1, winnerEastSemis2,
                                                               teamsList[convertAbbToName(winnerEastSemis1)],
                                                               teamsList[convertAbbToName(winnerEastSemis2)])
    seasonReport += report + '\n'
    # WEST FINALS
    seasonReport += "\nWest Finals:\n"
    winnerWestFinals, team1Wins, team2Wins, report = seriesSim(winnerWestSemis1, winnerWestSemis2,
                                                               teamsList[convertAbbToName(winnerWestSemis1)],
                                                               teamsList[convertAbbToName(winnerWestSemis2)])
    seasonReport += report + '\n'
    # FINALS
    seasonReport += "\nNBA Finals:\n"
    winnerFinals, team1WinsFinals, team2WinsFinals, report = seriesSim(winnerEastFinals, winnerWestFinals,
                                                                       teamsList[convertAbbToName(winnerEastFinals)],
                                                                       teamsList[convertAbbToName(winnerWestFinals)])
    seasonReport += report + '\n'
    seasonReport += winnerFinals + " wins the finals!\n"

    if bi.DEBUG_STATS:
        for key, value in ds.items():
            print(f"{key}: {value}")
        print(f"2%: {ds['made2s'] / ds['2s']}")
        print(f"3%: {ds['made3s'] / ds['3s']}")
        print(f"FT%: {ds['madeFreeThrows'] / ds['freeThrows']}")
        print(f"Shot%: {ds['shots'] / ds['possessions']}")
        print(f"TO%: {ds['turnovers'] / ds['possessions']}")
        print(f"PF%: {ds['fouls'] / ds['possessions']}")
        print(f"Team 1 Avg Score: {ds['team1Score'] / ds['games']}")
        print(f"Team 2 Avg Score: {ds['team2Score'] / ds['games']}")
        print(f"Avg Margin of Victory: {ds['marginOfVictory'] / ds['games']}")
        print(f"Possessions a game: {ds['possessions'] / ds['games']}")

    return seasonReport


def seedTeams(eastTeamsList, westTeamsList, scores):
    # sort teams by wins
    # East
    seededTeamsEast = sorted(eastTeamsList.items(), key=lambda x: x[1].wins, reverse=True)

    # group by wins to tiebreak teams with same num of wins
    eastGroupedByWins = {wins: list(group) for wins, group in groupby(seededTeamsEast, key=lambda item: item[1].wins)}
    # mark east playoff teams
    eastPlayoffTeamsGroups = {}
    eastNumOfTeams = 0
    for wins, group in eastGroupedByWins.items():
        if eastNumOfTeams >= 10:
            break
        for team in group:
            team[1].playoffTeam = True
        eastNumOfTeams += len(group)
        eastPlayoffTeamsGroups[wins] = group

    # West
    seededTeamsWest = sorted(westTeamsList.items(), key=lambda x: x[1].wins, reverse=True)
    westGroupedByWins = {wins: list(group) for wins, group in
                         groupby(seededTeamsWest, key=lambda item: item[1].wins)}
    # mark playoff teams
    westPlayoffTeamsGroups = {}
    westNumOfTeams = 0
    for wins, group in westGroupedByWins.items():
        if westNumOfTeams >= 10:
            break
        for team in group:
            team[1].playoffTeam = True
        westNumOfTeams += len(group)
        westPlayoffTeamsGroups[wins] = group

    # set east division winners
    eastDivisions = [[], [], []]
    for team in seededTeamsEast:
        if team[1].division == 'Atlantic':
            eastDivisions[0].append(team[1])
        elif team[1].division == 'Central':
            eastDivisions[1].append(team[1])
        else:
            eastDivisions[2].append(team[1])
    # group divisions by wins to find winner/needed tiebreakers for winner
    for division in eastDivisions:
        division = {wins: list(group) for wins, group in groupby(division, key=lambda item: item.wins)}
        # if first group in division is only one team, then no need for tiebreaker
        firstGroup = next(iter(division.values()))
        if len(firstGroup) == 1:
            firstGroup[0].divisionWinner = True
        else:
            divisionWinner = breakTiebreaker(scores, *firstGroup, divisionWinner=True,
                                             eastPlayoffTeamsGroups=eastPlayoffTeamsGroups.values(),
                                             westPlayoffTeamsGroups=westPlayoffTeamsGroups.values())
            divisionWinner.divisionWinner = True

    # set west division winners
    westDivisions = [[], [], []]
    for team in seededTeamsWest:
        if team[1].division == 'Northwest':
            westDivisions[0].append(team[1])
        elif team[1].division == 'Pacific':
            westDivisions[1].append(team[1])
        else:
            westDivisions[2].append(team[1])
    # group divisions by wins to find winner/needed tiebreakers for winner
    for division in westDivisions:
        division = {wins: list(group) for wins, group in groupby(division, key=lambda item: item.wins)}
        firstGroup = next(iter(division.values()))
        if len(firstGroup) == 1:
            firstGroup[0].divisionWinner = True
        else:
            divisionWinner = breakTiebreaker(scores, *firstGroup, divisionWinner=True,
                                             eastPlayoffTeamsGroups=eastPlayoffTeamsGroups.values(),
                                             westPlayoffTeamsGroups=westPlayoffTeamsGroups.values())
            divisionWinner.divisionWinner = True

    # EAST tiebreakers
    # used to check if first group in loop below
    firstGroupBool = True
    # .values() instead of .items() ???
    for wins, group in reversed(eastPlayoffTeamsGroups.items()):
        # two team tiebreaker
        if len(group) == 2:
            tieBreakWinner = breakTiebreaker(scores, group[0][1], group[1][1],
                                             eastPlayoffTeamsGroups=eastPlayoffTeamsGroups.values(),
                                             westPlayoffTeamsGroups=westPlayoffTeamsGroups.values())
            # seeds stay as is
            if tieBreakWinner == group[0][1]:
                if firstGroupBool and eastNumOfTeams > 10:
                    # in this case group[1][1] is the 11th team after losing tiebreaker and no longer a playoff team
                    group[1][1].playoffTeam = False
                    if bi.DEBUG_STATS:
                        print(f'{group[1][1].abbreviation} no longer a playoff team')
            # seeds swap
            elif tieBreakWinner == group[1][1]:
                seededTeamsEast[eastNumOfTeams-2], seededTeamsEast[eastNumOfTeams-1] = seededTeamsEast[eastNumOfTeams-1], seededTeamsEast[eastNumOfTeams-2]
                if firstGroupBool and eastNumOfTeams > 10:
                    # in this case group[0][1] is the 11th team after losing tiebreaker and no longer a playoff team
                    group[0][1].playoffTeam = False
                    if bi.DEBUG_STATS:
                        print(f'{group[0][1].abbreviation} no longer a playoff team')
        elif len(group) > 2:
            print("Multiple team tiebreaker not implemented yet")
        eastNumOfTeams -= len(group)
        firstGroupBool = False

    # WEST tiebreakers
    # used to check if first group in loop below
    firstGroupBool = True
    for wins, group in reversed(westPlayoffTeamsGroups.items()):
        # two team tiebreaker
        if len(group) == 2:
            tieBreakWinner = breakTiebreaker(scores, group[0][1], group[1][1],
                                             eastPlayoffTeamsGroups=eastPlayoffTeamsGroups.values(),
                                             westPlayoffTeamsGroups=westPlayoffTeamsGroups.values())
            # seeds stay as is
            if tieBreakWinner == group[0][1]:
                if firstGroupBool and westNumOfTeams > 10:
                    # in this case group[1][1] is the 11th team after losing tiebreaker and no longer a playoff team
                    group[1][1].playoffTeam = False
                    if bi.DEBUG_STATS:
                        print(f'{group[1][1].abbreviation} no longer a playoff team')
            # seeds swap
            elif tieBreakWinner == group[1][1]:
                seededTeamsWest[westNumOfTeams - 2], seededTeamsWest[westNumOfTeams - 1] = seededTeamsWest[westNumOfTeams - 1], seededTeamsWest[westNumOfTeams - 2]
                if firstGroupBool and westNumOfTeams > 10:
                    # in this case group[0][1] is the 11th team after losing tiebreaker and no longer a playoff team
                    group[0][1].playoffTeam = False
                    if bi.DEBUG_STATS:
                        print(f'{group[0][1].abbreviation} no longer a playoff team')
        elif len(group) > 2:
            print("Multiple team tiebreaker not implemented yet")
        westNumOfTeams -= len(group)
        firstGroupBool = False

    return seededTeamsEast, seededTeamsWest

# team names are corresponding abbreviations
def initializeTeams():
    # return copies of each team so each seasonSim starts with original team stats (wins/losses don't stack)
    eastTeamsList = {
        'Atlanta': copy.deepcopy(Teams[convertNameToAbb("Atlanta")]),
        'Boston': copy.deepcopy(Teams[convertNameToAbb("Boston")]),
        'Brooklyn': copy.deepcopy(Teams[convertNameToAbb("Brooklyn")]),
        'Charlotte': copy.deepcopy(Teams[convertNameToAbb("Charlotte")]),
        'Chicago': copy.deepcopy(Teams[convertNameToAbb("Chicago")]),
        'Cleveland': copy.deepcopy(Teams[convertNameToAbb("Cleveland")]),
        'Detroit': copy.deepcopy(Teams[convertNameToAbb("Detroit")]),
        'Indiana': copy.deepcopy(Teams[convertNameToAbb("Indiana")]),
        'Miami': copy.deepcopy(Teams[convertNameToAbb("Miami")]),
        'Milwaukee': copy.deepcopy(Teams[convertNameToAbb("Milwaukee")]),
        'New York': copy.deepcopy(Teams[convertNameToAbb("New York")]),
        'Orlando': copy.deepcopy(Teams[convertNameToAbb("Orlando")]),
        'Philadelphia': copy.deepcopy(Teams[convertNameToAbb("Philadelphia")]),
        'Toronto': copy.deepcopy(Teams[convertNameToAbb("Toronto")]),
        'Washington': copy.deepcopy(Teams[convertNameToAbb("Washington")])
    }
    westTeamsList = {
        'Dallas': copy.deepcopy(Teams[convertNameToAbb("Dallas")]),
        'Denver': copy.deepcopy(Teams[convertNameToAbb("Denver")]),
        'Golden St.': copy.deepcopy(Teams[convertNameToAbb("Golden St.")]),
        'Houston': copy.deepcopy(Teams[convertNameToAbb("Houston")]),
        'L.A. Clippers': copy.deepcopy(Teams[convertNameToAbb("L.A. Clippers")]),
        'L.A. Lakers': copy.deepcopy(Teams[convertNameToAbb("L.A. Lakers")]),
        'Memphis': copy.deepcopy(Teams[convertNameToAbb("Memphis")]),
        'Minnesota': copy.deepcopy(Teams[convertNameToAbb("Minnesota")]),
        'New Orleans': copy.deepcopy(Teams[convertNameToAbb("New Orleans")]),
        'Oklahoma City': copy.deepcopy(Teams[convertNameToAbb("Oklahoma City")]),
        'Phoenix': copy.deepcopy(Teams[convertNameToAbb("Phoenix")]),
        'Portland': copy.deepcopy(Teams[convertNameToAbb("Portland")]),
        'Sacramento': copy.deepcopy(Teams[convertNameToAbb("Sacramento")]),
        'San Antonio': copy.deepcopy(Teams[convertNameToAbb("San Antonio")]),
        'Utah': copy.deepcopy(Teams[convertNameToAbb("Utah")])
    }
    teamsList = {}
    for key, value in eastTeamsList.items():
        teamsList[key] = value
    for key, value in westTeamsList.items():
        teamsList[key] = value
    return teamsList, eastTeamsList, westTeamsList


def convertNameToAbb(name):
    if name == "Atlanta":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Boston":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Brooklyn":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Charlotte":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Chicago":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Cleveland":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Dallas":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Denver":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Detroit":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Golden St.":
        teamInfo = teams.find_teams_by_nickname("Warriors")
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Houston":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Indiana":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "L.A. Clippers":
        teamInfo = teams.find_teams_by_nickname("Clippers")
        teamAbb = teamInfo[0]['abbreviation']
    if name == "L.A. Lakers":
        teamInfo = teams.find_teams_by_nickname("Lakers")
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Memphis":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Miami":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Milwaukee":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Minnesota":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "New Orleans":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "New York":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Oklahoma City":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Orlando":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Philadelphia":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Phoenix":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Portland":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Sacramento":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "San Antonio":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Toronto":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Utah":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    if name == "Washington":
        teamInfo = teams.find_teams_by_city(name)
        teamAbb = teamInfo[0]['abbreviation']
    return teamAbb

# can this be integrated into convertNameToAbb
def convertAbbToName(abb):
    # could use switch instead or make else if, else for incorrect abb
    if abb == "ATL":
        name = "Atlanta"
    if abb == "BOS":
        name = "Boston"
    if abb == "BKN":
        name = "Brooklyn"
    if abb == "CHA":
        name = "Charlotte"
    if abb == "CHI":
        name = "Chicago"
    if abb == "CLE":
        name = "Cleveland"
    if abb == "DET":
        name = "Detroit"
    if abb == "IND":
        name = "Indiana"
    if abb == "MIA":
        name = "Miami"
    if abb == "MIL":
        name = "Milwaukee"
    if abb == "NYK":
        name = "New York"
    if abb == "ORL":
        name = "Orlando"
    if abb == "PHI":
        name = "Philadelphia"
    if abb == "TOR":
        name = "Toronto"
    if abb == "WAS":
        name = "Washington"
    if abb == "DAL":
        name = "Dallas"
    if abb == "DEN":
        name = "Denver"
    if abb == "GSW":
        name = "Golden St."
    if abb == "HOU":
        name = "Houston"
    if abb == "LAC":
        name = "L.A. Clippers"
    if abb == "LAL":
        name = "L.A. Lakers"
    if abb == "MEM":
        name = "Memphis"
    if abb == "MIN":
        name = "Minnesota"
    if abb == "NOP":
        name = "New Orleans"
    if abb == "OKC":
        name = "Oklahoma City"
    if abb == "PHX":
        name = "Phoenix"
    if abb == "POR":
        name = "Portland"
    if abb == "SAC":
        name = "Sacramento"
    if abb == "SAS":
        name = "San Antonio"
    if abb == "UTA":
        name = "Utah"
    return name


def breakTiebreaker(scores, *args, divisionWinner=False, eastPlayoffTeamsGroups=None, westPlayoffTeamsGroups=None):
    ''' Implement divisionWinner condition
            always return one value (winner) even if multiple passed
    '''
    '''if divisionWinner:
        print()'''
    # get playoff teams lists from playoffTeamsGroups
    eastPlayoffTeams = []
    for group in eastPlayoffTeamsGroups:
        for team in group:
            eastPlayoffTeams.append(team[1])
    westPlayoffTeams = []
    for group in westPlayoffTeamsGroups:
        for team in group:
            westPlayoffTeams.append(team[1])

    numOfTeams = len(args)
    if numOfTeams == 2:
        team1 = args[0]
        team2 = args[1]
        team1H2HWins = 0
        team2H2HWins = 0
        team1Abb = team1.abbreviation
        team2Abb = team2.abbreviation
        team1Div = team2.division
        team2Div = team2.division
        # head to head tiebreaker
        for score in scores:
            if score[0] == team1Abb and score[1] == team2Abb:
                team1H2HWins += 1
            elif score[0] == team2Abb and score[1] == team1Abb:
                team2H2HWins += 1
        if team1H2HWins > team2H2HWins:
            if bi.DEBUG_STATS:
                print(f"{team1Abb} wins tie by h2h {team1H2HWins} to {team2H2HWins}")
            return team1
        elif team2H2HWins > team1H2HWins:
            if bi.DEBUG_STATS:
                print(f"{team2Abb} wins tie by h2h {team2H2HWins} to {team1H2HWins}")
            return team2

        # division winner and w/l % tiebreaker
        # team1 division
        division = []
        for team in Teams.values():
            if team.division == team1Div:
                division.append(team)
        # div winner?
        team1DivWinner = True
        for team in division:
            if team.wins > team1.wins:  ### would this have to be seed and not wins???
                team1DivWinner = False  ### mark team as division winner or before hand (var in team class)???
        # div win/loss % (only if in same division)
        if team1.division == team2.division:
            team1DivWins = 0
            team1DivLosses = 0
            for score in scores:
                if score[0] == team1Abb and any(divTeam.abbreviation == score[1] for divTeam in division):
                    team1DivWins += 1
                if any(divTeam.abbreviation == score[0] for divTeam in division) and score[1] == team1Abb:
                    team1DivLosses += 1
        # team2 division
        division = []
        for team in Teams.values():
            if team.division == team2Div:
                division.append(team)
        # div winner?
        team2DivWinner = True
        for team in division:
            if team.wins > team2.wins:   ### would this have to be seed and not wins???
                team2DivWinner = False   ### mark team as division winner or not first???
        # div win/loss % (only if in same division)
        if team1.division == team2.division:
            team2DivWins = 0
            team2DivLosses = 0
            for score in scores:
                if score[0] == team2Abb and any(divTeam.abbreviation == score[1] for divTeam in division):
                    team2DivWins += 1
                if any(divTeam.abbreviation == score[0] for divTeam in division) and score[1] == team2Abb:
                    team2DivLosses += 1
        # div winner tiebreaker
        if team1DivWinner and not team2DivWinner:
            if bi.DEBUG_STATS:
                print(f"{team1Abb} wins tie by div winner")
            return team1
        elif team2DivWinner and not team1DivWinner:
            if bi.DEBUG_STATS:
                print(f"{team2Abb} wins tie by div winner")
            return team2
        # div w/l % tiebreaker (only if in same division)
        if team1.division == team2.division:
            team1DivWLPerc = team1DivWins / (team1DivWins + team1DivLosses)
            team2DivWLPerc = team2DivWins / (team2DivWins + team2DivLosses)
            if team1DivWLPerc > team2DivWLPerc:
                if bi.DEBUG_STATS:
                    print(f"{team1Abb} wins tie by div w/l % {team1DivWLPerc}({team1DivWins}) to {team2DivWLPerc}({team2DivWins})")
                return team1
            elif team2DivWLPerc > team1DivWLPerc:
                if bi.DEBUG_STATS:
                    print(f"{team2Abb} wins tie by div w/l % {team2DivWLPerc}({team2DivWins}) to {team1DivWLPerc}({team1DivWins})")
                return team2

        # conference win/loss % tiebreaker
        conference = [team1]
        for team in Teams.values():
            if team.conference == team1.conference:
                conference.append(team)
        # team1
        team1ConfWins = 0
        team1ConfLosses = 0
        for score in scores:
            if score[0] == team1Abb and any(confTeam.abbreviation == score[1] for confTeam in conference):
                team1ConfWins += 1
            if any(confTeam.abbreviation == score[0] for confTeam in conference) and score[1] == team1Abb:
                team1ConfLosses += 1
        # team2
        team2ConfWins = 0
        team2ConfLosses = 0
        for score in scores:
            if score[0] == team2Abb and any(confTeam.abbreviation == score[1] for confTeam in conference):
                team2ConfWins += 1
            if any(confTeam.abbreviation == score[0] for confTeam in conference) and score[1] == team2Abb:
                team2ConfLosses += 1
        # check
        team1ConfWLPerc = team1ConfWins / (team1ConfWins + team1ConfLosses)
        team2ConfWLPerc = team2ConfWins / (team2ConfWins + team2ConfLosses)
        if team1ConfWLPerc > team2ConfWLPerc:
            if bi.DEBUG_STATS:
                print(f"{team1Abb} wins tie by conf w/l % {team1ConfWLPerc}({team1ConfWins}) to {team2ConfWLPerc}({team2ConfWins})")
            return team1
        elif team2ConfWLPerc > team1ConfWLPerc:
            if bi.DEBUG_STATS:
                print(f"{team2Abb} wins tie by conf w/l % {team2ConfWLPerc}({team2ConfWins}) to {team1ConfWLPerc}({team1ConfWins})")
            return team2

        # conference playoff teams win/loss % tiebreaker
        # team1
        if team1.conference == 'East':
            playoffTeams = eastPlayoffTeams
        else:
            playoffTeams = westPlayoffTeams
        team1ConfPlayoffWins = 0
        team1ConfPlayoffLosses = 0
        for score in scores:
            if score[0] == team1Abb and any(confPlayoffTeam.abbreviation == score[1] for confPlayoffTeam in playoffTeams):
                team1ConfPlayoffWins += 1
            if any(confPlayoffTeam.abbreviation == score[0] for confPlayoffTeam in playoffTeams) and score[1] == team1Abb:
                team1ConfPlayoffLosses += 1
        # team2
        team2ConfPlayoffWins = 0
        team2ConfPlayoffLosses = 0
        for score in scores:
            if score[0] == team2Abb and any(confPlayoffTeam.abbreviation == score[1] for confPlayoffTeam in playoffTeams):
                team2ConfPlayoffWins += 1
            if any(confPlayoffTeam.abbreviation == score[0] for confPlayoffTeam in playoffTeams) and score[1] == team2Abb:
                team2ConfPlayoffLosses += 1
        # check
        team1ConfPlayoffWLPerc = team1ConfPlayoffWins / (team1ConfPlayoffWins + team1ConfPlayoffLosses)
        team2ConfPlayoffWLPerc = team2ConfPlayoffWins / (team2ConfPlayoffWins + team2ConfPlayoffLosses)
        if team1ConfPlayoffWLPerc > team2ConfPlayoffWLPerc:
            if bi.DEBUG_STATS:
                print(
                    f"{team1Abb} wins tie by conf playoff w/l % {team1ConfPlayoffWLPerc}({team1ConfPlayoffWins}) to {team2ConfPlayoffWLPerc}({team2ConfPlayoffWins})")
            return team1
        elif team2ConfPlayoffWLPerc > team1ConfPlayoffWLPerc:
            if bi.DEBUG_STATS:
                print(
                    f"{team2Abb} wins tie by conf playoff w/l % {team2ConfPlayoffWLPerc}({team2ConfPlayoffWins}) to {team1ConfPlayoffWLPerc}({team1ConfPlayoffWins})")
            return team2

        # opp conference playoff teams win/loss % tiebreaker
        # team1
        if team1.conference == 'East':
            playoffTeams = westPlayoffTeams
        else:
            playoffTeams = eastPlayoffTeams
        team1OppConfPlayoffWins = 0
        team1OppConfPlayoffLosses = 0
        for score in scores:
            if score[0] == team1Abb and any(oppConfPlayoffTeam.abbreviation == score[1] for oppConfPlayoffTeam in playoffTeams):
                team1OppConfPlayoffWins += 1
            if any(oppConfPlayoffTeam.abbreviation == score[0] for oppConfPlayoffTeam in playoffTeams) and score[1] == team1Abb:
                team1OppConfPlayoffLosses += 1
        # team2
        team2OppConfPlayoffWins = 0
        team2OppConfPlayoffLosses = 0
        for score in scores:
            if score[0] == team2Abb and any(oppConfPlayoffTeam.abbreviation == score[1] for oppConfPlayoffTeam in playoffTeams):
                team2OppConfPlayoffWins += 1
            if any(oppConfPlayoffTeam.abbreviation == score[0] for oppConfPlayoffTeam in playoffTeams) and score[1] == team2Abb:
                team2OppConfPlayoffLosses += 1
        # check
        team1OppConfPlayoffWLPerc = team1OppConfPlayoffWins / (team1OppConfPlayoffWins + team1OppConfPlayoffLosses)
        team2OppConfPlayoffWLPerc = team2OppConfPlayoffWins / (team2OppConfPlayoffWins + team2OppConfPlayoffLosses)
        if team1OppConfPlayoffWLPerc > team2OppConfPlayoffWLPerc:
            if bi.DEBUG_STATS:
                print(
                    f"{team1Abb} wins tie by opp conf playoff w/l % {team1OppConfPlayoffWLPerc}({team1OppConfPlayoffWins}) to {team2OppConfPlayoffWLPerc}({team2OppConfPlayoffWins})")
            return team1
        elif team2OppConfPlayoffWLPerc > team1OppConfPlayoffWLPerc:
            if bi.DEBUG_STATS:
                print(
                    f"{team2Abb} wins tie by opp conf playoff w/l % {team2OppConfPlayoffWLPerc}({team2OppConfPlayoffWins}) to {team1OppConfPlayoffWLPerc}({team1OppConfPlayoffWins})")
            return team2

        # total points
        if team1.points > team2.points:
            print(f"{team1Abb} wins tie by total points {team1.points} to {team2.points}")
            return team1
        elif team2.points > team1.points:
            print(f"{team2Abb} wins tie by total points {team2.points} to {team1.points}")
            return team2
        else:
            print("Tie could not be broken. Randomly chosen")
            team = random.randint(1, 2)
            if team == 1:
                print(f'{team1Abb} randomly chosen')
                return team1
            else:
                print(f'{team2Abb} randomly chosen')
                return team2
    else:
        print("Multiple team tiebreaker not implemented yet. Team1 returned")
        return args[0]

#breakTiebreaker()

from pyFiles.nbaSim import Teams