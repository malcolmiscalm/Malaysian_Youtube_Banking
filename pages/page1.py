# pages/page1.py
import dash
from dash import html, dcc, Input, Output, State, dash_table
import dash_bootstrap_components as dbc
import os
import re
import traceback
import pandas as pd
import ast
from dotenv import load_dotenv

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint


# -------------------------------------------------------
# 1️⃣ Load environment and connect database
# -------------------------------------------------------
load_dotenv()

db = SQLDatabase.from_uri(
    "sqlite:///./Data/RDBMS/malaysian_youtube_banks_sentiment_deduplicated.db",
    sample_rows_in_table_info=0
)


# -------------------------------------------------------
# 2️⃣ Utility Functions
# -------------------------------------------------------
def get_schema(_=None):
    """Return database schema for the LLM to understand table structures."""
    return db.get_table_info()


def clean_sql_output(text: str) -> str:
    """Sanitize LLM SQL output by removing markdown and formatting artifacts."""
    cleaned = re.sub(r"```(sql)?", "", text, flags=re.IGNORECASE)
    cleaned = cleaned.replace("```", "")
    cleaned = cleaned.replace("SQL Query:", "")
    cleaned = cleaned.strip()
    if not cleaned.endswith(";"):
        cleaned += ";"
    return cleaned


def run_query(query: str):
    """Run a cleaned SQL query against the SQLite database."""
    query = clean_sql_output(query)
    print(f"\n🧩 Clean SQL being run:\n{query}\n")
    try:
        return db.run(query)
        # return pd.read_sql(query, db)
    except Exception as e:
        print(f"❌ Database execution error:\n{e}")
        raise


# -------------------------------------------------------
# 3️⃣ Model Selector
# -------------------------------------------------------
def get_llm(load_from_hugging_face=False):
    """Return the desired LLM interface (OpenAI or HuggingFace)."""
    if load_from_hugging_face:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENROUTER_API_KEY environment variable.")

        print(f"✅ Loaded API key: {api_key[:5]}... (length: {len(api_key)})")

        llm = HuggingFaceEndpoint(
            repo_id="Qwen/Qwen2.5-VL-7B-Instruct",
            task="text-generation",
            provider="hyperbolic",
            api_key=api_key,
        )
        return ChatHuggingFace(llm=llm)

    # Default: OpenAI GPT-4o
    return ChatOpenAI(model="gpt-4o", temperature=0.0)


# -------------------------------------------------------
# 4️⃣ SQL Query Generation Chain
# -------------------------------------------------------
def write_sql_query(llm):
    """Chain that converts a user question into a SQL query."""
    template = """Based on the table schema below, write a SQL query that would answer the user's question:
    {schema}

    Question: {question}
    SQL Query:"""

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Given an input question, convert it to a SQL query. "
         "Return only the SQL query — no markdown, no code fences, no explanations."),
        ("human", template),
    ])

    return (
        RunnablePassthrough.assign(schema=get_schema)
        | prompt
        | llm
        | StrOutputParser()
        | RunnableLambda(clean_sql_output)
    )


# -------------------------------------------------------
# 5️⃣ Full Response Chain (SQL + Natural Language)
# -------------------------------------------------------
def answer_user_query(question: str, llm):
    """Generate SQL, run it, and return both SQL + natural language answer."""
    try:
        # Step 1: Generate SQL from question
        sql_query = write_sql_query(llm).invoke({"question": question})
        cleaned_query = clean_sql_output(sql_query)

        # Step 2: Execute SQL
        sql_response = run_query(cleaned_query)

        # Step 3: Generate final natural-language answer
        template = """Based on the table schema below, question, SQL query, and SQL response,
        write a natural language answer.

        {schema}

        Question: {question}
        SQL Query: {query}
        SQL Response: {response}"""

        prompt_response = ChatPromptTemplate.from_messages([
            ("system", "You are an analytical assistant. Answer clearly and factually."),
            ("human", template),
        ])

        result = (
            prompt_response
            | llm
        ).invoke({
            "schema": get_schema(None),
            "question": question,
            "query": cleaned_query,
            "response": sql_response
        })

        answer_text = result.content if hasattr(result, "content") else str(result)

        return {
            "sql": cleaned_query,
            "answer": answer_text
        }

    except Exception as e:
        print(f"❌ Error during processing: {e}")
        return {
            "sql": "",
            "answer": f"❌ Error: {str(e)}"
        }


