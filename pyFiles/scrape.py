from nba_api.stats.endpoints import teamdashptshots
from nba_api.stats.static import teams
import nba_api.stats.endpoints.teaminfocommon as teamInfoCommon

import time
import pickle
from bs4 import BeautifulSoup
from selenium import webdriver
from datetime import date
import requests
from pyFiles import basicInfo as bi
import re

LEAPYEAR = False
year = date.today().year
if year % 4 == 0 and year % 100 != 0 or year % 400 == 0:
    LEAPYEAR = True
else:
    LEAPYEAR = False


def scrapeTeamStats(Teams):
        start_time = time.time()

        for abb, list in Teams.items():
            teamInfoList = list[0]
            statDict = list[1]
            # get team name info from swar api and add ID, division to Team info list
            teamName = teams.find_team_by_abbreviation(abb)
            time.sleep(0.6)
            ID = str(teamName["id"])
            teamInfoList.append(ID)
            teamRankingsName = teamName["full_name"].replace(' ', '-')
            
            # get team division
            teamInfo = teamInfoCommon.TeamInfoCommon(league_id='00', team_id=ID).get_dict()['resultSets'][0]['rowSet'][0]
            division = teamInfo[6]
            conference = teamInfo[5]
            teamInfoList.append(division)
            teamInfoList.append(conference)

            # Site 1
            URL = f"https://www.teamrankings.com/nba/team/{teamRankingsName}/stats"
            page = requests.get(URL)
            soup = BeautifulSoup(page.content, "html.parser")
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

            # Site 2
            URL = f"https://www.teamrankings.com/nba/team/{teamRankingsName}/"
            page = requests.get(URL)
            soup = BeautifulSoup(page.content, "html.parser")
            elements = soup.find_all('td', class_='top')
            record = elements[0].get_text().split('(')[1].split(')')[0]
            # games, wins, and losses are not reg season only
            wins = int(record.split('-')[0])
            losses = int(record.split('-')[1])
            gamesPlayed = int(wins + losses)

            # team stats
            teamFgPerc = teamStats[0] / 100  # might have to calc manually to be exact
            teamTwoPerc = teamStats[1] / 100
            teamThreePerc = teamStats[2] / 100  # might have to calc manually to be exact
            teamFreeThrowAttempts = teamStats[3] / 100
            teamFreeThrowPerc = teamStats[4] / 100
            teamOREB = teamStats[5]
            teamDREB = teamStats[6]
            # should divide by num of possessions a game?
            #teamPF = teamStats[7] / 100
            teamTurnovers = teamStats[8] / 100

            # opp stats
            oppFgPerc = teamStats[9] / 100  # might have to calc manually to be exact
            oppTwoPerc = teamStats[10] / 100
            oppThreePerc = teamStats[11] / 100  # might have to calc manually to be exact
            oppFreeThrowAttempts = teamStats[12] / 100
            # should divide by num of possessions a game?
            #oppPF = teamStats[13] / 100
            oppTurnovers = teamStats[14] / 100

            # shot tendencies
            teamShotTendencies = teamdashptshots.TeamDashPtShots(team_id=ID).general_shooting.get_dict()
            time.sleep(1)

            for list1 in teamShotTendencies['data']:
                if list1[4] == 'Totals':
                    twoFrequency = list1[10]
                    threeFrequency = list1[14]

            # 0 is used as placeholder for teamDefPF, oppDefPF, shootingFoulChance, shootingFoulDrawnChance,
            # twoPointAnd1Chance, and threePointAnd1Chance, as they will be inserted below
            stats = [teamTwoPerc, oppTwoPerc, teamThreePerc, oppThreePerc, teamOREB, teamDREB, teamTurnovers, oppTurnovers,
                0, 0, 0, 0, twoFrequency, threeFrequency, 0, 0, teamFreeThrowPerc, wins, losses, gamesPlayed]
            for stat in stats:
                statDict.append(stat)

        by_team_time = time.time()
        print(f'Time to complete section 1 of scrape (by team sites): {by_team_time - start_time}')

        # Site 3
        URL = "http://www.pbpstats.com/totals/nba/team?Season=2024-25&SeasonType=Regular+Season&StartType=All&Type=Team&StatType=Totals&Table=Fouls"
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        browser = webdriver.Chrome(options=options)
        browser.get(URL)
        time.sleep(5)
        html = browser.page_source
        soup = BeautifulSoup(html, features="html.parser")
        soup.prettify()

        for abb, list in Teams.items():
            statDict = list[1]
            elements = soup.find_all("span", title=abb)

            ### Commented out stats that weren't being used. Needed at all? What are they?
            FC = int(elements[1].get_text())
            OFC = int(elements[5].get_text()) + int(elements[6].get_text())
            SFC = int(elements[2].get_text())
            CFC = FC - OFC - SFC
            FD = int(elements[15].get_text())
            OFD = int(elements[7].get_text()) + int(elements[8].get_text())
            DFC = FC - OFC
            DFD = FD - OFD
            statDict[8] = DFC / gamesPlayed / 100
            statDict[9] = DFD / gamesPlayed / 100
            statDict.append(SFC)
            statDict.append(FD)

        browser.quit()  ### check speed of closing and opening again ##############
        pbp1_time = time.time()
        print(f'Time to complete section 2 of scrape (PBP Site 1): {pbp1_time - by_team_time}')

        # Site 4
        URL = "http://www.pbpstats.com/totals/nba/team?Season=2024-25&SeasonType=Regular+Season&StartType=All&Type=Team&StatType=Totals&Table=FTs"
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        browser = webdriver.Chrome(options=options)
        browser.get(URL)
        time.sleep(5)
        html = browser.page_source
        soup = BeautifulSoup(html, features="html.parser")
        soup.prettify()

        for abb, list in Teams.items():
            statDict = list[1]
            elements = soup.find_all("span", title=abb)
            #                        SFC           gamesPlayed    poss     teamDefPF
            shootingFoulChance = ((statDict[20] / statDict[19]) / 100) / statDict[8]

            twoShootingFoulsDrawn = int(elements[3].get_text())
            threeShootingFoulsDrawn = int(elements[5].get_text())
            shootingFoulsDrawn = twoShootingFoulsDrawn + threeShootingFoulsDrawn
            twoPointAnd1s = int(elements[4].get_text())
            threePointAnd1s = int(elements[6].get_text())
            twoPointAnd1Chance = twoPointAnd1s / shootingFoulsDrawn
            threePointAnd1Chance = threePointAnd1s / shootingFoulsDrawn
            #                               SFD                gp         poss     oppDefPF
            shootingFoulDrawnChance = (shootingFoulsDrawn / statDict[19] / 100) / statDict[9]

            # Filling placeholders for shootingFoulChance, shootingFoulDrawnChance, twoPointAnd1Chance, and threePointAnd1Chance
            statDict[10] = shootingFoulChance
            statDict[11] = shootingFoulDrawnChance
            statDict[14] = twoPointAnd1Chance
            statDict[15] = threePointAnd1Chance

        browser.quit()
        pbp2_time = time.time()
        print(f'Time to complete section 3 of scrape (PBP Site 2): {pbp2_time - pbp1_time}')

        end_time = time.time()
        print(f'Time to complete entire scrape: {end_time - start_time}')

        return Teams


