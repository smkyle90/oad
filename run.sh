
echo "Initialise the Flask DB."
python3 run_db.py

echo "Set flask paramteres"
export FLASK_APP=project
export FLASK_DEBUG=1
# Run the db
echo "Start the Flask DB."
flask run