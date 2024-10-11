from nba_api.stats.static import teams
import random
from numpy.random import choice
from datetime import date
import requests
from bs4 import BeautifulSoup
from scrape import readScheduleFile

LEAGUEID = "00"
SEASONTYPE = "Regular Season"
SEASON = "2023-24"
SEASONENDDATE = 20240414
SEASONSTART = True
SEASONSTARTDATE = 20231024
ALLSTARDATE = 20230218
DEBUG_STATS = True

games = 0
possessions = 0
shots = 0
TOs = 0
PFs = 0
made2s = 0
attempted2s = 0
made3s = 0
attempted3s = 0
commonPFs = 0
shootingPFs = 0
madeFTs = 0
attemptedFTs = 0
score_1 = 0
score_2 = 0
simScore_1 = 0
simScore_2 = 0


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
    # print(team1ShootingFoulPerc, team2ShootingFoulPerc) ###
    return team1ShootingFoulPerc, team2ShootingFoulPerc


def singleGameSim(team1Abb, team2Abb, team1=None, team2=None):
    global games, possessions, shots, TOs, PFs, made2s, attempted2s, made3s, attempted3s, commonPFs, shootingPFs,\
        madeFTs, attemptedFTs, score_1, score_2, simScore_1, simScore_2
    if team1Abb == 'Select' or team2Abb == 'Select':
        return 'Please select two teams'
    if team1 == None:
        team1 = Teams[team1Abb]
    if team2 == None:
        team2 = Teams[team2Abb]
    team1TwoPerc, team2TwoPerc = getTwoPerc(team1, team2)
    team1ThreePerc, team2ThreePerc = getThreePerc(team1, team2)
    team1OREBPerc, team2OREBPerc = getOREBPerc(team1, team2)
    team1DREBPerc, team2DREBPerc = getDREBPerc(team1, team2)
    team1TurnoverPerc, team2TurnoverPerc = getTurnoverPerc(team1, team2)
    team1PFPerc, team2PFPerc = getPFPerc(team1, team2)
    team1ShootingFoulPerc, team2ShootingFoulPerc = getShootingFoulPerc(team1, team2)
    team1ShotFrequency = 1 - (team1TurnoverPerc + team2PFPerc)
    team2ShotFrequency = 1 - (team2TurnoverPerc + team1PFPerc)
    timePerPossession = 14.4

    quarter = 1
    team1Score = 0
    team2Score = 0
    possession = random.randint(1, 2)

    shot1 = 0
    to1 = 0
    foul1 = 0
    common1 = 0
    shooting1 = 0
    make2_1 = 0
    miss2_1 = 0
    make3_1 = 0
    miss3_1 = 0
    ftMake1 = 0
    ftMiss1 = 0
    shot2 = 0
    to2 = 0
    foul2 = 0
    common2 = 0
    shooting2 = 0
    make2_2 = 0
    miss2_2 = 0
    make3_2 = 0
    miss3_2 = 0
    ftMake2 = 0
    ftMiss2 = 0
    poss = 0
    team1TotalFouls = 0
    team2TotalFouls = 0

    #print('\n')
    #print(team1ShotFrequency, team1TurnoverPerc, team2PFPerc)
    #print(team2ShotFrequency, team2TurnoverPerc, team1PFPerc)

    while quarter <= 4 or (quarter >= 5 and team1Score == team2Score):
        team1Fouls = 0
        team1Last2MinFouls = 0
        team2Fouls = 0
        team2Last2MinFouls = 0
        if quarter <= 4:
            time = 720
            bonus = 5
        elif quarter >= 5 and team1Score == team2Score:
            time = 300
            bonus = 4
        while time > 0:
            if possession == 1:
                poss += 1
                #print("BOS Ball")
                outcome = choice(["Shot", "Turnover", "Foul"], 1,
                                 p=[team1ShotFrequency, team1TurnoverPerc, team2PFPerc])
                if outcome == "Shot":
                    shot1 += 1  ###
                    shotType = choice(["Two", "Three"], 1, p=[team1.twoFrequency, team1.threeFrequency])
                    if shotType == "Two":
                        shot = choice(["Make", "Miss"], 1, p=[team1TwoPerc, (1 - team1TwoPerc)])
                        if shot == "Make":
                            #print("Made 2")  ###
                            make2_1 += 1  ###
                            team1Score += 2
                            possession = 2
                        elif shot == "Miss":
                            #("Missed 2")  ###
                            miss2_1 += 1  ###
                            possession = choice([1, 2], 1, p=[team1OREBPerc, team2DREBPerc])
                            if possession == 1:
                                #print("OREB")
                                poss -= 1
                                time += timePerPossession
                    if shotType == "Three":
                        shot = choice(["Make", "Miss"], 1, p=[team1ThreePerc, (1 - team1ThreePerc)])
                        if shot == "Make":
                            #print("Made 3")  ###
                            make3_1 += 1  ###
                            team1Score += 3
                            possession = 2
                        elif shot == "Miss":
                            #print("Missed 3")  ###
                            miss3_1 += 1  ###
                            possession = choice([1, 2], 1, p=[team1OREBPerc, team2DREBPerc])
                            if possession == 1:
                                #print("OREB")
                                poss -= 1
                                time += timePerPossession
                elif outcome == "Turnover":
                    #print("Turnover")  ###
                    to1 += 1  ###
                    possession = 2
                elif outcome == "Foul":
                    foul1 += 1  ###
                    team2Fouls += 1
                    if time <= 120:
                        team2Last2MinFouls += 1
                    foulType = choice(["Common", "Shooting"], 1, p=[(1 - team2ShootingFoulPerc), team2ShootingFoulPerc])
                    if foulType == "Shooting":
                        shot1 += 1  ###
                        foulType = choice(["Shooting", "And1_2", "And1_3"], 1,
                                          p=[(1 - team1.twoPointAnd1Chance - team1.threePointAnd1Chance),
                                             team1.twoPointAnd1Chance, team1.threePointAnd1Chance])
                    if foulType == "Common" and (team2Fouls < bonus and team2Last2MinFouls < 2):
                        #print("Common Foul")  ###
                        common1 += 1  ###
                        possession = 1
                    elif foulType == "Common" and (team2Fouls >= bonus or team2Last2MinFouls >= 2):
                        #print("Common Foul")  ###
                        common1 += 1  ###
                        foulType = "Shooting"
                        shooting1 -= 1
                    elif foulType == "And1_2":
                        #print("And1 2")  ###
                        make2_1 += 1
                        team1Score += 2
                        freeThrow = choice(["Make", "Miss"], 1,
                                           p=[team1.teamFreeThrowPerc, (1 - team1.teamFreeThrowPerc)])
                        if freeThrow == "Make":
                            #print("Made FT")  ###
                            ftMake1 += 1  ###
                            team1Score += 1
                            possession = 2
                        elif freeThrow == "Miss":
                            #print("Missed FT")  ###
                            ftMiss1 += 1  ###
                            possession = choice([1, 2], 1, p=[team1OREBPerc, team2DREBPerc])
                            if possession == 1:
                                #print("OREB")
                                poss -= 1
                                time += timePerPossession
                    elif foulType == "And1_3":
                        #print("And1 3")  ###
                        make3_1 += 1
                        team1Score += 3
                        freeThrow = choice(["Make", "Miss"], 1,
                                           p=[team1.teamFreeThrowPerc, (1 - team1.teamFreeThrowPerc)])
                        if freeThrow == "Make":
                            #print("Made FT")  ###
                            ftMake1 += 1  ###
                            team1Score += 1
                            possession = 2
                        elif freeThrow == "Miss":
                            #print("Missed FT")  ###
                            ftMiss1 += 1  ###
                            possession = choice([1, 2], 1, p=[team1OREBPerc, team2DREBPerc])
                            if possession == 1:
                                #print("OREB")
                                poss -= 1
                                time += timePerPossession
                    if foulType == "Shooting":
                        shooting1 += 1  ###
                        #print("Shooting Foul")  ###
                        freeThrow1 = choice(["Make", "Miss"], 1,
                                            p=[team1.teamFreeThrowPerc, (1 - team1.teamFreeThrowPerc)])
                        if freeThrow1 == "Make":
                            #print("Made FT")  ###
                            ftMake1 += 1  ###
                            team1Score += 1
                        elif freeThrow1 == "Miss":
                            #print("Missed FT")  ###
                            ftMiss1 += 1  ###
                        freeThrow2 = choice(["Make", "Miss"], 1,
                                            p=[team1.teamFreeThrowPerc, (1 - team1.teamFreeThrowPerc)])
                        if freeThrow2 == "Make":
                            #print("Made FT")  ###
                            ftMake1 += 1  ###
                            team1Score += 1
                            possession = 2
                        elif freeThrow2 == "Miss":
                            #print("Missed FT")  ###
                            ftMiss1 += 1  ###
                            possession = choice([1, 2], 1, p=[team1OREBPerc, team2DREBPerc])
                            if possession == 1:
                                #print("OREB")
                                poss -= 1
                                time += timePerPossession
                time -= timePerPossession
            if possession == 2:
                poss += 1
                #print("BKN Ball")
                outcome = choice(["Shot", "Turnover", "Foul"], 1,
                                 p=[team2ShotFrequency, team2TurnoverPerc, team1PFPerc])
                if outcome == "Shot":
                    shot2 += 1  ###
                    shotType = choice(["Two", "Three"], 1, p=[team2.twoFrequency, team2.threeFrequency])
                    if shotType == "Two":
                        shot = choice(["Make", "Miss"], 1, p=[team2TwoPerc, (1 - team2TwoPerc)])
                        if shot == "Make":
                            #print("Made 2")  ###
                            make2_2 += 1  ###
                            team2Score += 2
                            possession = 1
                        elif shot == "Miss":
                            #print("Missed 2")  ###
                            miss2_2 += 1  ###
                            possession = choice([2, 1], 1, p=[team2OREBPerc, team1DREBPerc])
                            if possession == 2:
                                # print("OREB")
                                poss -= 1
                                time += timePerPossession
                    if shotType == "Three":
                        shot = choice(["Make", "Miss"], 1, p=[team2ThreePerc, (1 - team2ThreePerc)])
                        if shot == "Make":
                            #print("Made 3")  ###
                            make3_2 += 1  ###
                            team2Score += 3
                            possession = 1
                        elif shot == "Miss":
                            #print("Missed 3")  ###
                            miss3_2 += 1  ###
                            possession = choice([2, 1], 1, p=[team2OREBPerc, team1DREBPerc])
                            if possession == 2:
                                # print("OREB")
                                poss -= 1
                                time += timePerPossession
                elif outcome == "Turnover":
                    #print("Turnover")  ###
                    to2 += 1  ###
                    possession = 1
                elif outcome == "Foul":
                    foul2 += 1  ###
                    team1Fouls += 1
                    if time <= 120:
                        team1Last2MinFouls += 1
                    foulType = choice(["Common", "Shooting"], 1, p=[(1 - team1ShootingFoulPerc), team1ShootingFoulPerc])
                    if foulType == "Shooting":
                        shot2 += 1  ###
                        foulType = choice(["Shooting", "And1_2", "And1_3"], 1,
                                          p=[(1 - team2.twoPointAnd1Chance - team2.threePointAnd1Chance),
                                             team2.twoPointAnd1Chance, team2.threePointAnd1Chance])
                    if foulType == "Common" and (team1Fouls < bonus and team1Last2MinFouls < 2):
                        #print("Common Foul")  ###
                        common2 += 1  ###
                        possession = 2
                    elif foulType == "Common" and (team1Fouls >= bonus or team1Last2MinFouls >= 2):
                        #print("Common Foul")  ###
                        common2 += 1  ###
                        foulType = "Shooting"
                        shooting2 -= 1
                    elif foulType == "And1_2":
                        #print("And1 2")  ###
                        team2Score += 2
                        freeThrow = choice(["Make", "Miss"], 1,
                                           p=[team2.teamFreeThrowPerc, (1 - team2.teamFreeThrowPerc)])
                        if freeThrow == "Make":
                            #print("Made FT")  ###
                            ftMake2 += 1  ###
                            team2Score += 1
                            possession = 1
                        elif freeThrow == "Miss":
                            #print("Missed FT")  ###
                            ftMiss2 += 1  ###
                            possession = choice([2, 1], 1, p=[team2OREBPerc, team1DREBPerc])
                            if possession == 2:
                                #print("OREB")
                                poss -= 1
                                time += timePerPossession
                    elif foulType == "And1_3":
                        #print("And1 3")  ###
                        team2Score += 3
                        freeThrow = choice(["Make", "Miss"], 1,
                                           p=[team2.teamFreeThrowPerc, (1 - team2.teamFreeThrowPerc)])
                        if freeThrow == "Make":
                            #print("Made FT")  ###
                            ftMake2 += 1  ###
                            team2Score += 1
                            possession = 1
                        elif freeThrow == "Miss":
                            #print("Missed FT")  ###
                            ftMiss2 += 1  ###
                            possession = choice([2, 1], 1, p=[team2OREBPerc, team1DREBPerc])
                            if possession == 2:
                                #print("OREB")
                                poss -= 1
                                time += timePerPossession
                    if foulType == "Shooting":
                        #print("Shooting Foul")
                        shooting2 += 1  ###
                        freeThrow1 = choice(["Make", "Miss"], 1,
                                            p=[team2.teamFreeThrowPerc, (1 - team2.teamFreeThrowPerc)])
                        if freeThrow1 == "Make":
                            ftMake2 += 1  ###
                            #print("Made FT")  ###
                            team2Score += 1
                        elif freeThrow1 == "Miss":
                            #print("Missed FT")  ###
                            ftMiss2 += 1  ###
                        freeThrow2 = choice(["Make", "Miss"], 1,
                                            p=[team2.teamFreeThrowPerc, (1 - team2.teamFreeThrowPerc)])
                        if freeThrow2 == "Make":
                            #print("Made FT")  ###
                            ftMake2 += 1  ###
                            team2Score += 1
                            possession = 1
                        elif freeThrow2 == "Miss":
                            #print("Missed FT")  ###
                            ftMiss2 += 1  ###
                            possession = choice([2, 1], 1, p=[team2OREBPerc, team1DREBPerc])
                            if possession == 2:
                                #print("OREB")
                                poss -= 1
                                time += timePerPossession
                time -= timePerPossession
        quarter += 1
        team1TotalFouls += team1Fouls ###
        team2TotalFouls += team2Fouls ###
    '''print(f'Possessions: {poss}')
    print(f'Teams 1 shots, TOs, PFs: {shot1, to1, team1Fouls}')
    print('Team 1 Made 2s, Missed 2s, Made 3s, Missed 3s, Common PFs, Shooting PFs, FTs Made, FTs Missed:')
    print(f'\t{make2_1, miss2_1, make3_1, miss3_1, common1, shooting1, ftMake1, ftMiss1}')
    print(f'Teams 2 shots, TOs, PFs: {shot2, to2, team2Fouls}')
    print('Team 1 Made 2s, Missed 2s, Made 3s, Missed 3s, Common PFs, Shooting PFs, FTs Made, FTs Missed:')
    print(f'\t{make2_2, miss2_2, make3_2, miss3_2, common2, shooting2, ftMake2, ftMiss2}')'''
    if DEBUG_STATS:
        games += 1
        possessions += poss
        shots += shot1 + shot2
        TOs += to1 + to2
        PFs += team1TotalFouls + team2TotalFouls
        made2s += make2_1 + make2_2
        attempted2s += make2_1 + make2_2 + miss2_1 + miss2_2
        made3s += make3_1 + make3_2
        attempted3s += make3_1 + make3_2 + miss3_1 + miss3_2
        commonPFs += common1 + common2
        shootingPFs += shooting1 + shooting2
        madeFTs += ftMake1 + ftMake2
        attemptedFTs += ftMake1 + ftMake2 + ftMiss1 + ftMiss2
        simScore_1 += team1Score
        simScore_2 += team2Score
        if team1Score > team2Score:
            score_1 += team1Score
            score_2 += team2Score
        else:
            score_1 += team2Score
            score_2 += team1Score
    if team1Score > team2Score:
        print(team1Abb + " beat " + team2Abb + " by a score of " + str(team1Score) + " to " + str(team2Score))
        return team1Abb, team1Score, team2Score
    else:
        print(team2Abb + " beat " + team1Abb + " by a score of " + str(team2Score) + " to " + str(team1Score))
        return team2Abb, team1Score, team2Score


