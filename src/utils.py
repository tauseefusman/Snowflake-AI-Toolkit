import streamlit as st
from snowflake.snowpark import Session
from snowflake.snowpark.exceptions import SnowparkSQLException
from pathlib import Path
import json
import time
import base64
import os
import traceback

# Load the config file
config_path = Path("src/settings_config.json")
with open(config_path, "r") as f:
    config = json.load(f)

def render_image(filepath: str):
    """
    Renders an image in Streamlit from a filepath.
    filepath: path to the image. Must have a valid file extension.
    """
    mime_type = filepath.split('.')[-1:][0].lower()
    with open(filepath, "rb") as f:
        content_bytes = f.read()
        content_b64encoded = base64.b64encode(content_bytes).decode()
        image_string = f'data:image/{mime_type};base64,{content_b64encoded}'
        image_html = f"""
            <div style="text-align: center;">
                <img src="{image_string}" alt="App Logo" style="width: 150px; margin-bottom: 20px;">
            </div>
        """
        st.sidebar.markdown(image_html, unsafe_allow_html=True)


def list_databases(session):
    """List all databases."""
    return [row["name"] for row in session.sql("SHOW DATABASES").collect()]

def list_schemas(session, database: str):
    """List schemas in the specified database."""
    return [row["name"] for row in session.sql(f"SHOW SCHEMAS IN {database}").collect()]

def list_stages(session, database: str, schema: str):
    """List stages in the specified database and schema."""
    stages = [stage["name"] for stage in session.sql(f"SHOW STAGES IN {database}.{schema}").collect()]
    return stages

def list_files_in_stage(session, database: str, schema: str, stage: str):
    """List files in the specified stage."""
    stage_path = f"@{database}.{schema}.{stage}"
    files = [file["name"] for file in session.sql(f"LIST {stage_path}").collect()]
    return files

def list_file_details_in_stage(session, database, schema, stage_name):
    stage_path = f"@{database}.{schema}.{stage_name}"
    query = f"LIST {stage_path}"
    try:
        files = session.sql(query).collect()
        return [
            {
                "Filename": file["name"],
                "Size (Bytes)": file["size"],
                "Last Modified": file["last_modified"]
            }
            for file in files
        ]
    except Exception as e:
        st.error(f"Failed to list files in stage '{stage_name}': {e}")
        return []


def list_tables(session, database: str, schema: str):
    """List tables in the specified database and schema."""
    tables = [table["name"] for table in session.sql(f"SHOW TABLES IN {database}.{schema}").collect()]
    return tables

def list_columns(session, database: str, schema: str, table: str):
    """List columns in the specified table."""
    return [row["column_name"] for row in session.sql(f"SHOW COLUMNS IN {database}.{schema}.{table}").collect()]

def show_spinner(message: str):
    """Display a spinner with a custom message."""
    with st.spinner(message):
        yield

def validate_table_columns(session, database, schema, table, required_columns):
    try:
        # Query to get the column names in the specified table
        query = f"SHOW COLUMNS IN {database}.{schema}.{table}"
        columns = session.sql(query).collect()

        # Extract existing column names from the query result
        existing_columns = [column["column_name"].upper() for column in columns]

        # Check for missing columns
        missing_columns = [col for col in required_columns if col.upper() not in existing_columns]

        return missing_columns
    except Exception as e:
        raise RuntimeError(f"Failed to validate columns for table '{table}': {e}")


def create_prompt_for_rag(session, question: str, rag: bool, column: str, database: str, schema: str, table: str,embedding_type:str,embedding_model:str):
    """Create a prompt for RAG."""
    if rag and column:
        cmd = f"""
        WITH results AS (
            SELECT RELATIVE_PATH,
                   VECTOR_COSINE_SIMILARITY({column},
                   SNOWFLAKE.CORTEX.{embedding_type}('{embedding_model}', ?)) AS similarity,
                   chunk
            FROM {database}.{schema}.{table}
            ORDER BY similarity DESC
            LIMIT 3
        )
        SELECT chunk, relative_path FROM results;
        """
        question_rewrite = session.sql(cmd, [question]).collect()
        prompt = f"Context:\n{question_rewrite}\n\nQuestion: {question}\nAnswer:"
        return prompt
    else:
        prompt = f"Question: {question}\nAnswer:"
        return prompt

