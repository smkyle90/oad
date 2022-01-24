import pandas as pd

POINTS_DF = pd.read_csv("points.csv")
RESULTS_DF = pd.read_csv("sony.csv")

RESULTS_DF["pos"] = RESULTS_DF.pts.rank(axis=0, method="min", ascending=False).astype(
    int
)

EVENT_TYPE = "regular"


live_scores = {}

# pot_earns = []


for row in RESULTS_DF.itertuples():
    # print(row)

    live_scores[row.name] = {
        "position": row.pos,
        "freq": RESULTS_DF.groupby("pos").count().name.loc[row.pos],
    }

pot_earns = []
for pick in live_scores:
    pot_earns.append(
        # round(
        POINTS_DF[EVENT_TYPE]
        .loc[
            (live_scores[pick]["position"] - 1) : (live_scores[pick]["position"] - 1)
            + (live_scores[pick]["freq"] - 1)
        ]
        .sum()
        / (live_scores[pick]["freq"]),
        # 0,
        # )
    )

RESULTS_DF["calc"] = pot_earns

print(RESULTS_DF.pts - RESULTS_DF.calc)