# -------------------------------------------------------
# 6️⃣ Test Run (Standalone Mode)
# -------------------------------------------------------
if __name__ == "__main__":
    llm = get_llm(load_from_hugging_face=False)
    query = "What is the most viewed video in MM_table?"
    result = answer_user_query(query, llm)
    print("\n🧠 SQL Generated:\n", result["sql"])
    print("\n💬 Final Answer:\n", result["answer"])


# -------------------------------------------------------
# 7️⃣ Dash Page Layout
# -------------------------------------------------------
dash.register_page(__name__, path="/", name="Query Assistant")

layout = dbc.Container([
    html.H2("🧩 LLM-SQL Query Assistant", className="text-center mt-4 mb-4"),
    dbc.Row([
        html.Img(src=dash.get_asset_url('./ERD/Slide1.jpeg'), alt='My Static Image', style={'width': '1000px'})
     ]),

    dbc.Row([
         dbc.RadioItems(
            id="query-mode",
            options=[
                {"label": "Use LLM to write SQL (Costs tokens)", "value": "llm"},
                {"label": "Write my own SQL (No tokens)", "value": "manual"},
            ],
            value="llm",
            inline=True,
            className="mb-3"
        )
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Textarea(
                id="user-question",
                placeholder="Ask a question about the YouTube Sentiment Database...",
                style={"height": "120px"},
            ),
            dbc.Button("Submit", id="submit-btn", color="primary", className="mt-3"),
        ], md=12),
    ]),

    html.Hr(),

    dbc.Spinner([
        html.Div(id="sql-query-output", className="mt-3"),
        html.Div(id="nl-answer-output", className="mt-4"),
        html.Div(id="error-output", className="text-danger mt-3"),
    ], color="primary"),
], fluid=True)


# -------------------------------------------------------
# 8️⃣ Dash Callback Logic
# -------------------------------------------------------
@dash.callback(
    Output("sql-query-output", "children"),
    Output("nl-answer-output", "children"),
    Output("error-output", "children"),
    Input("submit-btn", "n_clicks"),
    State("user-question", "value"),
    State("query-mode", "value"),
    prevent_initial_call=True
)
def process_question(n_clicks, user_question, mode):
    
    if not user_question:
        return "", "", "⚠️ Please enter a question."
    
    try:
       if mode == "manual":
        cleaned = clean_sql_output(user_question)

        try:
            df = pd.read_sql(cleaned, db._engine)
        except Exception as e:
            return "", "", f"❌ SQL Error: {str(e)}"

        sql_block = dbc.Card([
            dbc.CardHeader("📄 Executed SQL (User-provided)"),
            dbc.CardBody(html.Pre(cleaned))
        ])

        if df.empty:
            result_table = dbc.Alert("⚠️ Query returned no rows.", color="warning")
        else:
            result_table = dash_table.DataTable(
                id="table-sql-result",
                columns=[{"name": c, "id": c} for c in df.columns],
                data=df.to_dict("records"),
                filter_action="native",
                sort_action="native",
                page_size=20,
                style_table={'overflowX': 'auto'},
            )

        result_block = dbc.Card([
            dbc.CardHeader("📊 SQL Result (Formatted Table)"),
            dbc.CardBody(result_table)
        ])

        return sql_block, result_block, ""


        # ----------------------------------------------------
        # LLM MODE (your original logic)
        # ----------------------------------------------------
        llm = get_llm(load_from_hugging_face=False)
        response = answer_user_query(user_question, llm)

        sql_query = response.get("sql", "SQL query not detected.")
        nl_answer = response.get("answer", "")

        sql_block = dbc.Card([
            dbc.CardHeader("🧠 Generated SQL Query"),
            dbc.CardBody(html.Pre(sql_query))
        ])

        nl_answer_block = dbc.Card([
            dbc.CardHeader("💬 Answer"),
            dbc.CardBody(html.Div(nl_answer))
        ])

        return sql_block, nl_answer_block, ""

    except Exception as e:
        tb = traceback.format_exc(limit=2)
        return "", "", f"❌ Error: {str(e)}\n\n{tb}"

