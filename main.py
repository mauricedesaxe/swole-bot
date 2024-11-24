import sys
from scrape import download_urls
from ai_stuff import setup, chat_session
from dotenv import load_dotenv
from fasthtml.common import *
import markdown
import datetime
import sqlite3
import json
import uuid

load_dotenv()

app, rt = fast_app(
    hdrs=(
        picolink,
        MarkdownJS(),
        HighlightJS(langs=['python', 'javascript']),
        Style("""
            textarea { min-height: 100px; }
            .source { font-size: 0.9em; color: #666; }
            #chat_response { margin-top: 2em; }
            .loading { opacity: 0.5; }
        """),
        Script("""
            htmx.on('htmx:beforeRequest', function(evt) {
                evt.detail.target.classList.add('loading');
            });
            htmx.on('htmx:afterRequest', function(evt) {
                evt.detail.target.classList.remove('loading');
            });
        """)
    )
)

# Home page
@rt("/")
def get():
    return Titled("Swole Bot 💪🏻", 
        Container(
            P("Your AI assistant for getting swole! Ask questions about sports, weightlifting, and testosterone."),
            Form(
                Textarea(id="user_input", placeholder="Ask me anything about getting swole...", required=True),
                Button("Send", type="submit"),
                hx_post="/chat",
                hx_target="#chat_response"
            ),
            Div(id="chat_response")
        )
    )

def init_chat_db():
    # Create db directory if it doesn't exist
    os.makedirs('db', exist_ok=True)
    
    db = sqlite3.connect('db/chat.db')
    cursor = db.cursor()
    
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            messages JSON,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.commit()
    return db

def save_chat_history(session_id: str, messages: list):
    db = init_chat_db()
    cursor = db.cursor()
    
    # Try to update existing session first
    cursor.execute(
        """
        UPDATE chats 
        SET messages = ?, 
            updated_at = CURRENT_TIMESTAMP 
        WHERE session_id = ? 
        AND id = (
            SELECT id FROM chats 
            WHERE session_id = ? 
            ORDER BY created_at DESC 
            LIMIT 1
        )
        """,
        (json.dumps(messages), session_id, session_id)
    )
    
    # If no existing session was updated, insert new one
    if cursor.rowcount == 0:
        cursor.execute(
            "INSERT INTO chats (session_id, messages) VALUES (?, ?)",
            (session_id, json.dumps(messages))
        )
    
    db.commit()
    db.close()

init_chat_db()

def get_chat_history(session_id: str):
    db = init_chat_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT messages FROM chats WHERE session_id = ? ORDER BY created_at DESC LIMIT 1",
        (session_id,)
    )
    result = cursor.fetchone()
    db.close()
    
    if not result:
        return []
    return json.loads(result[0])

# Chat endpoint
@rt("/chat")
def post(user_input: str, session):
    if 'id' not in session:
        session['id'] = str(uuid.uuid4())
    session_id = session['id']
    
    messages = get_chat_history(session_id)
    messages.append({'role': 'user', 'content': user_input})
    save_chat_history(session_id, messages)

    storage_context = setup()
    chat_engine = chat_session(storage_context)
    
    # Create chat history pairs for LlamaIndex (list of tuples)
    chat_history = []
    for i in range(0, len(messages)-1, 2):  # Step by 2 to get pairs, exclude current message
        if i+1 < len(messages):  # Make sure we have a pair
            if messages[i]['role'] == 'user' and messages[i+1]['role'] == 'assistant':
                chat_history.append((
                    messages[i]['content'],
                    messages[i+1]['content']
                ))
    
    # Use chat_history with the chat engine
    response = chat_engine.chat(
        user_input,
        chat_history=chat_history
    )
    
    sources = []
    if hasattr(response, 'source_nodes'):
        sources = ['/data/' + os.path.basename(node.metadata.get('source', 'Unknown source')) for node in response.source_nodes]
        sources = list(dict.fromkeys(sources))  # Remove duplicates while preserving order

    messages.append({'role': 'assistant', 'content': str(response.response)})
    save_chat_history(session_id, messages)
    
    return Container(
        Div(
            str(response.response),
            cls="marked response-content"
        ),
        Div(
            H2("Sources:"),
            Ul(*[Li(source) for source in sources]) if sources else None,
            cls="sources mt-4"
        ) if sources else None
    )

# Admin scrape endpoint
@rt("/admin/scrape")
def post():
    download_urls()
    return P("Scraping completed!")

serve()