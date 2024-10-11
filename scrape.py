from nba_api.stats.endpoints import cumestatsteamgames
from nba_api.stats.endpoints import teamdashptshots
from nba_api.stats.static import teams

import time
import pickle
from bs4 import BeautifulSoup
from selenium import webdriver
from datetime import date
import requests

LEAGUEID = "00"
SEASONTYPE = "Regular Season"
SEASON = "2023-24"
SEASONENDDATE = 20240414
SEASONSTART = True
SEASONSTARTDATE = 20231024
#SEASONSTARTDATE = 20240401
ALLSTARDATE = 20240218
NBACUPFINALDATE = 20231209

LEAPYEAR = False
year = date.today().year
if year % 4 == 0 and year % 100 != 0 or year % 400 == 0:
    LEAPYEAR = True
else:
    LEAPYEAR = False


def scrapeTeamStats(abbreviation):
        start_time = time.time()
        # get team ID
        teamName = teams.find_team_by_abbreviation(abbreviation)
        time.sleep(0.6)
        ID = str(teamName["id"])
        teamRankingsName = teamName["full_name"].replace(' ', '-')
        # get team games
        teamGames = cumestatsteamgames.CumeStatsTeamGames(team_id=ID, league_id=LEAGUEID, season=SEASON,
                                                          season_type_all_star=SEASONTYPE).cume_stats_team_games.get_dict()[
            'data']
        time.sleep(0.6)

        gameIDs = ""
        for game in teamGames:
            gameIDs += str(game[1])
            gameIDs += "|"

        # get team stats
        # print(f'teamID: {ID}, gameids: {gameIDs}')
        # stats = cumestatsteam.CumeStatsTeam(team_id=ID, game_ids=gameIDs, league_id=LEAGUEID, season=SEASON, season_type_all_star=SEASONTYPE).total_team_stats.get_dict()
        URL = f"https://www.teamrankings.com/nba/team/{teamRankingsName}/stats"
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        browser = webdriver.Chrome(options=options)
        browser.get(URL)
        time.sleep(4)
        html = browser.page_source
        soup = BeautifulSoup(html, features="html.parser")
        soup.prettify()
        elements = soup.find_all('td', class_='nowrap')
        ### could just define here instead of making array to draw from
        teamStats = [float(elements[53].get_text().split(' ')[0].replace('%', '')),
                          float(elements[49].get_text().split(' ')[0].replace('%', '')),
                          float(elements[45].get_text().split(' ')[0].replace('%', '')),
                          float(elements[81].get_text().split(' ')[0].replace('%', '')),
                          float(elements[41].get_text().split(' ')[0].replace('%', '')),
                          float(elements[105].get_text().split(' ')[0].replace('%', '')),
                          float(elements[109].get_text().split(' ')[0].replace('%', '')),
                          float(elements[145].get_text().split(' ')[0].replace('%', '')),
                          float(elements[137].get_text().split(' ')[0].replace('%', '')),
                          float(elements[55].get_text().split(' ')[0].replace('%', '')),
                          float(elements[51].get_text().split(' ')[0].replace('%', '')),
                          float(elements[47].get_text().split(' ')[0].replace('%', '')),
                          float(elements[83].get_text().split(' ')[0].replace('%', '')),
                          float(elements[147].get_text().split(' ')[0].replace('%', '')),
                          float(elements[139].get_text().split(' ')[0].replace('%', '')),
                          float(elements[65].get_text().split(' ')[0].replace('%', '')),
                          float(elements[67].get_text().split(' ')[0].replace('%', '')),
                          float(elements[73].get_text().split(' ')[0].replace('%', '')),
                          float(elements[75].get_text().split(' ')[0].replace('%', '')),
                          ]
        browser.quit()

        URL = f"https://www.teamrankings.com/nba/team/{teamRankingsName}/"
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        browser = webdriver.Chrome(options=options)
        browser.get(URL)
        time.sleep(4)
        html = browser.page_source
        soup = BeautifulSoup(html, features="html.parser")
        soup.prettify()
        elements = soup.find_all('td', class_='top')
        record = elements[0].get_text().split('(')[1].split(')')[0]
        # games, wins, and losses are not reg season only
        wins = int(record.split('-')[0])
        losses = int(record.split('-')[1])
        gamesPlayed = int(wins + losses)

        browser.quit()

        # time.sleep(0.6)
        teamShotTendicies = teamdashptshots.TeamDashPtShots(team_id=ID).general_shooting.get_dict()
        time.sleep(0.6)

        URL = "http://www.pbpstats.com/totals/nba/team?Season=2023-24&SeasonType=Regular+Season&StartType=All&Type=Team&StatType=Totals&Table=Fouls"
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        browser = webdriver.Chrome(options=options)
        browser.get(URL)
        time.sleep(4)
        html = browser.page_source
        soup = BeautifulSoup(html, features="html.parser")
        soup.prettify()
        elements = soup.find_all("span", title=abbreviation)
        FC = int(elements[1].get_text())
        OFC = int(elements[5].get_text()) + int(elements[6].get_text())
        SFC = int(elements[2].get_text())
        CFC = FC - OFC - SFC
        FD = int(elements[15].get_text())
        OFD = int(elements[7].get_text()) + int(elements[8].get_text())

        browser.quit()  ### check speed of closing and opening again ##############

        URL = "http://www.pbpstats.com/totals/nba/team?Season=2023-24&SeasonType=Regular+Season&StartType=All&Type=Team&StatType=Totals&Table=FTs"
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        browser = webdriver.Chrome(options=options)
        browser.get(URL)
        time.sleep(4)
        html = browser.page_source
        soup = BeautifulSoup(html, features="html.parser")
        soup.prettify()
        # print(soup)
        elements = soup.find_all("span", title=abbreviation)
        # print(elements)
        twoShootingFoulsDrawn = int(elements[3].get_text())
        threeShootingFoulsDrawn = int(elements[5].get_text())
        shootingFoulsDrawn = twoShootingFoulsDrawn + threeShootingFoulsDrawn
        twoPointAnd1s = int(elements[4].get_text())
        threePointAnd1s = int(elements[6].get_text())
        twoPointAnd1Chance = twoPointAnd1s / shootingFoulsDrawn
        threePointAnd1Chance = threePointAnd1s / shootingFoulsDrawn
        shootingFoulDrawnChance = shootingFoulsDrawn / FD
        # print(shootingFoulsDrawn, twoPointAnd1s, threePointAnd1s, twoPointAnd1Chance, threePointAnd1Chance)

        browser.quit()

        '''URL = "http://www.pbpstats.com/totals/nba/team?Season=2023-24&SeasonType=Regular%20Season&StartType=All&Type=Team&StatType=Totals&Table=Scoring"
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        browser = webdriver.Chrome(options=options)
        browser.get(URL)
        time.sleep(4)
        html = browser.page_source
        soup = BeautifulSoup(html, features="html.parser")
        soup.prettify()
        elements = soup.find_all("span", title=abbreviation)
        twoPA = int(elements[4].get_text())
        threePA = int(elements[7].get_text())

        browser.quit()'''

        URL = "http://www.pbpstats.com/totals/nba/team?Season=2023-24&SeasonType=Regular%20Season&StartType=All&Type=Team&StatType=Totals&Table=Turnovers"
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        browser = webdriver.Chrome(options=options)
        browser.get(URL)
        time.sleep(4)
        html = browser.page_source
        soup = BeautifulSoup(html, features="html.parser")
        soup.prettify()
        elements = soup.find_all("span", title='DEN')
        totalTOs = int(elements[1].get_text())

        browser.quit()

        # team stats
        teamFgPerc = teamStats[0] / 100  # might have to calc manually to be exact
        teamTwoPerc = teamStats[1] / 100
        teamThreePerc = teamStats[2] / 100  # might have to calc manually to be exact
        teamFreeThrowAttempts = teamStats[3] / 100
        teamFreeThrowPerc = teamStats[4] / 100
        teamOREB = teamStats[5]
        teamDREB = teamStats[6]
        # should divide by num of possessions a game?
        teamPF = teamStats[7] / 100
        teamTurnovers = teamStats[8] / 100

        shootingFoulChance = ((SFC / gamesPlayed) / 100) / teamPF
        #print(shootingFoulChance, shootingFoulDrawnChance)

        # opp stats
        oppFgPerc = teamStats[9] / 100  # might have to calc manually to be exact
        oppTwoPerc = teamStats[10] / 100
        oppThreePerc = teamStats[11] / 100  # might have to calc manually to be exact
        oppFreeThrowAttempts = teamStats[12] / 100
        # should divide by num of possessions a game?
        oppPF = teamStats[13] / 100
        oppTurnovers = teamStats[14] / 100

        # shot tendecies
        for list in teamShotTendicies['data']:
            if list[4] == 'Totals':
                twoFrequency = list[10]
                threeFrequency = list[14]

        end_time = time.time()
        print(f'Time to complete team scrape: {end_time - start_time}')
        # print(teamShotTendicies['data'], twoFrequency, threeFrequency)
        # bug with API for OKC teamShotTendicies 
        # if (abbreviation == 'okc' or abbreviation == 'OKC'):
        #   twoFrequency = teamShotTendicies["data"][2][10]
        #  threeFrequency = teamShotTendicies["data"][2][14]
        '''
        ### sim 2.0 stats needed
        CFD = FD - OFD - shootingFoulsDrawn
        fga = int(teamStats[15] * gamesPlayed)
        SFDminusAnd1s = shootingFoulsDrawn - twoPointAnd1s - threePointAnd1s
        totalPoss = fga + SFDminusAnd1s + totalTOs + CFD
        shotChance = (fga + SFDminusAnd1s) / totalPoss
        TOChance = totalTOs / totalPoss
        CFDChance = CFD / totalPoss
        oppFGA = int(teamStats[16] * gamesPlayed)
        SFCminusAnd1s = SFC - 199 # stat not availble -> league wide avg of and1s
        oppTotalTOs = int(oppTurnovers * gamesPlayed)
        oppTotalPoss = oppFGA + SFCminusAnd1s + oppTotalTOs + CFC
        oppShotChance = (oppFGA + SFCminusAnd1s) / oppTotalPoss
        oppTOChance = oppTotalTOs / oppTotalPoss
        CFCChance = CFC / oppTotalPoss

        print(totalPoss, shotChance, TOChance, CFDChance)
        print(oppTotalPoss, oppShotChance, oppTOChance, CFCChance)

        threesAttempted = int(teamStats[17] * gamesPlayed)
        oppThreesAttempted = int(teamStats[18] * gamesPlayed)
        twosAttempted = fga - threesAttempted
        oppTwosAttempted = oppFGA - oppThreesAttempted

        totalTwosPoss = twosAttempted + twoShootingFoulsDrawn - twoPointAnd1s
        totalThreesPoss = threesAttempted + threeShootingFoulsDrawn - threePointAnd1s
        oppTotalTwosPoss = oppTwosAttempted + oppTwoShootingFoulsDrawn - twoPointAnd1s
        oppTotalThreesPoss = threesAttempted + threeShootingFoulsDrawn - threePointAnd1s
        
        twoNoFoulChance = (twosAttempted - twoPointAnd1s) / totalTwosPoss
        twoShootingFoulChance = (twoShootingFoulsDrawn - twoPointAnd1s) / totalTwosPoss
        twoAnd1Chance = twoPointAnd1s / totalTwosPoss
        oppTwoNoFoulChance = (oppTwosAttempted - 199) / oppTotalTwosPoss
        oppTwoShootingFoulChance = (twoShootingFoulsDrawn - 199) / totalTwosPoss
        oppTwoAnd1Chance = 199 / totalTwosPoss
        threeNoFoulChance = (threesAttempted - threePointAnd1s) / totalThreesPoss
        '''
        return ([teamTwoPerc, oppTwoPerc, teamThreePerc, oppThreePerc, teamOREB, teamDREB, teamTurnovers, oppTurnovers,
                teamPF, oppPF, shootingFoulChance, shootingFoulDrawnChance, twoFrequency, threeFrequency,
                twoPointAnd1Chance, threePointAnd1Chance, teamFreeThrowPerc, wins, losses, gamesPlayed])
                #, shotChance, TOChance, CFDChance, oppShotChance, oppTOChance, CFCChance]