# singleGameSim("BOS", "BKN")

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
        winner, team1Score, team2Score = singleGameSim(team1Abb, team2Abb, team1, team2)
        if team1Score > team2Score:
            team1Wins += 1
        elif team2Score > team1Score:
            team2Wins += 1
    if team1Wins == 4:
        #print(team1Abb + " wins the series 4 games to " + str(team2Wins))
        report = team1Abb + " wins the series vs " + team2Abb + " 4 games to " + str(team2Wins) + '\n'
        return team1Abb, team1Wins, team2Wins, report
    elif team2Wins == 4:
        #print(team2Abb + " wins the series 4 games to " + str(team1Wins))
        report = team2Abb + " wins the series vs " + team1Abb + " 4 games to " + str(team1Wins) + '\n'
        return team2Abb, team1Wins, team2Wins, report


# seriesSim("BOS", "BKN")

def seasonSim():
    seasonReport = ""
    teamsList, eastTeamsList, westTeamsList = initializeTeams()
    if SEASONSTART:
        for key, value in teamsList.items():
            teamsList[key].wins = 0
            teamsList[key].losses = 0
    schedule = readScheduleFile()
    for key, value in schedule.items():
        if key < SEASONSTARTDATE:
            continue
        else:
            teamNames = value
            numOfGames = (len(teamNames) / 2)
            gamesPlayed = 0
            while gamesPlayed < numOfGames:
                team1Name = teamNames[gamesPlayed * 2]
                team2Name = teamNames[(gamesPlayed * 2) + 1]
                team1Abb = convertNameToAbb(team1Name)
                team2Abb = convertNameToAbb(team2Name)
                winner, team1Score, team2Score = singleGameSim(team1Abb, team2Abb, teamsList[team1Name],
                                                               teamsList[team2Name])
                if winner == team1Abb:
                    teamsList[team1Name].wins += 1
                    teamsList[team2Name].losses += 1
                if winner == team2Abb:
                    teamsList[team2Name].wins += 1
                    teamsList[team1Name].losses += 1
                gamesPlayed += 1
    seasonReport += "Season Standings:\n"
    for team in eastTeamsList.values():
        #print(team.abbreviation, team.wins, team.losses)
        seasonReport += team.abbreviation + ": " + str(team.wins) + "-" + str(team.losses) + "\n"
    for team in westTeamsList.values():
        #print(team.abbreviation, team.wins, team.losses)
        seasonReport += team.abbreviation + ": " + str(team.wins) + "-" + str(team.losses) + "\n"
    eastTeamsList, westTeamsList = seedTeams(eastTeamsList, westTeamsList)

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
    winner, team1Score, team2Score = singleGameSim(east7, east8, teamsList[convertAbbToName(east7)],
                                                   teamsList[convertAbbToName(east8)])
    if winner == east8:
        temp = east7
        east7 = east8
        east8 = temp
    seasonReport += east7 + " beat " + east8 + " to get the 7 seed\n"
    # 9 vs 10
    winner, team1Score, team2Score = singleGameSim(east9, east10, teamsList[convertAbbToName(east9)],
                                                   teamsList[convertAbbToName(east10)])
    if winner == east10:
        temp = east9
        east9 = east10
        east10 = temp
    seasonReport += east9 + " beat " + east10 + " to stay in the play in\n"
    # 8 vs 9
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
    winner, team1Score, team2Score = singleGameSim(west7, west8, teamsList[convertAbbToName(west7)],
                                                   teamsList[convertAbbToName(west8)])
    if winner == west8:
        temp = west7
        west7 = west8
        west8 = temp
    seasonReport += west7 + " beat " + west8 + " to get the 7 seed\n"
    # 9 vs 10
    winner, team1Score, team2Score = singleGameSim(west9, west10, teamsList[convertAbbToName(west9)],
                                                   teamsList[convertAbbToName(west10)])
    if winner == west10:
        temp = west9
        west9 = west10
        west10 = temp
    seasonReport += west9 + " beat " + west10 + " to stay in the play in\n"
    # 8 vs 9
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
    seasonReport += report
    winnerEast2_7, team1Wins, team2Wins, report = seriesSim(east2, east7, teamsList[convertAbbToName(east2)],
                                                            teamsList[convertAbbToName(east7)])
    seasonReport += report
    winnerEast3_6, team1Wins, team2Wins, report = seriesSim(east3, east6, teamsList[convertAbbToName(east3)],
                                                            teamsList[convertAbbToName(east6)])
    seasonReport += report
    winnerEast4_5, team1Wins, team2Wins, report = seriesSim(east4, east5, teamsList[convertAbbToName(east4)],
                                                            teamsList[convertAbbToName(east5)])
    seasonReport += report
    # WEST 1ST RND
    seasonReport += "\nWest Round 1:\n"
    winnerWest1_8, team1Wins, team2Wins, report = seriesSim(west1, west8, teamsList[convertAbbToName(west1)],
                                                            teamsList[convertAbbToName(west8)])
    seasonReport += report
    winnerWest2_7, team1Wins, team2Wins, report = seriesSim(west2, west7, teamsList[convertAbbToName(west2)],
                                                            teamsList[convertAbbToName(west7)])
    seasonReport += report
    winnerWest3_6, team1Wins, team2Wins, report = seriesSim(west3, west6, teamsList[convertAbbToName(west3)],
                                                            teamsList[convertAbbToName(west6)])
    seasonReport += report
    winnerWest4_5, team1Wins, team2Wins, report = seriesSim(west4, west5, teamsList[convertAbbToName(west4)],
                                                            teamsList[convertAbbToName(west5)])
    seasonReport += report
    # EAST 2ND RND
    seasonReport += "\nEast Semifinals:\n"
    winnerEastSemis1, team1Wins, team2Wins, report = seriesSim(winnerEast1_8, winnerEast4_5,
                                                               teamsList[convertAbbToName(winnerEast1_8)],
                                                               teamsList[convertAbbToName(winnerEast4_5)])
    seasonReport += report
    winnerEastSemis2, team1Wins, team2Wins, report = seriesSim(winnerEast2_7, winnerEast3_6,
                                                               teamsList[convertAbbToName(winnerEast2_7)],
                                                               teamsList[convertAbbToName(winnerEast3_6)])
    seasonReport += report
    # WEST 2ND RND
    seasonReport += "\nWest Semifinals:\n"
    winnerWestSemis1, team1Wins, team2Wins, report = seriesSim(winnerWest1_8, winnerWest4_5,
                                                               teamsList[convertAbbToName(winnerWest1_8)],
                                                               teamsList[convertAbbToName(winnerWest4_5)])
    seasonReport += report
    winnerWestSemis2, team1Wins, team2Wins, report = seriesSim(winnerWest2_7, winnerWest3_6,
                                                               teamsList[convertAbbToName(winnerWest2_7)],
                                                               teamsList[convertAbbToName(winnerWest3_6)])
    seasonReport += report
    # EAST FINALS
    seasonReport += "\nEast Finals:\n"
    winnerEastFinals, team1Wins, team2Wins, report = seriesSim(winnerEastSemis1, winnerEastSemis2,
                                                               teamsList[convertAbbToName(winnerEastSemis1)],
                                                               teamsList[convertAbbToName(winnerEastSemis2)])
    seasonReport += report
    # WEST FINALS
    seasonReport += "\nWest Finals:\n"
    winnerWestFinals, team1Wins, team2Wins, report = seriesSim(winnerWestSemis1, winnerWestSemis2,
                                                               teamsList[convertAbbToName(winnerWestSemis1)],
                                                               teamsList[convertAbbToName(winnerWestSemis2)])
    seasonReport += report
    # FINALS
    seasonReport += "\nNBA Finals:\n"
    winnerFinals, team1WinsFinals, team2WinsFinals, report = seriesSim(winnerEastFinals, winnerWestFinals,
                                                                       teamsList[convertAbbToName(winnerEastFinals)],
                                                                       teamsList[convertAbbToName(winnerWestFinals)])
    seasonReport += report
    seasonReport += winnerFinals + " wins the finals!\n"

    if DEBUG_STATS:
        global games, possessions, shots, TOs, PFs, made2s, attempted2s, made3s, attempted3s, commonPFs, shootingPFs, \
            madeFTs, attemptedFTs, score_1, score_2, simScore_1, simScore_2
        print(f'Num of games: {games}')
        print(f'Poss/G, Shots/G, TOs/G: {possessions/games, shots/games, TOs/games}\n'
              f'PFs/G, Common PFs/G, Shooting PFs/G, FTs/Game: {PFs/games, commonPFs/games, shootingPFs/games, attemptedFTs/games}\n'
              f'2%, 3%, FT%: {made2s/attempted2s, made3s/attempted3s, madeFTs/attemptedFTs}\n'
              f'Score 1, Score 2, SimScore 1, SimScore2: {score_1/games, score_2/games, simScore_1/games, simScore_2/games}')
    return seasonReport


