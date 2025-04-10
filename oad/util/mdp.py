import pandas as pd

from .helpers import get_live_scores

# Major DRAFT POOL
ALL_PICKS = [
    ("David", "Scottie Scheffler"),
    ("Brady", "Rory McIlroy"),
    ("Brock", "Collin Morikawa"),
    ("Lucas", "Bryson DeChambeau"),
    ("Tom ", "Joaquín Niemann"),
    ("Scott", "Xander Schauffele"),
    ("Sohale", "Ludvig Åberg"),
    ("Jamil", "Jon Rahm"),
    ("Jamil", "Brooks Koepka"),
    ("Sohale", "Viktor Hovland"),
    ("Scott", "Hideki Matsuyama"),
    ("Tom ", "Justin Thomas"),
    ("Lucas", "Tommy Fleetwood"),
    ("Brock", "Patrick Cantlay"),
    ("Brady", "Shane Lowry"),
    ("David", "Cameron Smith"),
    ("David", "Wyndham Clark"),
    ("Brady", "Will Zalatoris"),
    ("Brock", "Corey Conners"),
    ("Lucas", "Russell Henley"),
    ("Tom ", "Min Woo Lee"),
    ("Scott", "Robert MacIntyre"),
    ("Sohale", "Sepp Straka"),
    ("Jamil", "Tyrrell Hatton"),
    ("Jamil", "Akshay Bhatia"),
    ("Sohale", "J.J. Spaun"),
    ("Scott", "Jason Day"),
    ("Tom ", "Tony Finau"),
    ("Lucas", "Jordan Spieth"),
    ("Brock", "Max Homa"),
    ("Brady", "Justin Rose"),
    ("David", "Keegan Bradley"),
    ("David", "Patrick Reed"),
    ("Brady", "Maverick McNealy"),
    ("Brock", "Taylor Pendrith"),
    ("Lucas", "Sergio Garcia"),
    ("Tom ", "Aaron Rai"),
    ("Scott", "Dustin Johnson"),
    ("Sohale", "Nicolai Højgaard"),
    ("Jamil", "Brian Harman"),
    ("Jamil", "Stephan Jaeger"),
    ("Sohale", "Nicolas Echavarria"),
    ("Scott", "Sahith Theegala"),
    ("Tom ", "Tom Kim"),
    ("Lucas", "Sungjae Im"),
    ("Brock", "Nick Taylor"),
    ("Brady", "Michael Kim"),
    ("David", "Adam Scott"),
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
