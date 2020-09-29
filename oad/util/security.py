# oad/util/security.py

from itsdangerous import URLSafeTimedSerializer

ts = URLSafeTimedSerializer("1234")
