# Swole Bot

A chatbot that uses RAG to answer questions about sports, weightlifting, testosterone... 
all with the goal of getting you swole. 💪🏻

## Features

- RAG-powered responses using OpenAI models
- Smart document processing with hierarchical chunking
- Semantic search with Jina AI embeddings and reranking
- Source tracking and citation
- Intelligent content validation
- Intelligent scraping of documents from the web
- Vector storage with Chroma

## Installation

1. Clone the repository
2. Install Poetry if you haven't already
3. Install dependencies with `poetry install`
4. Create a `.env` file based on the `.env.example` file
5. Scrape documents with `make scrape`
6. Chat with the bot with `make chat`

## Roadmap

- [ ] Transition into a web app using FastHTML.
- [ ] Implement semantic chunking based on section headers, smart overlap that preserves complete sentences and dynamic chunk sized based on content type

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please use descriptive commit messages and add a PR description 
describing the *why* behind the changes you're making.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.