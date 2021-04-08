import pandas as pd

from .helpers import get_live_scores

# Major DRAFT POOL
ALL_PICKS = [
    ("Brock", "Dustin Johnson"),
    ("Lucas", "Jon Rahm"),
    ("Brady", "Justin Thomas"),
    ("Scott", "Jordan Spieth"),
    ("David", "Bryson DeChambeau"),
    ("Sohale", "Xander Schauffele"),
    ("Tom", "Rory McIlroy"),
    ("Jamil", "Brooks Koepka"),
    ("Jamil", "Patrick Reed"),
    ("Tom", "Cameron Smith"),
    ("Sohale", "Daniel Berger"),
    ("David", "Patrick Cantlay"),
    ("Scott", "Collin Morikawa"),
    ("Brady", "Matthew Fitzpatrick"),
    ("Lucas", "Webb Simpson"),
    ("Brock", "Viktor Hovland"),
    ("Brock", "Matthew Wolff"),
    ("Lucas", "Tony Finau"),
    ("Brady", "Sungjae Im"),
    ("Scott", "Joaquin Niemann"),
    ("David", "Scottie Scheffler"),
    ("Sohale", "Hideki Matsuyama"),
    ("Tom", "Sergio Garcia"),
    ("Jamil", "Lee Westwood"),
    ("Jamil", "Paul Casey"),
    ("Tom", "Tommy Fleetwood"),
    ("Sohale", "Tyrrell Hatton"),
    ("David", "Jason Day"),
    ("Scott", "Louis Oosthuizen"),
    ("Brady", "Will Zalatoris"),
    ("Lucas", "Adam Scott"),
    ("Brock", "Gary Woodland"),
    ("Brock", "Corey Conners"),
    ("Lucas", "Abraham Ancer"),
    ("Brady", "Si Woo Kim"),
    ("Scott", "Matt Kuchar"),
    ("David", "Max Homa"),
    ("Sohale", "Harris English"),
    ("Tom", "Shane Lowry"),
    ("Jamil", "Bubba Watson"),
    ("Jamil", "Billy Horschel"),
    ("Tom", "Marc Leishman"),
    ("Sohale", "Carlos Ortiz"),
    ("David", "Dylan Frittelli"),
    ("Scott", "Matt Wallace"),
    ("Brady", "Ryan Palmer"),
    ("Lucas", "Justin Rose"),
    ("Brock", "Mackenzie Hughes"),
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

    df["Pick"] = [i // 8 + 1 for i in range(len(df))]
    df["Total Score"] = [live_scores[player]["score"] for player in df.Player]
    df["Position"] = [live_scores[player]["position"] for player in df.Player]
    df["Scores"] = [
        "{} ({})".format(row["Player"], row["Total Score"])
        for idx, row in df.iterrows()
    ]

    count_df = df[df["Position"] != "--"]
    count_df.sort_values(["Total Score"], inplace=True, ascending=True)
    count_df = count_df.groupby("User").head(3)
    count_df = count_df.groupby("User").agg(
        {"Total Score": "sum", "Scores": lambda x: ", ".join(x),}
    )
    count_df.sort_values(["Total Score"], inplace=True, ascending=True)

    score_df = pd.pivot_table(
        df,
        values=["Scores"],
        index=["User"],
        columns=["Pick"],
        fill_value="--",
        aggfunc="first",
    )

    return count_df, score_df
