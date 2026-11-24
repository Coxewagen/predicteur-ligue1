# ⚽ **Club Football Match Data**

This dataset offers a simple entrance to the world of football match data analysis. It contains 238,858 football match records across 38 league/division codes, including competitions such as the English Premier League, German Bundesliga, and Spanish La Liga. The match data spans from the 2000/01 season through 3 September 2026, including the complete 2025/26 season and the opening rounds of 2026/27.

Match results and statistics are sourced from [Football-Data.co.uk](https://www.football-data.co.uk/). Elo data are sourced from [ClubElo](https://www.clubelo.com/).

**If you want to work with more data, visit [odds.adamgabor.eu](https://odds.adamgabor.eu/) to browse the available datasets of football odds including World Cup 2026, Champions League 2026/27 and women's football leagues.**

---

## 📅 **DATASET OVERVIEW**

📂 **Files number**: 2

🔗 **Files type**: .csv

⌨️ **Rows**: 238,858 matches and 273,972 Elo records as of 09/2026

💾 **Total size**: approximately 57 MB as of 09/2026


The dataset is a great starting point for football match prediction, both pre-match and in-play, with huge potential lying in the amount of data and their accuracy. The dataset contains information about teams' strength and form prior to the match, as well as general market predictions via pre-match odds.



---

## 🔑 KEY FEATURES

1️⃣ **SIZE** - This is a large open dataset containing uniform information about hundreds of thousands of football matches, including match statistics, odds, form information, and Elo ratings.

2️⃣ **READABILITY** - The whole dataset is tabular, and all of the data are clear to navigate and explain. Both tables in the dataset correspond to each other via remapped club names, and all of the formats within the table (such as odds) are uniform.

3️⃣ **RECENCY** - The latest match is dated 3 September 2026. The dataset currently contains the complete 2025/26 season and the first few rounds of 2026/27; future updates will be added periodically.

---

## 📋 COLUMNS AND DESCRIPTIONS

### 💪 TABLE 1 - ELO RATINGS.csv

This table contains historical Elo snapshots. Records through 1 June 2025 come from [ClubElo](https://www.clubelo.com/). The additional snapshots from 15 June 2025 onward are a provisional continuation generated from the last ClubElo snapshot using the new match results. Snapshots are kept on the 1st and 15th day of the month, and some club names are remapped to correspond with the **Matches** table (*for example, "Bayern" to "Bayern Munich").

|Column | Data Type | Description |
| --- | --- |---|
| **📅 `date`**| *date*|Date of the snapshot. |
| **🛡️ `club`**| *string* |Club name in English corresponding to the Matches table. |
| **🌍️ `country`**| *enum* |Club country three-letter code. |
| **📈 `elo`**| *float* |Club's Elo rating, rounded to two decimal places. |

### 💪 TABLE 2 - MATCHES.csv

This table is a collection of historical match results and statistics taken from [Football-Data.co.uk](https://www.football-data.co.uk). The data are ordered by date, starting from 28 July 2000 and continuing through 3 September 2026. The table contains the most important information about both teams and about the match itself. It is intentionally incomplete in places because the statistics available differ by league and season; users can create smaller sub-tables or remove null values for specific analyses. The table currently contains 238,858 match records.

|Column | Data Type | Description |
| --- | --- |---|
| **🏆 `Division`**| *enum*|League that the match was played in - country code + division number (*I1 for Italian First Division*). For countries where we only have one league, we use 3-letter country code (*ARG for Argentina*). |
| **📆 `MatchDate`**| *date* |Match date in the classic YYYY-MM-DD format. |
| **🕘 `MatchTime`**| *time* |Match time in the HH:MM:SS format. CET-1 timezone. |
| **🏠 `HomeTeam`**| *string* |Home team's club name in English, abbreviated if needed. |
| **🚗 `AwayTeam`**| *string*|Home team's club name in English, abbreviated if needed. |
| **📊 `HomeElo`**| *float* |Home team's most recent Elo rating. |
| **📊 `AwayElo`**| *float* |Away team's most recent Elo rating. |
| **📉 `Form3Home`**| *int* |Number of points gathered by home team in the last 3 matches (*Win = 3 points, Draw = 1 point, Loss = 0 points, so this value is between 0 and 9*). |
| **📈 `Form5Home`**| *int*|Number of points gathered by home team in the last 5 matches (*Win = 3 points, Draw = 1 point, Loss = 0 points, so this value is between 0 and 15*). |
| **📉 `Form3Away`**| *int* |Number of points gathered by away team in the last 3 matches (*Win = 3 points, Draw = 1 point, Loss = 0 points, so this value is between 0 and 9*). |
| **📈 `Form5Away`**| *int* |Number of points gathered by away team in the last 5 matches (*Win = 3 points, Draw = 1 point, Loss = 0 points, so this value is between 0 and 15*). |
| **⚽ `FTHome`**| *int* |Full-time goals scored by home team. |
| **⚽ `FTAway`**| *int*|Full-time goals scored by away team. |
| **🏁 `FTResult`**| *enum* |Full-time result (*H for Home win, D for Draw and A for Away win*). |
| **⚽ `HTHome`**| *int* |Half-time goals scored by home team. |
| **⚽ `HTAway`**| *int* |Half-time goals scored by away team. |
| **⏱️ `HTResult`**| *enum*|Half-time result (*H for Home win, D for Draw and A for Away win*). |
| **🏹 `HomeShots`**| *int* |Total shots (*goal, saved, blocked, off-target*) by home team. |
| **🏹 `AwayShots`**| *int* |Total shots (*goal, saved, blocked, off-target*) by away team. |
| **🎯 `HomeTarget`**| *int* |Total shots on target (*goal, saved*) by home team. |
| **🎯 `AwayTarget`**| *int* |Total shots on target (*goal, saved*) by away team. |
| **🤕 `HomeFouls`**| *int* |Total fouls by home team. |
| **🤕 `AwayFouls`**| *int* |Total fouls by away team. |
| **🚩 `HomeCorners`**| *int* |Total corners taken by home team. |
| **🚩 `AwayCorners`**| *int* |Total corners taken by away team. |
| **🟨 `HomeYellow`**| *int* |Total yellow cards awarded to home team players (*excl. staff*). |
| **🟨 `AwayYellow`**| *int* |Total yellow cards awarded to away team players (*excl. staff*). |
| **🟥 `HomeRed`**| *int* |Total red cards awarded to home team players (*excl. staff*). |
| **🟥 `AwayRed`**| *int* |Total red cards awarded to away team players (*excl. staff*). |
| **1️⃣ `OddHome`**| *float* |Bet365's Home Team Win Odd. |
| **0️⃣ `OddDraw`**| *float* |Bet365's Draw Odd. |
| **2️⃣ `OddAway`**| *float* |Bet365's Away Team Win Odd. |
| **1️⃣ `MaxHome`**| *float* |Maximum Home Team Win Odd from ~17 European bookmakers. |
| **0️⃣ `MaxDraw`**| *float* |Maximum Draw Odd from ~17 European bookmakers. |
| **2️⃣ `MaxAway`**| *float* |Maximum Away Team Win Odd from ~17 European bookmakers. |
| **⬆️ `Over25`**| *float* |Bet365's Over 2.5 Total Goals Scored Odd. |
| **⬇️ `Under25`**| *float* |Bet365's Under 2.5 Total Goals Scored Odd. |
| **⬆️ `MaxOver25`**| *float* |Maximum Over 2.5 Total Goals Scored Odd from ~17 European bookmakers. |
| **⬇️ `MaxUnder25`**| *float* |Maximum Under 2.5 Total Goals Scored Odd from ~17 European bookmakers. |
| **🟰 `HandiSize`**| *float* |Asian handicap size for home team (*negative number indicating stronger home team*) . |
| **➕️ `HandiHome`**| *float* |Bet365's Home Team Win Odd with the given handicap size for Home team. |
| **➖️ `HandiAway`**| *float* |Bet365's Away Team Win Odd with the given handicap size for Home team. |
| **📦 `C_LTH`**| *float* |Likeliness of match falling into the Low Tempo Home-oriented match cluster. |
| **📦 `C_LTA`**| *float* |Likeliness of match falling into the Low Tempo Away-oriented match cluster. |
| **📦 `C_VHD`**| *float* |Likeliness of match falling into the Visibly Home Dominated match cluster. |
| **📦 `C_VAD`**| *float* |Likeliness of match falling into the Visibly Away Dominated match cluster. |
| **📦 `C_HTB`**| *float* |Likeliness of match falling into the High Tempo Balanced match cluster. |
| **📦 `C_PHB`**| *float* |Likeliness of match falling into the Highly Physical Balanced match cluster. |

The six cluster-probability columns are blank for the latest 8,301 appended match rows. They will be recalculated after the clustering model and feature definitions are reviewed.

---

## 🔭 FEATURE ENGINEERING

### 🔗 LAGGED FEATURES

Given that the dataset includes a time data, it offers a possibility to create lagged features. One of those features (Form) is already included in the dataset, but others might include things like goal potency, points gathered during the season, table position, streaks or Elo shifts. These are planned to be added into the dataset in the future as they might contain valuable information for match prediction:

|Column | Data Type | Description |
| --- | --- |---|
| **⚽️ `GF3Home`**| *int*|Goals scored by the Home team in last 3 matches. |
| **⚽️ `GF3Away`**| *int* |Goals scored by the Away team in last 3 matches. |
| **🥅 `GA3Home`**| *int* |Goals conceded by the Home team in last 3 matches. |
| **🥅 `GA3Away`**| *int* |Goals conceded by the Away team in last 3 matches. |
| **⚽️ `GF5Home`**| *int*|Goals scored by the Home team in last 5 matches. |
| **⚽️ `GF5Away`**| *int* |Goals scored by the Away team in last 5 matches. |
| **🥅 `GA5Home`**| *int* |Goals conceded by the Home team in last 5 matches. |
| **🥅 `GA5Away`**| *int* |Goals conceded by the Away team in last 5 matches. |
| **🥅 `GA5Away`**| *int* |Goals conceded by the Away team in last 5 matches. |
| **🏆 `PointsHome`**| *int* |Points gathered in the respective season in the league by Home team. |
| **🏆 `PointsAway`**| *int* |Points gathered in the respective season in the league by Away team. |
| **🏆 `PositionHome`**| *int* |Home team's current position in the league. |
| **🏆 `PositionAway`**| *int* |Away team's current position in the league. |
| **🔥 `WStreakHome`**| *int* |Home team's number of won games in a row. |
| **🔥 `WStreakAway`**| *int* |Away team's number of won games in a row. |
| **🔥 `LStreakHome`**| *int* |Home team's number of lost games in a row. |
| **🔥 `LStreakAway`**| *int* |Away team's number of lost games in a row. |
| **🔥 `SStreakHome`**| *int* |Home team's number of games in a row they scored in. |
| **🔥 `SStreakAway`**| *int* |Away team's number of games in a row they scored in. |
| **🏃 `EloChange1Home`**| *float* |The difference between today's Home team Elo and Home team Elo a month before. |
| **🏃 `EloChange1Away`**| *float* |The difference between today's Away team Elo and Away team Elo a month before. |
| **🏃 `EloChange2Home`**| *float* |The difference between today's Home team Elo and Home team Elo two months before. |
| **🏃 `EloChange2Away`**| *float* |The difference between today's Away team Elo and Away team Elo two months before. |
| **🏠 `HomeRecord`**| *int* |Number of points gathered by home team in the last 5 home matches (*Win = 3 points, Draw = 1 point, Loss = 0 points, so this value is between 0 and 15*). |
| **🚗 `AwayRecord`**| *int*|Number of points gathered by away team in the last 5 away matches (*Win = 3 points, Draw = 1 point, Loss = 0 points, so this value is between 0 and 15*). |
| **💆‍♂️ `RestDaysHome`**| *int*|Number of days between Home team's last match and today (*note this might not give correct and accurate results because of other competitions played in between domestic league matches, such as domestic cups and continental cups, as well as international break games*).|
| **💆‍♂️ `RestDaysAway`**| *int*|Number of days between Away team's last match and today (*note this might not give correct and accurate results because of other competitions played in between domestic league matches, such as domestic cups and continental cups, as well as international break games*).|

### ⛓️‍💥 DERIVED FEATURES

Derived features are computed quickly on-the-go and that's why they are not included in the base dataset, however they may still contain some very useful information that can affect teams' performances such as their relative chances, attacking potence or defensive strength. These are just some of the suggestions for the derived features you can get from the dataset that could come in handy when using the dataset:

|Column | Data Type | Description |
| --- | --- |---|
| **🕘 `MatchDateTime`**| *datetime*|Combining match day and match time as one data type. |
| **⚽️ `TotalGoals`**| *int* |Goals scored by Home team + Goals scored by Away team. |
| **1️⃣0️⃣ `1XOdd`**| *float* |Combined odd for Double chance bet - Home Team Win or a Draw (*making Max1XOdd is also possible*). |
| **0️⃣2️⃣ `X2Odd`**| *float* |Combined odd for Double chance bet - Away Team Win or a Draw (*making MaxX2Odd is also possible*). |
| **1️⃣2️⃣ `12Odd`**| *float* |Combined odd for Double chance bet - Home Team Win or an Away Team Win (*making Max12Odd is also possible*). |
| **📊 `EloDifference`**| *float* |Difference between Home Team Elo rating and Away Team Elo rating. |
| **📊 `EloTotal`**| *float* |Home Team Elo rating + Away Team Elo rating. |
| **📊 `EloAdvantage`**| *float* |EloDifference divided by EloTotal - normalizes the Elo difference to become a percentage. |
| **📉 `Form3Difference`**| *int* |Home Team Form3 - Away Team Form3. |
| **📉 `Form5Difference`**| *int*|Home Team Form5 - Away Team Form5. |
| **↗️ `FormMomentumHome`**| *int* |Difference between Home Team's recent and older form, derived from the formula *Form3Home - (Form5Home - Form3Home)*. Values lie between -15 for the worst momentum and 18 for the best momentum. |
| **↗️ `FormMomentumAway`**| *int* |Difference between Away Team's recent and older form, derived from the formula *Form3Away - (Form5Away - Form3Away)*. Values lie between -15 for the worst momentum and 18 for the best momentum. |
| **1️⃣ `ImpliedProbHome`**| *float* |Probability value for Home Win derived from OddHome using formula *1/OddHome*. |
| **0️⃣ `ImpliedProbDraw`**| *float* |Probability value for a Draw derived from OddDraw using formula *1/OddDraw*. |
| **2️⃣ `ImpliedProbAway`**| *float* |Probability value for Away Win derived from OddAway using formula *1/OddAway*. |
| **➗️ `ImpliedProbTotal`**| *float* |ImpliedProbHome + ImpliedProbDraw + ImpliedProbAway. |
| **💰️ `BookmakerMargin`**| *float* |ImpliedProbTotal - 1. Understoot as a "market uncertainty", can help distinguishing between clear-favorite matches and matches that can go either way. |
| **🏹 `ShotsDifference`**| *int* |HomeShots - AwayShots. |
| **🏹 `ShotsTotal`**| *int* |HomeShots + AwayShots. |
| **🎯 `ShotAccuracyHome`**| *float* |HomeTarget / HomeShots. Gives us % accuracy, this tends to go up as match progresses. Better team does not necessarily need to have better shot accuracy. |
| **🎯 `ShotAccuracyAway`**| *float* |AwayTarget / AwayShots. Gives us % accuracy, this tends to go up as match progresses. Better team does not necessarily need to have better shot accuracy. |
| **🎯 `ShotAccuracyDiff`**| *float* |ShotAccuracyHome - ShotAccuracyAway. |
| **🗡️ `ScoringEfficiencyHome`**| *float* |Derived from Home Team's goals and Home Team's shots on target. Home Elo, Odds and Form can also be taken into account as well as historic scoring ratios. |
| **🗡️ `ScoringEfficiencyAway`**| *float* |Derived from Away Team's goals and Away Team's shots on target. Away Elo, Odds and Form can also be taken into account as well as historic scoring ratios. |
| **🛡️ `DefensiveRatingHome`**| *float* |Derived from Home Team's fouls and Away Team's shots and shots on target. Home Elo, Odds and Form can also be taken into account as well as historic scoring ratios. |
| **🛡️ `DefensiveRatingAway`**| *float* |Derived from Away Team's fouls and Home Team's shots and shots on target. Away Elo, Odds and Form can also be taken into account as well as historic scoring ratios. |
| **🚩 `CornersDifference`**| *int* |HomeCorners - AwayCorners. |
| **🚩 `CornersTotal`**| *int* |HomeCorners + AwayCorners. |
| **🏋️ `GameDominanceIndex`**| *float* |GDI, to some extent reflexing match ball possesion and the number of attacking chances. Derived from shot and corner data using formula (*CornersDifference+ShotsDifference)/2*), can be fine-tuned. |
| **⛔️ `CardPointsHome`**| *int* |HomeYellow + 2* HomeRed. Multiplier of 3 or 4 can also be used to get better results in Machine Learning. |
| **⛔️ `CardPointsAway`**| *int* |AwayYellow+ 2* AwayRed. Multiplier of 3 or 4 can also be used to get better results in Machine Learning. |
| **⛔️ `CardPointsDiff`**| *int* |CardPointsHome - CardPointsAway. |
| **🧱 `DrawLikelihood`**| *float* |Derived from EloDifference, Form5Difference and ImpliedProbDraw. Gives a weighted % likelihood of a draw, which is notoriously difficult to predict when predicting football matches. Used to counter-weight the clear-winner-biased Machine Learning methods. |
| **🧤 `CleanSheetProbHome`**| *float* |Derived from DefensiveRatingHome and ScoringEfficiencyAway. Gives a weighted % likelihood of Home Team keeping a clean sheet. |
| **🧤 `CleanSheetProbAway`**| *float* |Derived from DefensiveRatingAway and ScoringEfficiencyHome. Gives a weighted % likelihood of Away Team keeping a clean sheet. |
| **🔍️ `ExpectedGoalsHome`**| *float* |Derived from HomeTarget, ShotAccuracyHome, OddHome and recent home scoring trends (*not to be confused with popular xG metric not included in this dataset*). |
| **🔍️ `ExpectedGoalsAway`**| *float* |Derived from AwayTarget, ShotAccuracyAway, OddAway and recent away scoring trends (*not to be confused with popular xG metric not included in this dataset*). |

---

## 🚀 POSSIBLE APPLICATIONS

⌛️ **History book**: Has a team ever won when 3-0 down at halftime? Browse historical data and find bizarre records, oddities, and against-the-odds performances of your favorites.

🔎 **Hypothesis testing**:  Are more goals scored during late-night matches? Do Premier League players have better shot accuracy? Test your own hypothesis on this huge dataset.

📊 **Match prediction**: Who's going to win and by what margin? Predict match outcomes, total goals, or team goals before or during the actual game using historical data, team form data, and match stats.

🆚 **Team comparison**: United 2007/08 or City 2022/23? Compare teams' historical seasons, their points, game results, and form streaks during different periods of time.

🖼️ **Data visualization**: Elo strength over time, average goals scored per league, or anything else - create data visualizations and accurate graphs from any metrics possible.

---

## ✒️ CITING THIS REPOSITORY

If you use this repository or its contents, please use the following information to cite it.

**Author:** Adam Gábor  
**ORCID:** https://orcid.org/0009-0001-9252-5976  
**Affiliation:** Faculty of Informatics and Information Technologies, Slovak University of Technology in Bratislava  
**Year:** 2026

**Example citation:**
Gábor, A. (2026). Club Football Match Data. Retrieved from https://github.com/xgabora/Club-Football-Match-Data/.

## ➗ GETTING MORE FOOTBALL DATA - ODDS FROM 45 LEAGUES

Looking for clean and ready-to-use historical football bookmaker odds in JSON? The packs include World Cup 2026 odds and a larger European football collection covering markets such as 1X2, double chance, goals, handicaps, correct scores, corners, half-time markets and more, perfectly suitable for machine learning, model testing and market analysis.

Visit [odds.adamgabor.eu](https://odds.adamgabor.eu/) to browse the available datasets.
