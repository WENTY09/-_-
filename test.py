import sys
print("Python version:", sys.version)
print("\nTrying to import Flask...")
try:
    from flask import Flask
    print("Flask imported successfully")
except ImportError as e:
    print("Error importing Flask:", e)

print("\nTrying to import SQLAlchemy...")
try:
    from flask_sqlalchemy import SQLAlchemy
    print("SQLAlchemy imported successfully")
except ImportError as e:
    print("Error importing SQLAlchemy:", e)

print("\nTrying to import dotenv...")
try:
    from dotenv import load_dotenv
    print("dotenv imported successfully")
except ImportError as e:
    print("Error importing dotenv:", e) 