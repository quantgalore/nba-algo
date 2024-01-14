# -*- coding: utf-8 -*-
"""
Created in 2024

@author: Quant Galore
"""

import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime, timedelta

def get_favorite(row):
    
    if row["home_team_odds"] < row["away_team_odds"]:
        return row["home_team"]
    elif row["away_team_odds"] < row["home_team_odds"]:
        return row["away_team"]
    else:
        return np.nan
    
def get_winner(row):
    
    if row["home_score"] > row["away_score"]:
        return row["home_team"]
    elif row["away_score"] > row["home_score"]:
        return row["away_team"]
    else:
        return np.nan
    
def favorite_odds(row):
    if row["home_team_odds"] < row["away_team_odds"]:
        return row["home_team_odds"]
    elif row["away_team_odds"] < row["home_team_odds"]:
        return row["away_team_odds"]
    else:
        return np.nan    
    
def implied_prob(odds):
    if odds < 0:
        implied_prob = abs(odds) / (abs(odds) + 100)
    else:
        implied_prob = 100 / (odds + 100)
    return implied_prob    

def favorite_binarizer(row):
    if row["favorite"] == row["winner"]:
        return 1
    else:
        return 0
    
def odds_payoff(odds):
    if odds < 0:
        payoff = (100 / abs(odds)) * 100
    else:
        payoff = (odds / 100) * 100        
    return payoff   

def bet_payoff(row):
    if row["favorite"] == row["winner"]:
        return row["odds_payoff"]
    else:
        return -100
    
api_key = "a79ab26fe613be4ed15c278856bb5dc5"

dates = pd.date_range("2023-10-24", "2024-01-12").strftime("%Y%m%d")

game_datapoint_list = []
times = []

for date in dates:
    
    try:
        
        start_time = datetime.now()
        
        historical_games = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard?dates={date}").json()["events"]
        
        if len(historical_games) <2:
            continue
        
        for historical_game in historical_games:
            game_time = (pd.to_datetime(historical_game["date"])).strftime('%Y-%m-%dT%H:%M:%SZ')
            game_matchup = historical_game["name"]
            
            team_a_name = historical_game["competitions"][0]["competitors"][0]["team"]["displayName"]
            team_a_side = historical_game["competitions"][0]["competitors"][0]["homeAway"]
            team_a_score = historical_game["competitions"][0]["competitors"][0]["score"]
            
            team_b_name = historical_game["competitions"][0]["competitors"][1]["team"]["displayName"]
            team_b_side = historical_game["competitions"][0]["competitors"][1]["homeAway"]
            team_b_score = historical_game["competitions"][0]["competitors"][1]["score"]
            
            if (team_a_side == "home") & (team_b_side == "away"):
                home_team, away_team = team_a_name, team_b_name
                home_score, away_score = team_a_score, team_b_score
            elif (team_a_side == "away") & (team_b_side == "home"):
                home_team, away_team = team_b_name, team_a_name
                home_score, away_score = team_b_score, team_a_score
            
            game_datapoint = pd.DataFrame([{"id":historical_game["id"],"commence_time": game_time, "home_team": home_team, "away_team": away_team,
                                            "home_score": home_score, "away_score": away_score}])
            
            game_datapoint_list.append(game_datapoint)
            
        end_time = datetime.now()
        
        seconds_to_complete = (end_time - start_time).total_seconds()
        times.append(seconds_to_complete)
        iteration = round((np.where(dates==date)[0][0]/len(dates))*100,2)
        iterations_remaining = len(dates) - np.where(dates==date)[0][0]
        average_time_to_complete = np.mean(times)
        estimated_completion_time = (datetime.now() + timedelta(seconds = int(average_time_to_complete*iterations_remaining)))
        time_remaining = estimated_completion_time - datetime.now()
                
        print(f"{iteration}% complete, {time_remaining} left, ETA: {estimated_completion_time}")
    except Exception as espn_error:
        print(espn_error)
        continue

