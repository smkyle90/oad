from flask_table import Col, Table


# Declare your table
class UserTable(Table):
    name = Col("name")
    email = Col("email")


# Declare your table
class PickTable(Table):
    id = Col("id")
    event = Col("event")
    pick = Col("pick")
    name = Col("name")
