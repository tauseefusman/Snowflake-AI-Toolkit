from snowflake.snowpark.exceptions import SnowparkSQLException
import json
import streamlit as st


def escape_sql_string(s):
    """Helper function to escape single quotes in SQL strings."""
    return s.replace("'", "''")


def check_and_create_table(session, db, schema, table, columns):
    """
    Check if the table exists and if it does, truncate it.
    If the table does not exist, create it with the specified columns.

    Args:
        session: Snowflake session.
        db: Database name.
        schema: Schema name.
        table: Table name.
        columns: List of column definitions (e.g., ["col1 STRING", "col2 NUMBER"]).
    """
    full_table_name = f"{db}.{schema}.{table}"

    # Check if the table exists
    table_exists_query = f"SHOW TABLES IN SCHEMA {db}.{schema}"
    tables = session.sql(table_exists_query).collect()

    table_exists = any(t["name"] == table.upper() for t in tables)

    if table_exists:
        truncate_query = f"DROP TABLE {full_table_name}"
        session.sql(truncate_query).collect()
        print(f"Table {full_table_name} dropped successfully.")     


    # Create the table if it doesn't exist
    columns_definition = ", ".join(columns)
    create_table_query = f"CREATE TABLE {full_table_name} ({columns_definition})"
    session.sql(create_table_query).collect()
    print(f"Table {full_table_name} created successfully.")
    return



def get_complete_result(session, model, prompt, temperature, max_tokens, guardrails, system_prompt=None):
    """Handles the Complete functionality in playground mode."""
    messages = []
    if system_prompt:
        messages.append({'role': 'system', 'content': system_prompt})
    messages.append({'role': 'user', 'content': prompt})

    messages_json = escape_sql_string(json.dumps(messages))

    query = f"""
    SELECT SNOWFLAKE.CORTEX.COMPLETE(
        '{model}',
        PARSE_JSON('{messages_json}'),
        {{
            'temperature': {temperature},
            'max_tokens': {max_tokens},
            'guardrails': {str(guardrails).lower()}
        }}
    );
    """
    try:
        result = session.sql(query).collect()[0][0]
        return json.loads(result)
    except SnowparkSQLException as e:
        raise e


def get_complete_result_from_column(session, model, db, schema, table, input_column, temperature, max_tokens, guardrails, output_table, output_column, system_prompt=None, user_prompt=None):
    """Fetches content from a column and writes the completion result to an output table."""
    
    # Check if the output table and column exist, and create/add the column if necessary
    columns = [
        f"{input_column} VARCHAR(16777216)",
        f"{output_column} VARCHAR(16777216)"
    ]
    # Ensure output table exists
    check_and_create_table(session, db, schema, output_table, columns)

    # Build full table names
    source_table_full = f"{db}.{schema}.{table}"
    output_table_full = f"{db}.{schema}.{output_table}"

    # Escape system prompt
    system_prompt_escaped = escape_sql_string(system_prompt) if system_prompt else ""
    user_prompt_escaped = escape_sql_string(user_prompt) if user_prompt else ""

    # Prepare user prompt by escaping special characters
    user_prompt_sql = f"'{user_prompt_escaped} <{table}>' || {input_column} || '</{table}>'"

    # Construct the SQL query without using PARSE_JSON incorrectly
    query = f"""
    INSERT INTO {output_table_full} ({input_column}, {output_column})
    SELECT {input_column},
        GET_PATH(
            SNOWFLAKE.CORTEX.COMPLETE(
                '{model}',
                ARRAY_CONSTRUCT(
                    OBJECT_CONSTRUCT('role', 'system', 'content', '{system_prompt_escaped}'),
                    OBJECT_CONSTRUCT('role', 'user', 'content', {user_prompt_sql})
                ),
                OBJECT_CONSTRUCT(
                    'temperature', {temperature},
                    'max_tokens', {max_tokens},
                    'guardrails', {str(guardrails).lower()}
                )
            ),
            'choices[0].messages'
        ) AS message_content
    FROM {source_table_full};
    """

    try:
        session.sql(query).collect()
    except SnowparkSQLException as e:
        raise e



# Translation function for playground mode using SQL
def get_translation(session, text, source_lang, target_lang):
    """Handles the Translate functionality in playground mode using SQL."""
    query = f"""
    SELECT SNOWFLAKE.CORTEX.TRANSLATE('{escape_sql_string(text)}', '{source_lang}', '{target_lang}');
    """
    try:
        result = session.sql(query).collect()[0][0]
        return result
    except SnowparkSQLException as e:
        raise e


# Summary function for playground mode using SQL
def get_summary(session, text):
    """Handles the Summarize functionality in playground mode using SQL."""
    query = f"""
    SELECT SNOWFLAKE.CORTEX.SUMMARIZE('{escape_sql_string(text)}');
    """
    try:
        result = session.sql(query).collect()[0][0]
        return result
    except SnowparkSQLException as e:
        raise e


# Extraction function for playground mode using SQL
def get_extraction(session, text, query_text):
    """Handles the Extract functionality in playground mode using SQL."""
    query_text_escaped = escape_sql_string(query_text)
    query = f"""
    SELECT SNOWFLAKE.CORTEX.EXTRACT_ANSWER('{escape_sql_string(text)}', '{query_text_escaped}');
    """
    try:
        result = session.sql(query).collect()[0][0]
        return result
    except SnowparkSQLException as e:
        raise e