teamAbbs = ['ATL', 'BOS', 'BKN', 'CHA', 'CHI', 'CLE', 'DET', 'IND', 'MIA', 'MIL', 'NYK', 'ORL', 'PHI', 'TOR', 'WAS',
            'DAL', 'DEN', 'GSW', 'HOU', 'LAC', 'LAL', 'MEM', 'MIN', 'NOP', 'OKC', 'PHX', 'POR', 'SAC', 'SAS', 'UTA']

Teams = {}


def createStatsFile():
    for abb in teamAbbs:
        Teams.update({abb: scrapeTeamStats(abb)})
        print(f'Completed {abb} scrape')

    with open('scrapeResults.pickle', 'wb') as pklFile:
        pickle.dump(Teams, pklFile)
    pklFile.close()


def scrapeSchedule():
    today = date.today()
    today = int(today.strftime("%Y%m%d"))
    if SEASONSTART:
        today = SEASONSTARTDATE
    teamNames = []
    schedule = {}
    while today <= SEASONENDDATE:
        print(today)
        URL = "https://www.cbssports.com/nba/schedule/" + str(today) + "/"
        int(today)
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")
        elements = soup.find_all("span", class_="TeamName")
        num = 0
        for element in elements:
            textElement = element.find("a")
            teamNames.append(textElement.text)
            num += 1
        if len(teamNames) != 0:
            print(teamNames)
            schedule.update({today: teamNames[0:]})
        teamNames.clear()
        today += 1

        if str(today)[-4:] == '1232':
            today = int(str(int(str(today)[0:4]) + 1) + '0101')
        if str(today)[-4:] == '1032':
            today = int(str(today)[0:4] + str(int(str(today)[4:6]) + 1) + '01')
        if str(today)[-4:] == '1131':
            today = int(str(today)[0:4] + str(int(str(today)[4:6]) + 1) + '01')
        if str(today)[-4:] == '0132':
            today = int(str(today)[0:4] + '0' + str(int(str(today)[4:6]) + 1) + '01')

        testStr = ''
        if LEAPYEAR:
            testStr = '0230'
        else:
            testStr = '0229'
        if str(today)[-4:] == testStr:
            today = int(str(today)[0:4] + '0' + str(int(str(today)[4:6]) + 1) + '01')
        if str(today)[-4:] == '0431':
            today = int(str(today)[0:4] + '0' + str(int(str(today)[4:6]) + 1) + '01')
        if str(today)[-4:] == '0332':
            today = int(str(today)[0:4] + '0' + str(int(str(today)[4:6]) + 1) + '01')
        if today == ALLSTARDATE or today == NBACUPFINALDATE:
            today += 1

    return schedule


def createScheduleFile():
    schedule = scrapeSchedule()
    with open('scrapeSchedule.pickle', 'wb') as pklFile:
        pickle.dump(schedule, pklFile)
    pklFile.close()


def readScheduleFile():
    with open('scrapeSchedule.pickle', 'rb') as pklFile:
        schedule = pickle.load(pklFile)
        #print(schedule)
    pklFile.close()
    return schedule


#createScheduleFile()
#readScheduleFile()

