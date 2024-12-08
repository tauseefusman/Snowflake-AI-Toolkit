import streamlit as st
from src.utils import *
from snowflake.snowpark.exceptions import SnowparkSQLException
import json
import pandas as pd
from src.notification import *

config_path = Path("src/settings_config.json")
with open(config_path, "r") as f:
    config = json.load(f)




def format_and_display_result(result, question):
    """Formats and displays the result in a consistent manner."""
    try:
        # Parse the result JSON
        result_json = json.loads(result)
        print(result_json)
        messages = result_json.get("choices", [{}])[0].get("messages", "No messages found")
        model_used = result_json.get("model", "No model specified")
        usage = result_json.get("usage", {})

        # Display the formatted output
        st.write("Completion Result")
        st.write(f"**Model Used:** {model_used}")
        st.write(f"**Question Asked:** {question}")
        st.write("**Usage:**")
        st.write(f"  - Completion Tokens: {usage.get('completion_tokens', 'N/A')}")
        st.write(f"  - Prompt Tokens: {usage.get('prompt_tokens', 'N/A')}")
        st.write(f"  - Total Tokens: {usage.get('total_tokens', 'N/A')}")
        st.success(messages)
    except Exception as e:
        st.error(f"Failed to format and display result: {e}")
        raise e


def execute_query_and_get_result(session, prompt, model, functionality):
    """Executes a query and retrieves the result with error handling."""
    try:
        query = f"""
        SELECT SNOWFLAKE.CORTEX.COMPLETE(
            '{model}',
            [
                {{
                    'role': 'user',
                    'content': '{prompt}'
                }}
            ],
            {{
				'temperature': '{config["default_settings"]["temperature"]}',
				'max_tokens': '{config["default_settings"]["max_tokens"]}'
            }}
        );
        """
        result = session.sql(query).collect()
        return result[0][0] if result else None
    except Exception as e:
        # Log the error in the logs table
        add_log_entry(session, functionality, str(e))
        # Raise the exception to be handled by the calling function
        raise e
    


def execute_fine_tune_query(session, db, schema, train_table, validation_table, base_model, new_model_name):
    """Executes the fine-tune query and returns the tracking ID."""
    query = f"""
    SELECT SNOWFLAKE.CORTEX.FINETUNE(
        'CREATE',
        '{new_model_name}',
        '{base_model}',
        'SELECT PROMPT, COMPLETION FROM {db}.{schema}.{train_table}',
        'SELECT PROMPT, COMPLETION FROM {db}.{schema}.{validation_table}'
    )
    """
    try:
        result = session.sql(query).collect()
        return result[0][0] if result else None
    except Exception as e:
        raise RuntimeError(f"Failed to execute fine-tune query: {e}")


def execute_fine_tune_status_query(session, tracking_id):
    """Fetches the fine-tune status for the given tracking ID."""
    query = f"""
    SELECT SNOWFLAKE.CORTEX.FINETUNE(
        'DESCRIBE',
        '{tracking_id}'
    )
    """
    try:
        result = session.sql(query).collect()
        return result[0][0] if result else None
    except Exception as e:
        raise RuntimeError(f"Failed to fetch fine-tune status: {e}")


def fetch_fine_tuned_models(session):
    """Fetches the list of fine-tuned models."""
    query = "SHOW MODELS"
    try:
        models = session.sql(query).collect()
        fine_tuned_models = [
            model["name"]
            for model in models
            if "CORTEX_FINETUNED" in model["model_type"]
        ]
        return fine_tuned_models
    except Exception as e:
        raise RuntimeError(f"Failed to fetch fine-tuned models: {e}")


def execute_fine_tune_status_query(session, tracking_id):
    query = f"""
    SELECT SNOWFLAKE.CORTEX.FINETUNE(
        'DESCRIBE',
        '{tracking_id}'
    )
    """
    try:
        result = session.sql(query).collect()
        return result[0][0] if result else None
    except Exception as e:
        raise RuntimeError(f"Failed to fetch fine-tune status for Tracking ID {tracking_id}: {e}")

def format_fine_tune_status_result(status_json):
    try:
        status_data = json.loads(status_json)

        # Prepare table-friendly data
        table_data = {
            "Base Model": [status_data.get("base_model", "N/A")],
            "Created On": [status_data.get("created_on", "N/A")],
            "Finished On": [status_data.get("finished_on", "N/A")],
            "Model": [status_data.get("model", "N/A")],
            "Progress": [f"{status_data.get('progress', 0) * 100:.2f}%"],
            "Status": [status_data.get("status", "N/A")],
            "Training Data": [status_data.get("training_data", "N/A")],
            "Validation Data": [status_data.get("validation_data", "N/A")],
            "Trained Tokens": [status_data.get("trained_tokens", "N/A")],
            "Validation Loss": [status_data.get("training_result", {}).get("validation_loss", "N/A")],
            "Training Loss": [status_data.get("training_result", {}).get("training_loss", "N/A")],
        }

        return pd.DataFrame(table_data)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse the fine-tune status JSON: {e}")