def createStatsFile(Teams):
    Teams = scrapeTeamStats(Teams)
    return Teams

def readStatsFile():
    with open('../pklFiles/scrapeResults.pickle', 'rb') as pklFile:
        stats = pickle.load(pklFile)
    pklFile.close()
    return stats

def scrapeSchedule(Teams):
    # add placeholder (0) for teams points that will be added to below
    for abb, list in Teams.items():
        list[0].append(0)
    irlToday = date.today()
    irlToday = int(irlToday.strftime("%Y%m%d"))
    # Start scrape at beginning of season
    today = bi.SEASONSTARTDATE
    teamNames = []
    schedule = {}
    scores = []
    while today <= bi.SEASONENDDATE:
        print(today)
        URL = "https://www.cbssports.com/nba/schedule/" + str(today) + "/"
        int(today)
        page = requests.get(URL)
        soup = BeautifulSoup(page.content, "html.parser")
        elements = soup.find_all("span", class_="TeamName")
        # get results cell so if game is postponed it can be skipped
        # also get so scores can be tracked for tiebreakers
        results = soup.find_all("div", class_="CellGame")
        # find postponed games to exclude (excluded by index)
        postponed = []
        num = 0
        for result in results:
            if "Postponed" in result.text:
                postponed.append(num * 2)
                postponed.append((num * 2) + 1)
            # add game result to scores for tiebreaking needs
            elif today < irlToday:
                score = ''
                text = result.text.split("/")[0]
                parts = text.split()
                team1Points = int(parts[1])
                team2Points = int(parts[4])
                for char in text:
                    if not char.isdigit() and char != ' ':
                        score += char
                # convert from CBS abb to Team abbs
                if 'NY' in score:
                    score = score.replace('NY', 'NYK')
                if 'GS' in score:
                    score = score.replace('GS', 'GSW')
                if 'NO' in score:
                    score = score.replace('NO', 'NOP')
                if 'PHO' in score:
                    score = score.replace('PHO', 'PHX')
                if 'SA' in score:
                    # take out SA if it is not followed by C (SAC - Sacramento)
                    score = re.sub(r'SA(?!C)', 'SAS', score)
                abbreviations = score.split('-')
                scores.append(abbreviations)
                abb1 = abbreviations[0]
                abb2 = abbreviations[1]
                # add to teams total points
                Teams[abb1][0][-1] += team1Points
                Teams[abb2][0][-1] += team2Points
            num += 1
        # get team names
        num = 0
        for element in elements:
            # skip if postponed
            if num in postponed:
                num += 1
                continue
            textElement = element.find("a")
            teamNames.append(textElement.text)
            num += 1
        # if day isn't empty, add to schedule
        if len(teamNames) != 0:
            print(teamNames)
            schedule.update({today: teamNames[0:]})
        teamNames.clear()
        today += 1

        # if end of month, correctly go to next month
        if str(today)[-4:] == '1232':
            today = int(str(int(str(today)[0:4]) + 1) + '0101')
        if str(today)[-4:] == '1032':
            today = int(str(today)[0:4] + str(int(str(today)[4:6]) + 1) + '01')
        if str(today)[-4:] == '1131':
            today = int(str(today)[0:4] + str(int(str(today)[4:6]) + 1) + '01')
        if str(today)[-4:] == '0132':
            today = int(str(today)[0:4] + '0' + str(int(str(today)[4:6]) + 1) + '01')

        # account for leap year
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
        # skip all star game and nba cup final as they do not count towards regular season
        # what if these fall at the end of a month?
        if today == bi.ALLSTARDATE or today == bi.NBACUPFINALDATE:
            today += 1

    return schedule, scores, Teams