# Sentiment function for playground mode using SQL
def get_sentiment(session, text):
    """Handles the Sentiment functionality in playground mode using SQL."""
    query = f"""
    SELECT SNOWFLAKE.CORTEX.SENTIMENT('{escape_sql_string(text)}');
    """
    try:
        result = session.sql(query).collect()[0][0]
        return result
    except SnowparkSQLException as e:
        raise e


def get_translation_from_column(session, db, schema, table, input_column, source_lang, target_lang, output_table, output_column):
    """Fetches content from a column and writes the translation result to an output table."""
    columns = [
        f"{input_column} VARCHAR(16777216)",
        f"{output_column} VARCHAR(16777216)"
    ]
    # Ensure output table exists
    check_and_create_table(session, db, schema, output_table, columns)

    source_table_full = f"{db}.{schema}.{table}"
    output_table_full = f"{db}.{schema}.{output_table}"

    query = f"""
    INSERT INTO {output_table_full} ({output_column})
    SELECT CAST(SNOWFLAKE.CORTEX.TRANSLATE({input_column}, '{source_lang}', '{target_lang}') AS STRING)
    FROM {source_table_full};
    """
    try:
        session.sql(query).collect()
    except SnowparkSQLException as e:
        raise e


def get_summary_from_column(session, db, schema, table, input_column, output_table, output_column):
    """Fetches content from a column and writes the summary result to an output table."""
    columns = [
        f"{input_column} VARCHAR(16777216)",
        f"{output_column} VARCHAR(16777216)"
    ]
    # Ensure output table exists
    check_and_create_table(session, db, schema, output_table, columns)

    source_table_full = f"{db}.{schema}.{table}"
    output_table_full = f"{db}.{schema}.{output_table}"

    query = f"""
    INSERT INTO {output_table_full} ({output_column})
    SELECT CAST(SNOWFLAKE.CORTEX.SUMMARIZE({input_column}) AS STRING)
    FROM {source_table_full};
    """
    try:
        session.sql(query).collect()
    except SnowparkSQLException as e:
        raise e


def get_extraction_from_column(session, db, schema, table, input_column, query_text, output_table, output_column):
    """Fetches content from a column and writes the extracted answer to an output table."""
    columns = [
        f"{input_column} VARCHAR(16777216)",
        f"{output_column} VARCHAR(16777216)"
    ]
    # Ensure output table exists
    check_and_create_table(session, db, schema, output_table, columns)

    source_table_full = f"{db}.{schema}.{table}"
    output_table_full = f"{db}.{schema}.{output_table}"

    query_text_escaped = escape_sql_string(query_text)

    query = f"""
    INSERT INTO {output_table_full} ({output_column})
    SELECT CAST(SNOWFLAKE.CORTEX.EXTRACT_ANSWER({input_column}, '{query_text_escaped}') AS STRING)
    FROM {source_table_full};
    """
    try:
        session.sql(query).collect()
    except SnowparkSQLException as e:
        raise e


def get_sentiment_from_column(session, db, schema, table, input_column, output_table, output_column):
    """Fetches content from a column and writes the sentiment analysis result to an output table."""
    columns = [
        f"{input_column} VARCHAR(16777216)",
        f"{output_column} VARCHAR(16777216)"
    ]
    # Ensure output table exists
    check_and_create_table(session, db, schema, output_table, columns)

    source_table_full = f"{db}.{schema}.{table}"
    output_table_full = f"{db}.{schema}.{output_table}"

    query = f"""
    INSERT INTO {output_table_full} ({output_column})
    SELECT CAST(SNOWFLAKE.CORTEX.SENTIMENT({input_column}) AS STRING)
    FROM {source_table_full};
    """
    try:
        session.sql(query).collect()
    except SnowparkSQLException as e:
        raise e

    
def create_vector_embedding_from_stage(session, db, schema, stage, embedding_type, embedding_model,output_table):
    """Creates vector embeddings for all files in a selected stage."""
    stage_path = f"@{db}.{schema}.{stage}"
    output_table_full = f"{db}.{schema}.{output_table}"

    # Define the columns required in the output table
    columns = [
        "relative_path VARCHAR(16777216)","size NUMBER(38,0)","file_url VARCHAR(16777216)",
        "scoped_file_url VARCHAR(16777216)", "chunk VARCHAR(16777216)"
    ]
    if embedding_model == "EMBED_TEXT_768":
        columns.append("vector_embeddings VECTOR(FLOAT, 768)")
    else:
        columns.append("vector_embeddings VECTOR(FLOAT, 1024)")
    # Ensure the output table exists with the required columns
    check_and_create_table(session, db, schema, output_table, columns)

    # Construct the SQL query to process all files in the stage
    query = f"""
    INSERT INTO {output_table_full} (relative_path, size, file_url, scoped_file_url, chunk, vector_embeddings)
    SELECT 
        relative_path, 
        size,
        file_url,
        build_scoped_file_url('{stage_path}', relative_path) AS scoped_file_url,
        func.chunk AS chunk,
        SNOWFLAKE.CORTEX.{embedding_type}('{embedding_model}', func.chunk) AS vector_embeddings
    FROM 
        directory('{stage_path}') AS dir,
        TABLE(pdf_text_chunker(build_scoped_file_url('{stage_path}', relative_path))) AS func;
    """
    try:
        session.sql(query).collect()
        st.success(f"Vector embeddings created successfully for all files in {stage}. Results saved to {output_table}.")
    except SnowparkSQLException as e:
        st.error(f"Failed to create embeddings: {e}")
        raise e





