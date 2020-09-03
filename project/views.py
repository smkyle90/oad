from flask_table import Col, Table


# Declare your table
class UserTable(Table):
    name = Col("name")
    strikes_remaining = Col("strikes_remaining")


# Declare your table
class PickTable(Table):
    event = Col("event")
    pick = Col("pick")
    name = Col("name")

# Declare your table
class PlayerTable(Table):
    name = Col("name")
    cumulative_points = Col("cumulative_points")

class UserPickTable(Table):
    event = Col("event")
    pick = Col("pick")
    points = Col("points")
