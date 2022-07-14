import pandas as pd

from .helpers import get_live_scores

# Major DRAFT POOL
ALL_PICKS = [
    ("David", "Rory McIlroy"),
    ("Scott", "Xander Schauffele"),
    ("Tom", "Matt Fitzpatrick"),
    ("Lucas", "Scottie Scheffler"),
    ("Brady", "Jon Rahm"),
    ("Brock", "Justin Thomas"),
    ("Jamil", "Shane Lowry"),
    ("Sohale", "Patrick Cantlay"),
    ("Sohale", "Tommy Fleetwood"),
    ("Jamil", "Collin Morikawa"),
    ("Brock", "Tiger Woods"),
    ("Brady", "Will Zalatoris"),
    ("Lucas", "Jordan Spieth"),
    ("Tom", "Hideki Matsuyama"),
    ("Scott", "Max Homa"),
    ("David", "Cameron Smith"),
    ("David", "Tyrrell Hatton"),
    ("Scott", "Dustin Johnson"),
    ("Tom", "Joaquin Niemann"),
    ("Lucas", "Sam Burns"),
    ("Brady", "Tony Finau"),
    ("Brock", "Louis Oosthuizen"),
    ("Jamil", "Viktor Hovland"),
    ("Sohale", "Seamus Power"),
    ("Sohale", "Ryan Fox"),
    ("Jamil", "Brooks Koepka"),
    ("Brock", "Keith Mitchell"),
    ("Brady", "Corey Conners"),
    ("Lucas", "Sungjae Im"),
    ("Tom", "Gary Woodland"),
    ("Scott", "Adam Scott"),
    ("David", "Marc Leishman"),
    ("David", "Patrick Reed"),
    ("Scott", "Robert MacIntyre"),
    ("Tom", "Brian Harman    "),
    ("Lucas", "Talor Gooch"),
    ("Brady", "Cameron Tringale"),
    ("Brock", "Abraham Ancer"),
    ("Jamil", "Christiaan Bezuidenhout"),
    ("Sohale", "Thomas Pieters"),
    ("Sohale", "Jordan Smith"),
    ("Jamil", "Danny Willett"),
    ("Brock", "Cameron Young"),
    ("Brady", "Paul Casey"),
    ("Lucas", "Bryson DeChambeau"),
    ("Tom", "Kurt Kitayama"),
    ("Scott", "Min Woo Lee"),
    ("David", "Billy Horschel"),
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
