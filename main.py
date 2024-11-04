import sys
from scrape import download_urls
from ai_stuff import load_config, setup_ai, initialize_llm, chat_session

def main():
    config = load_config()
    storage_context, config = setup_ai()
    initialize_llm(config)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "scrape":
            download_urls()
        elif sys.argv[1] == "chat":
            chat_session(storage_context, config)
        else:
            print("Invalid command. Use 'make help' to see available commands.")
            sys.exit(1)

if __name__ == "__main__":
    main()
