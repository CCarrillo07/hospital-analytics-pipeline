# Hospital Analytics Pipeline

This project implements an end-to-end data analytics pipeline for a hospital management dataset using Python, PostgreSQL, SQL, and Streamlit.

The goal is to simulate a real-world data pipeline where raw CSV files are ingested into a database, transformed into a clean harmonized layer, and delivered through analytics views and dashboards.

## Project Overview

The pipeline follows a layered data architecture:

```text
CSV files
   ↓
raw schema
   ↓
harmonized schema
   ↓
analytics schema
   ↓
Streamlit dashboard

The project includes:

- Raw data ingestion from CSV files
- PostgreSQL database schemas
- Ingestion logging
- Raw-to-harmonized data transformations
- Stored procedures
- Automated pipeline execution
- File watcher automation
- Jupyter notebooks for exploration and testing
- Streamlit dashboard for data delivery

## Tech Stack

- Python
- PostgreSQL
- SQLAlchemy
- pandas
- psycopg2
- python-dotenv
- schedule
- watchdog
- Streamlit
- Plotly
- Jupyter Notebook
- DBeaver
