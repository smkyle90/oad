import pandas as pd

from .helpers import get_live_scores

# Major DRAFT POOL
ALL_PICKS = [
    ("Tom", "Jon Rahm"),
    ("David", "Rory McIlroy"),
    ("Brock", "Xander Schauffele"),
    ("Jamil", "Brooks Koepka"),
    ("Brady", "Jordan Spieth"),
    ("Sohale", "Louis Oosthuizen"),
    ("Lucas", "Justin Thomas"),
    ("Scott", "Dustin Johnson"),
    ("Scott", "Bryson DeChambeau"),
    ("Lucas", "Patrick Cantlay"),
    ("Sohale", "Collin Morikawa"),
    ("Brady", "Scottie Scheffler"),
    ("Jamil", "Viktor Hovland"),
    ("Brock", "Tyrrell Hatton"),
    ("David", "Patrick Reed"),
    ("Tom", "Paul Casey"),
    ("Tom", "Matt Fitzpatrick"),
    ("David", "Tony Finau"),
    ("Brock", "Rickie Fowler"),
    ("Jamil", "Tommy Fleetwood"),
    ("Brady", "Webb Simpson"),
    ("Sohale", "Daniel Berger"),
    ("Lucas", "Cameron Smith"),
    ("Scott", "Shane Lowry"),
    ("Scott", "Justin Rose"),
    ("Lucas", "Will Zalatoris"),
    ("Sohale", "Corey Conners"),
    ("Brady", "Harris English"),
    ("Jamil", "Marc Leishman"),
    ("Brock", "Jason Day"),
    ("David", "Lee Westwood"),
    ("Tom", "Ian Poulter"),
    ("Tom", "Phil Mickelson"),
    ("David", "Sergio Garcia"),
    ("Brock", "Charley Hoffman"),
    ("Jamil", "Branden Grace"),
    ("Brady", "Jason Kokrak"),
    ("Sohale", "Joaquin Niemann"),
    ("Lucas", "Adam Scott"),
    ("Scott", "Francesco Molinari"),
    ("Scott", "Matt Wallace"),
    ("Lucas", "Robert MacIntyre"),
    ("Sohale", "Russell Henley"),
    ("Brady", "Sam Burns"),
    ("Jamil", "Abraham Ancer"),
    ("Brock", "Min Woo Lee"),
    ("David", "Christiaan Bezuidenhout"),
    ("Tom", "Thomas Detry"),
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
