import pandas as pd

from .helpers import get_live_scores

# Major DRAFT POOL
ALL_PICKS = [
    ("David", "Justin Thomas"),
    ("Lucas", "Jon Rahm"),
    ("Tom", "Scottie Scheffler"),
    ("Scott", "Collin Morikawa"),
    ("Sohale", "Xander Schauffele"),
    ("Jamil", "Jordan Spieth"),
    ("Brady", "Rory McIlroy"),
    ("Brock", "Patrick Cantlay"),
    ("Brock", "Cameron Smith"),
    ("Brady", "Hideki Matsuyama"),
    ("Jamil", "Dustin Johnson"),
    ("Sohale", "Viktor Hovland"),
    ("Scott", "Will Zalatoris"),
    ("Tom", "Brooks Koepka"),
    ("Lucas", "Sam Burns"),
    ("David", "Max Homa"),
    ("David", "Matt Fitzpatrick"),
    ("Lucas", "Tony Finau"),
    ("Tom", "Shane Lowry"),
    ("Scott", "Joaquin Niemann"),
    ("Sohale", "Louis Oosthuizen"),
    ("Jamil", "Corey Conners"),
    ("Brady", "Tyrrell Hatton"),
    ("Brock", "Tiger Woods"),
    ("Brock", "Daniel Berger"),
    ("Brady", "Jason Day"),
    ("Jamil", "Keegan Bradley"),
    ("Sohale", "Cameron Young"),
    ("Scott", "Abraham Ancer"),
    ("Tom", "Billy Horschel"),
    ("Lucas", "Alex Noren"),
    ("David", "Adam Scott"),
    ("David", "Patrick Reed"),
    ("Lucas", "Sebastián Muñoz"),
    ("Tom", "Marc Leishman"),
    ("Scott", "Cameron Champ"),
    ("Sohale", "Mito Pereira"),
    ("Jamil", "Talor Gooch"),
    ("Brady", "Jason Kokrak"),
    ("Brock", "Tommy Fleetwood"),
    ("Brock", "Russell Henley"),
    ("Brady", "Gary Woodland"),
    ("Jamil", "Aaron Wise"),
    ("Sohale", "Seamus Power"),
    ("Scott", "Russell Knox"),
    ("Tom", "Harold Varner III"),
    ("Lucas", "Kevin Na"),
    ("David", "Matt Kuchar"),
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
    print(live_scores)
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