games = pd.concat(game_datapoint_list)    

sport = "basketball_nba"
market = "h2h"

played_game_data_list = []
times = []

for played_game in games["id"]:
    
    try:
        start_time = datetime.now()
        played_game_data = games[games["id"] == played_game].copy()
        date = played_game_data["commence_time"].iloc[0]
    
        odds_request = pd.json_normalize(requests.get(f"https://api.the-odds-api.com/v4/historical/sports/{sport}/odds?apiKey={api_key}&regions=us&markets={market}&oddsFormat=american&date={date}").json()["data"])
        
        odds = odds_request[odds_request["home_team"] == played_game_data["home_team"].iloc[0]].reset_index().copy()
        
        bookmaker_odds = pd.json_normalize(pd.json_normalize(odds["bookmakers"][0][0])["markets"][0][0]["outcomes"])
        
        home_team_odds = bookmaker_odds[bookmaker_odds["name"] == played_game_data["home_team"].iloc[0]]["price"].iloc[0]        
        away_team_odds = bookmaker_odds[bookmaker_odds["name"] == played_game_data["away_team"].iloc[0]]["price"].iloc[0]
        
        played_game_data["home_team_odds"] = home_team_odds
        played_game_data["away_team_odds"] = away_team_odds
        
        played_game_data_list.append(played_game_data)
        
        end_time = datetime.now()
        
        seconds_to_complete = (end_time - start_time).total_seconds()
        times.append(seconds_to_complete)
        iteration = round((np.where(games["id"]==played_game)[0][0]/len(games["id"]))*100,2)
        iterations_remaining = len(games["id"]) - np.where(games["id"]==played_game)[0][0]
        average_time_to_complete = np.mean(times)
        estimated_completion_time = (datetime.now() + timedelta(seconds = int(average_time_to_complete*iterations_remaining)))
        time_remaining = estimated_completion_time - datetime.now()
                
        print(f"{iteration}% complete, {time_remaining} left, ETA: {estimated_completion_time}")
        
    except Exception as odds_error:
        print(odds_error)
        continue

games_with_odds = pd.concat(played_game_data_list)
games_with_odds["commence_time"] = pd.to_datetime(games_with_odds["commence_time"])
  
games_with_odds["favorite"] = games_with_odds.apply(get_favorite, axis = 1)
games_with_odds["winner"] = games_with_odds.apply(get_winner, axis = 1)
games_with_odds["favorite_odds"] = games_with_odds.apply(favorite_odds, axis = 1)
games_with_odds["implied_prob"] = round((games_with_odds["favorite_odds"].apply(implied_prob)*100), 2)
games_with_odds["did_favorite_win"] = games_with_odds.apply(favorite_binarizer, axis = 1)

games_with_odds = games_with_odds.dropna()
# removes data outliers (e.g., impossible -9000)
games_with_odds = games_with_odds[games_with_odds["favorite_odds"] > -300]
games_with_odds["odds_payoff"] = games_with_odds["favorite_odds"].apply(odds_payoff)
games_with_odds["bet_payoff"] = games_with_odds.apply(bet_payoff, axis = 1)


threshold = games_with_odds[(games_with_odds["implied_prob"] >= 50) & (games_with_odds["implied_prob"] <= 60)].copy().sort_values(by="commence_time", ascending = True)
threshold["capital"] = 1000 + threshold["bet_payoff"].cumsum()

win_rate = round((len(threshold[threshold["bet_payoff"] > 0]) / len(threshold))*100,2)
print(f"Win Rate: {win_rate}%")

plt.figure(dpi = 600)
plt.title(f"Win Rate: {win_rate}%")
plt.xticks(rotation=45)
plt.plot(pd.to_datetime(threshold["commence_time"]), threshold["capital"], linestyle='-', color='skyblue', linewidth=2, markersize=6)
plt.show()
