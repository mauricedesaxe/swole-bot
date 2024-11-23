import sys
from scrape import download_urls
from ai_stuff import setup, chat_session
from dotenv import load_dotenv
from fasthtml.common import *
import markdown

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

# Chat endpoint
@rt("/chat")
def post(user_input: str):
    storage_context = setup()
    chat_engine = chat_session(storage_context)
    response = chat_engine.chat(user_input)
    
    sources = []
    if hasattr(response, 'source_nodes'):
        sources = [node.metadata.get('source', 'Unknown source') for node in response.source_nodes]
    
    return Container(
        # Main response using FastHTML's markdown support
        Div(
            str(response.response),
            cls="marked response-content"
        ),
        # Sources section
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