import sys
from scrape import download_urls
from ai_stuff import setup, chat_session

def main():
    if len(sys.argv) > 1:
        if sys.argv[1] == "scrape":
            download_urls()
        elif sys.argv[1] == "chat":
            storage_context, config = setup()
            chat_session(storage_context, config)
        else:
            print("Invalid command. Use 'make help' to see available commands.")
            sys.exit(1)

if __name__ == "__main__":
    main()
