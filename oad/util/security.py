# oad/util/security.py

from itsdangerous import URLSafeTimedSerializer

# from .. import create_app


ts = URLSafeTimedSerializer("1234")