def seedTeams(eastTeamsList, westTeamsList):
    seededTeamsEast = sorted(eastTeamsList.items(), key=lambda x: x[1].wins, reverse=True)
    seededTeamsWest = sorted(westTeamsList.items(), key=lambda x: x[1].wins, reverse=True)
    return seededTeamsEast, seededTeamsWest


def initializeTeams():
    eastTeamsList = {
        'Atlanta': Teams[convertNameToAbb("Atlanta")],
        'Boston': Teams[convertNameToAbb("Boston")],
        'Brooklyn': Teams[convertNameToAbb("Brooklyn")],
        'Charlotte': Teams[convertNameToAbb("Charlotte")],
        'Chicago': Teams[convertNameToAbb("Chicago")],
        'Cleveland': Teams[convertNameToAbb("Cleveland")],
        'Detroit': Teams[convertNameToAbb("Detroit")],
        'Indiana': Teams[convertNameToAbb("Indiana")],
        'Miami': Teams[convertNameToAbb("Miami")],
        'Milwaukee': Teams[convertNameToAbb("Milwaukee")],
        'New York': Teams[convertNameToAbb("New York")],
        'Orlando': Teams[convertNameToAbb("Orlando")],
        'Philadelphia': Teams[convertNameToAbb("Philadelphia")],
        'Toronto': Teams[convertNameToAbb("Toronto")],
        'Washington': Teams[convertNameToAbb("Washington")]
    }
    westTeamsList = {
        'Dallas': Teams[convertNameToAbb("Dallas")],
        'Denver': Teams[convertNameToAbb("Denver")],
        'Golden St.': Teams[convertNameToAbb("Golden St.")],
        'Houston': Teams[convertNameToAbb("Houston")],
        'L.A. Clippers': Teams[convertNameToAbb("L.A. Clippers")],
        'L.A. Lakers': Teams[convertNameToAbb("L.A. Lakers")],
        'Memphis': Teams[convertNameToAbb("Memphis")],
        'Minnesota': Teams[convertNameToAbb("Minnesota")],
        'New Orleans': Teams[convertNameToAbb("New Orleans")],
        'Oklahoma City': Teams[convertNameToAbb("Oklahoma City")],
        'Phoenix': Teams[convertNameToAbb("Phoenix")],
        'Portland': Teams[convertNameToAbb("Portland")],
        'Sacramento': Teams[convertNameToAbb("Sacramento")],
        'San Antonio': Teams[convertNameToAbb("San Antonio")],
        'Utah': Teams[convertNameToAbb("Utah")]
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


def convertAbbToName(abb):
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
from nbaSim import Teams