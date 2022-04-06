import pandas as pd

from .helpers import get_live_scores

# Major DRAFT POOL
ALL_PICKS = [
    ("Scott", "Jon Rahm"),
    ("Lucas", "Justin Thomas"),
    ("Tom", "Cameron Smith"),
    ("Sohale", "Scottie Scheffler"),
    ("David", "Dustin Johnson"),
    ("Jamil", "Viktor Hovland"),
    ("Brock", "Patrick Cantlay"),
    ("Brady", "Brooks Koepka"),
    ("Brady", "Jordan Spieth"),
    ("Brock", "Collin Morikawa"),
    ("Jamil", "Xander Schauffele"),
    ("David", "Rory McIlroy"),
    ("Sohale", "Will Zalatoris"),
    ("Tom", "Tiger Woods"),
    ("Lucas", "Daniel Berger"),
    ("Scott", "Shane Lowry"),
    ("Scott", "Corey Conners"),
    ("Lucas", "Hideki Matsuyama"),
    ("Tom", "Louis Oosthuizen"),
    ("Sohale", "Matt Fitzpatrick"),
    ("David", "Sam Burns"),
    ("Jamil", "Adam Scott"),
    ("Brock", "Paul Casey"),
    ("Brady", "Sungjae Im"),
    ("Brady", "Patrick Reed"),
    ("Brock", "Tyrrell Hatton"),
    ("Jamil", "Joaquin Niemann"),
    ("David", "Tony Finau"),
    ("Sohale", "Russell Henley"),
    ("Tom", "Tommy Fleetwood"),
    ("Lucas", "Webb Simpson"),
    ("Scott", "Marc Leishman"),
    ("Scott", "Billy Horschel"),
    ("Lucas", "Bryson DeChambeau"),
    ("Tom", "Max Homa"),
    ("Sohale", "Gary Woodland"),
    ("David", "Abraham Ancer"),
    ("Jamil", "Talor Gooch"),
    ("Brock", "Kevin Kisner"),
    ("Brady", "Matthew Wolff"),
    ("Brady", "Sergio Garcia"),
    ("Brock", "Francesco Molinari"),
    ("Jamil", "Justin Rose"),
    ("David", "Bubba Watson"),
    ("Sohale", "Seamus Power"),
    ("Tom", "Mackenzie Hughes"),
    ("Lucas", "Brian Harman"),
    ("Scott", "Jason Kokrak"),
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

    df["Pick"] = [i // 8 + 1 for i in range(len(df))]
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
        {"Total Score": "sum", "Scores": lambda x: ", ".join(x),}
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
