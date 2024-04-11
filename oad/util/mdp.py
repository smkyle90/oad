import pandas as pd

from .helpers import get_live_scores

# Major DRAFT POOL
ALL_PICKS = [
    ("Tom", "Scottie Scheffler"),
    ("Lucas", "Rory McIlroy"),
    ("David", "Jon Rahm"),
    ("Scott", "Brooks Koepka"),
    ("Jamil", "Xander Schauffele"),
    ("Sohale", "Hideki Matsuyama"),
    ("Brock", "Patrick Cantlay"),
    ("Brady", "Wyndham Clark"),
    ("Brady", "Joaquín Niemann"),
    ("Brock", "Tiger Woods"),
    ("Sohale", "Ludvig Åberg"),
    ("Jamil", "Jordan Spieth"),
    ("Scott", "Viktor Hovland"),
    ("David", "Will Zalatoris"),
    ("Lucas", "Matt Fitzpatrick"),
    ("Tom", "Bryson DeChambeau"),
    ("Tom", "Tony Finau"),
    ("Lucas", "Cameron Young"),
    ("David", "Justin Thomas"),
    ("Scott", "Dustin Johnson"),
    ("Jamil", "Cameron Smith"),
    ("Sohale", "Collin Morikawa"),
    ("Brock", "Max Homa"),
    ("Brady", "Sahith Theegala"),
    ("Brady", "Tyrrell Hatton"),
    ("Brock", "Jason Day"),
    ("Sohale", "Tom Kim"),
    ("Jamil", "Shane Lowry"),
    ("Scott", "Min Woo Lee"),
    ("David", "Brian Harman"),
    ("Lucas", "Russell Henley"),
    ("Tom", "Corey Conners"),
    ("Tom", "Patrick Reed"),
    ("Lucas", "Sam Burns"),
    ("David", "Tommy Fleetwood"),
    ("Scott", "Sergio Garcia"),
    ("Jamil", "Akshay Bhatia"),
    ("Sohale", "Sungjae Im"),
    ("Brock", "Rickie Fowler"),
    ("Brady", "Justin Rose"),
    ("Brady", "Nick Taylor"),
    ("Brock", "Denny McCarthy"),
    ("Sohale", "Si Woo Kim"),
    ("Jamil", "Adam Scott"),
    ("Scott", "Byeong Hun An"),
    ("David", "Chris Kirk"),
    ("Lucas", "Harris English"),
    ("Tom", "Erik van Rooyen"),
]


def major_draft_pool():
    # df = pd.read_csv("./oad/util/mdp.csv")

    data_dict = {
        "User": [],
        "Player": [],
    }

    for u, p in ALL_PICKS:
        data_dict["User"].append(u)
        data_dict["Player"].append(p)

    df = pd.DataFrame(data_dict)

    # live scores from API for each pick.
    live_scores = get_live_scores(df.Player.to_list())

    curr_round = 0
    for player, data in live_scores.items():
        curr_round = max(curr_round, data["round"])

    df["Pick"] = [i // len(df.User.unique()) + 1 for i in range(len(df))]
    df["Total Score"] = [live_scores[player]["score"] for player in df.Player]
    df["Position"] = [live_scores[player]["position"] for player in df.Player]
    df["Round"] = [live_scores[player]["round"] for player in df.Player]
    df["Scores"] = [
        "{} ({})".format(row["Player"], row["Total Score"])
        for idx, row in df.iterrows()
    ]

    count_df = df[df["Position"] != "--"]
    count_df.sort_values(["Total Score"], inplace=True, ascending=True)
    count_df = count_df[count_df.Round == curr_round]
    count_df = count_df.groupby("User").head(3)

    freq_df = count_df.groupby("User").count()
    N = 3
    all_teams = set(df.User)
    valid_teams = set(freq_df[freq_df.Pick == N].index)
    invalid_teams = all_teams - valid_teams
    count_df = count_df[count_df.User.isin(valid_teams)]
    count_df = count_df.groupby("User").agg(
        {
            "Total Score": "sum",
            "Scores": lambda x: ", ".join(x),
        }
    )
    count_df.sort_values(["Total Score"], inplace=True, ascending=True)

    for user in invalid_teams:
        count_df.loc[user] = ["CUT", None]

    df.loc[df.Round != curr_round, "Total Score"] = "CUT"
    df["Scores"] = [
        "{} ({})".format(row["Player"], row["Total Score"])
        for idx, row in df.iterrows()
    ]

    score_df = pd.pivot_table(
        df,
        values=["Scores"],
        index=["User"],
        columns=["Pick"],
        fill_value="--",
        aggfunc="first",
    )
    count_df.index.names = [None]
    score_df.index.names = [None]

    return count_df, score_df