# create schedule and scores file
def createScheduleFile(Teams):
    schedule, scores, Teams = scrapeSchedule(Teams)
    with open('../pklFiles/scrapeSchedule.pickle', 'wb') as pklFile:
        pickle.dump(schedule, pklFile)
    pklFile.close()
    with open('../pklFiles/scrapeScores.pickle', 'wb') as pklFile:
        pickle.dump(scores, pklFile)
    pklFile.close()
    return Teams


def readScheduleFile():
    with open('../pklFiles/scrapeSchedule.pickle', 'rb') as pklFile:
        schedule = pickle.load(pklFile)
    pklFile.close()
    return schedule

def readScoresFile():
    with open('../pklFiles/scrapeScores.pickle', 'rb') as pklFile:
        scores = pickle.load(pklFile)
    pklFile.close()
    return scores

def scrape():
    # dictionary of teams with an empty stat list to be filled
    Teams = {'ATL': [[], []], 'BOS': [[], []], 'BKN': [[], []], 'CHA': [[], []], 'CHI': [[], []], 'CLE': [[], []],
             'DET': [[], []], 'IND': [[], []], 'MIA': [[], []],
             'MIL': [[], []], 'NYK': [[], []], 'ORL': [[], []], 'PHI': [[], []], 'TOR': [[], []], 'WAS': [[], []],
             'DAL': [[], []], 'DEN': [[], []], 'GSW': [[], []],
             'HOU': [[], []], 'LAC': [[], []], 'LAL': [[], []], 'MEM': [[], []], 'MIN': [[], []], 'NOP': [[], []],
             'OKC': [[], []], 'PHX': [[], []], 'POR': [[], []],
             'SAC': [[], []], 'SAS': [[], []], 'UTA': [[], []]}
    Teams = createStatsFile(Teams)
    Teams = createScheduleFile(Teams)
    # scrapeResults holds team stats (Teams)
    with open('../pklFiles/scrapeResults.pickle', 'wb') as pklFile:
        pickle.dump(Teams, pklFile)
    pklFile.close()
    print(f'\n\nStats file: \n{readStatsFile()}\n\n')
    print(f'Schedule file: \n{readScheduleFile()}\n\n')
    print(f'Scores file: \n{readScoresFile()}\n\n')

#scrape()