def get_cortex_complete_result(session, query: str):
    """Execute Cortex complete query and return the result."""
    return session.sql(query).collect()[0][0]

def list_existing_models(session):
    """List existing models."""
    query = "SHOW MODELS"  # Hypothetical query to show models
    return [model["name"] for model in session.sql(query).collect()]

def list_fine_tuned_models(session):
    """List fine-tuned models."""
    query = "SHOW FINE_TUNED_MODELS"  # Hypothetical query to show fine-tuned models
    return [model["name"] for model in session.sql(query).collect()]

def get_table_preview(session, database, schema, table):
    """Fetch a preview of the top 5 rows from the table."""
    query = f"SELECT * FROM {database}.{schema}.{table} LIMIT 5"
    df = session.sql(query).to_pandas()
    return df

def load_css(filepath):
    """Load custom CSS file."""
    with open(filepath) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def format_result(result_json):
    """Format the result from a Cortex query."""
    messages = result_json.get('choices', [{}])[0].get('messages', 'No messages found')
    model_used = result_json.get('model', 'No model specified')
    usage = result_json.get('usage', {})
    return {
        "messages": messages,
        "model_used": model_used,
        "usage": usage
    }

def write_result_to_output_table(session, output_table, output_column, result):
    """Writes the result to the specified output table and column."""
    insert_query = f"INSERT INTO {output_table} ({output_column}) VALUES (?)"
    session.sql(insert_query, [result]).collect()

def create_database_and_stage_if_not_exists(session: Session):
    """Creates the CORTEX_TOOLKIT database and MY_STAGE stage if they do not already exist."""

    # Fetch database and stage details from the config file
    database_name = config["snowflake"]["database"]
    stage_name = config["snowflake"]["stage"]

    # Check if the database exists, and create if it doesn't
    database_query = f"SHOW DATABASES LIKE '{database_name}'"
    existing_databases = session.sql(database_query).collect()

    if not existing_databases:
        session.sql(f"CREATE DATABASE IF NOT EXISTS {database_name}").collect()
    else:
        pass
        #print(f"Database '{database_name}' already exists. Skipping creation.")

    # Check if the stage exists, and create if it doesn't
    stage_query = f"SHOW STAGES LIKE '{stage_name}'"
    existing_stages = session.sql(stage_query).collect()

    if not existing_stages:
        session.sql(f"CREATE STAGE IF NOT EXISTS {database_name}.PUBLIC.{stage_name}").collect()
    else:
        pass
        #print(f"Stage '{stage_name}' already exists in '{database_name}'. Skipping creation.")

def create_stage(session, database, schema, stage_name):
    """Creates a stage in the specified database and schema."""
    query = f"CREATE STAGE IF NOT EXISTS {database}.{schema}.{stage_name}"
    try:
        session.sql(query).collect()
    except SnowparkSQLException as e:
        st.error(f"Failed to create stage: {e}")
        raise e


