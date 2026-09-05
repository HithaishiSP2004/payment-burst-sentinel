"""
Payment Burst Sentinel — Configuration
=======================================
Project-wide constants and configuration values.
All thresholds, paths, and structural decisions live here.

Phase 1: Data loading constants only.
Detection thresholds will be added in later phases.
"""

import os
from pathlib import Path

# ─────────────────────────────────────────────────────────────
# Project Paths
# ─────────────────────────────────────────────────────────────

# Root of the project (parent of backend/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"

# Raw CSV files
TRAIN_CSV = RAW_DATA_DIR / "fraudTrain.csv"
TEST_CSV = RAW_DATA_DIR / "fraudTest.csv"

# Design reference directory
DESIGN_REF_DIR = PROJECT_ROOT / "design_reference"

# ─────────────────────────────────────────────────────────────
# Dataset Schema — from Phase 0 audit
# ─────────────────────────────────────────────────────────────

# Original CSV column names (index column = unnamed first column)
COLUMN_INDEX = ""  # Unnamed index column in CSV
COLUMN_TIMESTAMP = "trans_date_trans_time"
COLUMN_CC_NUM = "cc_num"
COLUMN_MERCHANT = "merchant"
COLUMN_CATEGORY = "category"
COLUMN_AMOUNT = "amt"
COLUMN_FIRST_NAME = "first"
COLUMN_LAST_NAME = "last"
COLUMN_GENDER = "gender"
COLUMN_STREET = "street"
COLUMN_CITY = "city"
COLUMN_STATE = "state"
COLUMN_ZIP = "zip"
COLUMN_LAT = "lat"
COLUMN_LONG = "long"
COLUMN_CITY_POP = "city_pop"
COLUMN_JOB = "job"
COLUMN_DOB = "dob"
COLUMN_TRANS_NUM = "trans_num"
COLUMN_UNIX_TIME = "unix_time"
COLUMN_MERCH_LAT = "merch_lat"
COLUMN_MERCH_LONG = "merch_long"
COLUMN_IS_FRAUD = "is_fraud"

# ─────────────────────────────────────────────────────────────
# Columns relevant to burst detection (Phase 0 finding)
# ─────────────────────────────────────────────────────────────

# Critical columns — required for core detection
CRITICAL_COLUMNS = [
    COLUMN_TIMESTAMP,
    COLUMN_UNIX_TIME,
    COLUMN_MERCHANT,
    COLUMN_AMOUNT,
    COLUMN_IS_FRAUD,
]

# High-value columns — used for behavioral signals
BEHAVIORAL_COLUMNS = [
    COLUMN_CATEGORY,
    COLUMN_CC_NUM,
]

# Contextual columns — may support secondary analysis
CONTEXTUAL_COLUMNS = [
    COLUMN_LAT,
    COLUMN_LONG,
    COLUMN_STATE,
    COLUMN_MERCH_LAT,
    COLUMN_MERCH_LONG,
]

# Columns NOT used — PII or irrelevant to burst detection
EXCLUDED_COLUMNS = [
    COLUMN_INDEX,
    COLUMN_FIRST_NAME,
    COLUMN_LAST_NAME,
    COLUMN_GENDER,
    COLUMN_STREET,
    COLUMN_CITY,
    COLUMN_ZIP,
    COLUMN_CITY_POP,
    COLUMN_JOB,
    COLUMN_DOB,
    COLUMN_TRANS_NUM,
]

# All columns to retain after cleaning
RETAINED_COLUMNS = CRITICAL_COLUMNS + BEHAVIORAL_COLUMNS + CONTEXTUAL_COLUMNS

# ─────────────────────────────────────────────────────────────
# Data Cleaning
# ─────────────────────────────────────────────────────────────

# Merchant names in the dataset are prefixed with "fraud_"
# This is a synthetic dataset artifact, not meaningful for analysis
MERCHANT_NAME_PREFIX = "fraud_"

# Timestamp format in the CSV
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"
