from nba_api.stats.static import teams
import random
from numpy.random import choice
from datetime import date
from pyFiles.scrape import readScheduleFile
from pyFiles import basicInfo as bi

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

def simPoss(off, offStats, defStats, defFouls, defLast2MinFouls, bonus, time):
    points = 0
    possession = 0
    addTime = False

    outcome = choice(["Shot", "Turnover", "Foul"], 1,
                     p=[offStats['ShotFreq'], offStats['TO%'], defStats['PF%']])
    if outcome == "Shot":
        shotType = choice(["Two", "Three"], 1, p=[off.twoFrequency, off.threeFrequency])
        if shotType == "Two":
            shot = choice(["Make", "Miss"], 1, p=[offStats['2%'], (1 - offStats['2%'])])
            if shot == "Make":
                points += 2
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
                points += 3
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
            points += 2
            freeThrow = choice(["Make", "Miss"], 1,
                               p=[off.teamFreeThrowPerc, (1 - off.teamFreeThrowPerc)])
            if freeThrow == "Make":
                points += 1
                possession = 2
            elif freeThrow == "Miss":
                possession = choice([1, 2], 1, p=[offStats['OREB%'], defStats['DREB%']])
                if possession == 1:
                    addTime = True
        elif foulType == "And1_3":
            points += 3
            freeThrow = choice(["Make", "Miss"], 1,
                               p=[off.teamFreeThrowPerc, (1 - off.teamFreeThrowPerc)])
            if freeThrow == "Make":
                points += 1
                possession = 2
            elif freeThrow == "Miss":
                possession = choice([1, 2], 1, p=[offStats['OREB%'], defStats['DREB%']])
                if possession == 1:
                    addTime = True
        if foulType == "Shooting":
            freeThrow1 = choice(["Make", "Miss"], 1,
                                p=[off.teamFreeThrowPerc, (1 - off.teamFreeThrowPerc)])
            if freeThrow1 == "Make":
                points += 1
            elif freeThrow1 == "Miss":
                points += 0
            freeThrow2 = choice(["Make", "Miss"], 1,
                                p=[off.teamFreeThrowPerc, (1 - off.teamFreeThrowPerc)])
            if freeThrow2 == "Make":
                points += 1
                possession = 2
            elif freeThrow2 == "Miss":
                possession = choice([1, 2], 1, p=[offStats['OREB%'], defStats['DREB%']])
                if possession == 1:
                    # print("OREB")
                    addTime = True

    return points, possession, addTime, defFouls, defLast2MinFouls

def singleGameSim(team1Abb, team2Abb, team1=None, team2=None):
    # update stats in outer scope so they can be used elsewhere
    global games, possessions, shots, TOs, PFs, made2s, attempted2s, made3s, attempted3s, commonPFs, shootingPFs,\
        madeFTs, attemptedFTs, score_1, score_2, simScore_1, simScore_2
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

    #print('\n')
    #print(team1ShotFrequency, team1TurnoverPerc, team2PFPerc)
    #print(team2ShotFrequency, team2TurnoverPerc, team1PFPerc)

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
                #possessionPoints, possession, addTime, team2Fouls, team2Last2MinFouls = simPoss(team1, team1Stats, team2Stats, team2Fouls, team2Last2MinFouls, bonus, time)
                off = team1
                offStats = team1Stats
                defStats = team2Stats
                defFouls = team2Fouls
                defLast2MinFouls = team2Last2MinFouls
            else:
                #possessionPoints, possession, addTime, team1Fouls, team1Last2MinFouls = simPoss(team2, team2Stats, team1Stats, team1Fouls, team1Last2MinFouls, bonus, time)
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
        print(team1Abb + " beat " + team2Abb + " by a score of " + str(team1Score) + " to " + str(team2Score))
        return team1Abb, team1Score, team2Score
    else:
        print(team2Abb + " beat " + team1Abb + " by a score of " + str(team2Score) + " to " + str(team1Score))
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
    # get team records
    for team in eastTeamsList.values():
        seasonReport += team.abbreviation + ": " + str(team.wins) + "-" + str(team.losses) + "\n"
    for team in westTeamsList.values():
        seasonReport += team.abbreviation + ": " + str(team.wins) + "-" + str(team.losses) + "\n"
    # seed teams
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

    return seasonReport


def seedTeams(eastTeamsList, westTeamsList):
    # sort teams by wins
    # need to implement tiebreakers for if wins are equal
    seededTeamsEast = sorted(eastTeamsList.items(), key=lambda x: x[1].wins, reverse=True)
    seededTeamsWest = sorted(westTeamsList.items(), key=lambda x: x[1].wins, reverse=True)
    return seededTeamsEast, seededTeamsWest

# team names are corresponding abbreviations
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

from pyFiles.nbaSim import Teams