def upload_file_to_stage(session, database, schema, stage_name, file):
    """
    Uploads a file to the specified stage in Snowflake using the PUT command.

    Args:
        session: Snowflake session.
        database: Database name.
        schema: Schema name.
        stage_name: Stage name where the file will be uploaded.
        file: File object from Streamlit file uploader.
    """
    import tempfile
    import os

    # Construct stage path
    stage_path = f"@{database}.{schema}.{stage_name}"

    # Save the uploaded file temporarily
    temp_dir = tempfile.gettempdir()  # Use system temporary directory
    temp_file_path = os.path.join(temp_dir, file.name)
    temp_file_path = temp_file_path.replace("\\", "/")  # Ensure the path uses forward slashes for compatibility
    print("temp_file_path:", temp_file_path)

    try:
        with open(temp_file_path, "wb") as temp_file:
            temp_file.write(file.read())

        # Upload the file to the Snowflake stage
        put_query = f"PUT 'file://{temp_file_path}' {stage_path} AUTO_COMPRESS=FALSE"
        print("PUT Query:", put_query)  # For debugging
        session.sql(put_query).collect()

        st.success(f"File '{file.name}' uploaded successfully to stage '{stage_name}'.")
    except Exception as e:
        # Log the full traceback
        import traceback
        trace = traceback.format_exc()
        st.error(f"Failed to upload file: {e}")
        st.error(f"Traceback:\n{trace}")
        raise e
    finally:
        # Clean up the temporary file
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)


def show_toast_message(message, duration=3, toast_type="info"):
    """Displays a toast message in Streamlit using a temporary container."""
    # Define color styles based on the toast type
    toast_colors = {
        "info": "#007bff",
        "success": "#28a745",
        "warning": "#ffc107",
        "error": "#dc3545"
    }

    color = toast_colors.get(toast_type, "#007bff")  # Default to "info" color

    # Create a temporary container to display the toast
    toast_container = st.empty()

    # Use custom HTML and CSS to display a toast-like message
    toast_html = f"""
    <div style="
        position: fixed;
        top: 20px;
        right: 20px;
        background-color: {color};
        color: white;
        padding: 10px 20px;
        border-radius: 5px;
        box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.2);
        z-index: 10000;
        font-family: Arial, sans-serif;
    ">
        {message}
    </div>
    """

    # Display the toast message
    toast_container.markdown(toast_html, unsafe_allow_html=True)

    # Wait for the specified duration, then clear the container
    time.sleep(duration)
    toast_container.empty()

def setup_pdf_text_chunker(session):
    """Sets up the pdf_text_chunker UDF in the current database and schema."""
    # Check if UDF already exists
    try:
        udf_check_query = "SHOW USER FUNCTIONS LIKE 'pdf_text_chunker'"
        existing_udfs = session.sql(udf_check_query).collect()
        if existing_udfs:
            #st.info("UDF pdf_text_chunker already exists. Skipping creation.")
            return
    except Exception as e:
        st.error(f"Error checking UDF existence: {e}")
        return

    # Create UDF if it doesn't exist
    create_udf_query = """
    CREATE OR REPLACE FUNCTION pdf_text_chunker(file_url STRING)
    RETURNS TABLE (chunk VARCHAR)
    LANGUAGE PYTHON
    RUNTIME_VERSION = '3.9'
    HANDLER = 'pdf_text_chunker'
    PACKAGES = ('snowflake-snowpark-python', 'PyPDF2', 'langchain')
    AS
    $$
import PyPDF2
import io
import pandas as pd
from snowflake.snowpark.files import SnowflakeFile
from langchain.text_splitter import RecursiveCharacterTextSplitter

class pdf_text_chunker:
    def read_pdf(self, file_url: str) -> str:
        with SnowflakeFile.open(file_url, 'rb') as f:
            buffer = io.BytesIO(f.readall())
        reader = PyPDF2.PdfReader(buffer)
        text = ""
        for page in reader.pages:
            try:
                text += page.extract_text().replace('\\n', ' ').replace('\\0', ' ')
            except:
                text = "Unable to Extract"
        return text

    def process(self, file_url: str):
        text = self.read_pdf(file_url)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=400,
            length_function=len
        )
        chunks = text_splitter.split_text(text)
        df = pd.DataFrame(chunks, columns=['chunk'])
        yield from df.itertuples(index=False, name=None)
    $$
    """
    try:
        session.sql(create_udf_query).collect()
        #st.success("UDF pdf_text_chunker created successfully.")
    except Exception as e:
        st.error(f"Error creating UDF: {e}")


