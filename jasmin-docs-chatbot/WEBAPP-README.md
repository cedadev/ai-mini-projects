## Chainlit web-app

```
pip install -r requirements.txt
pip install -e . --no-deps
```

## Run with

```
chainlit run app.py
```

## Building and running with Docker

Build the image:

```
docker build -t jasmin-docs-chatbot:latest .
```

Run the container, with environment variables set:

```
docker run -p 8000:8000 \
       -e OPENAI_API_KEY="<openai_key>" \
       -e PINECONE_API_KEY="<pinecone_key>" \
       <image_id>
```

It should now be running on: http://localhost:8000


