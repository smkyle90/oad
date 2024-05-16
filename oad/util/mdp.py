import pandas as pd

from .helpers import get_live_scores

# Major DRAFT POOL
ALL_PICKS = [
    ("Brady", "Scottie Scheffler"),
    ("Sohale", "Rory McIlroy"),
    ("Lucas", "Xander Schauffele"),
    ("Scott", "Jon Rahm"),
    ("David", "Brooks Koepka"),
    ("Tom", "Bryson DeChambeau"),
    ("Brock", "Max Homa"),
    ("Jamil", "Collin Morikawa"),
    ("Jamil", "Ludvig Åberg"),
    ("Brock", "Viktor Hovland"),
    ("Tom", "Cameron Smith"),
    ("David", "Patrick Cantlay"),
    ("Scott", "Joaquín Niemann"),
    ("Lucas", "Wyndham Clark"),
    ("Sohale", "Will Zalatoris"),
    ("Brady", "Sahith Theegala"),
    ("Brady", "Tommy Fleetwood"),
    ("Sohale", "Byeong Hun An"),
    ("Lucas", "Cameron Young"),
    ("Scott", "Hideki Matsuyama"),
    ("David", "Justin Thomas"),
    ("Tom", "Talor Gooch"),
    ("Brock", "Tiger Woods"),
    ("Jamil", "Matt Fitzpatrick"),
    ("Jamil", "Tony Finau"),
    ("Brock", "Jordan Spieth"),
    ("Tom", "Tyrrell Hatton"),
    ("David", "Shane Lowry"),
    ("Scott", "Jason Day"),
    ("Lucas", "Si Woo Kim"),
    ("Sohale", "Min Woo Lee"),
    ("Brady", "Sam Burns"),
    ("Brady", "Sepp Straka"),
    ("Sohale", "Nicolai Højgaard"),
    ("Lucas", "Russell Henley"),
    ("Scott", "Taylor Pendrith"),
    ("David", "Denny McCarthy"),
    ("Tom", "Cam Davis"),
    ("Brock", "Rickie Fowler"),
    ("Jamil", "Dustin Johnson"),
    ("Jamil", "Corey Conners"),
    ("Brock", "Gary Woodland"),
    ("Tom", "Sungjae Im"),
    ("David", "Patrick Reed"),
    ("Scott", "Dean Burmester"),
    ("Lucas", "Akshay Bhatia"),
    ("Sohale", "Keith Mitchell"),
    ("Brady", "Keegan Bradley"),
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
