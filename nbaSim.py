from flask import Flask, render_template
app = Flask(__name__)

from sims import singleGameSim
from sims import seriesSim
from sims import seasonSim
import pickle

LEAGUEID = "00"
SEASONTYPE = "Regular Season"
SEASON = "2023-24"
SEASONENDDATE = 20240414
SEASONSTART = True

class Team:
    def __init__(self, abb, stats):
        self.abbreviation = abb
        self.teamTwoPerc = stats[0]
        self.oppTwoPerc = stats[1]
        self.teamThreePerc = stats[2]
        self.oppThreePerc = stats[3]
        self.teamOREB = stats[4]
        self.teamDREB = stats[5]
        self.teamTurnovers = stats[6]
        self.oppTurnovers = stats[7]
        self.teamPF = stats[8]
        self.oppPF = stats[9]
        self.shootingFoulChance = stats[10]
        self.shootingFoulDrawnChance = stats[11]
        self.twoFrequency = stats[12]
        self.threeFrequency = stats[13]
        self.twoPointAnd1Chance = stats[14]
        self.threePointAnd1Chance = stats[15]
        self.teamFreeThrowPerc = stats[16]
        self.wins = stats[17]
        self.losses = stats[18]
        self.gamesPlayed = stats[19]
        '''self.shotChance = stats[20]
        self.TOChance = stats[21]
        self.CFDChance = stats[22]
        self.oppShotChance = stats[23]
        self.oppTOChance = stats[24]
        self.CFCChance = stats[25]'''

with open('scrapeResults.pickle', 'rb') as pklFile:
    # {abb: list of stats}
    Teams = pickle.load(pklFile)
    #print(Teams)
pklFile.close()

for key, value in Teams.items():
    Teams[key] = Team(key, Teams[key])
    #if SEASONSTART:
       # Teams[key].wins = 0
       # Teams[key].losses = 0


@app.route("/", methods=['GET'])
def home():
    return render_template("nbaSim.html")

@app.route("/singlegamesim", methods=['GET'])
def goToSingleGameSim():
    return render_template("singleGameSim.html")

@app.route("/singlegamesim/<team1Abb>/<team2Abb>", methods=['GET'])
def runSingleGameSim(team1Abb, team2Abb):
    results = singleGameSim(team1Abb, team2Abb)
    return render_template("singleGameSim.html", data=results)

@app.route("/seriessim", methods=['GET'])
def goToSeriesSim():
    return render_template("seriesSim.html")

@app.route("/seriessim/<team1Abb>/<team2Abb>", methods=['GET'])
def runSeriesSim(team1Abb, team2Abb):
    results = seriesSim(team1Abb, team2Abb)
    return render_template("seriesSim.html", data=results)

@app.route("/seasonsim", methods=['GET'])
def goToSeasonSim():
    return render_template("seasonSim.html")

@app.route("/seasonsim/run", methods=['GET'])
def runSeasonSim():
    results = seasonSim()
    return render_template("seasonSim.html", data=results)

####### shooting chance is low, should be around 72%, check all to and pf stats #######################################
####### add to shooting number for shooting fouls and and-1s

if __name__ == "__main__":
    app.run()
    
