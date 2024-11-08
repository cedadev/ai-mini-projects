# JASMIN Docs Chatbot mini-project

## Justification

- **Objective:** Create a chatbot that knows about JASMIN based on our documentation. Deploy the chatbot for internal testing and evaluation.
- **Success Metrics:** Does the chatbot tell the truth? Does it add value? Could we consider providing a public version? Could we add more information to it (for CEDA docs etc)?

## Project Outline

- **Project Name:** JASMIN Docs Chatbot
- **Scope:** Testing out AI technologies for potential use in communications with our users. Considered experimental at this stage but might lead to a production service.
- **Timeline:** 
  - Planning: 1 day
  - Development: 3 days
  - Testing: 3 days
  - Deployment: (internal) 1 day
- **Team:** 
  - Developer: Ag
  - Tester: ?
- **Datasets:**
  - JASMIN Help Docs: https://github.com/cedadev/jasmin-help-hugo-hinode
- **AI Methods:**
  - Retrieval Augmented Generation (RAG)
- **Dependencies and tools:**
  - OpenAI LLM API (costed usage)
  - Text Encocder model: https://huggingface.co/sentence-transformers/paraphrase-MiniLM-L6-v2
  - Pinecone Vector DB service (free for low usage)
  - Chainlit library to build web app
- **Metrics:**
  - Human testing

## Detailed description

See: https://github.com/cedadev/ai-mini-projects/blob/main/jasmin-docs-chatbot

This approach uses Retrieval Augmented Generation (RAG), as outlined below:

![RAG image](https://github.com/user-attachments/assets/cc98afc3-f842-462c-9701-e14bd60552bb)
**Figure 1.** Overview of RAG (Source: https://www.researchgate.net/publication/376182986_Semantic_Embeddings_for_Arabic_Retrieval_Augmented_Generation_ARAG)

The way RAG works is as follows:
- **Ahead of use:**
  - Identify trusted information sources - typically documents split into "chunks"
  - Encode those into vector form using an Embedding Model
  - Put them into a Vector Database
- **When a query is received:**
  - Encode the query into vector form using the same Embedding Model
  - Find the most relevant _chunks_ from the trusted information, using _cosine similarity_ in vector space
  - Send a request to a Large Language Model (LLM, such as ChatGPT or other) which includes:
    - A prompt to instruct it to use the _chunks_ provided as its primary source
    - The content of the _chunks_
    - The query sent by the user
    - A prompt to tell the LLM to respond the query given the above context
   
**What is the result?**

When RAG works, it uses all the power of an LLM in terms of being able to interpret and respond in natural language (in our case, English). However, it also uses information from a trusted knowledge base so it should be much more reliable than a general unconstrained LLM.

**Example chat**

Ask it about LOTUS:

![image](https://github.com/user-attachments/assets/ba0e361d-e6be-4ed2-8b2b-244e026bd8c8)

Ask it to generate a command specifying memory and CPU requirements:

![image](https://github.com/user-attachments/assets/aff1ff40-e6c8-47b1-8fa6-0429cecd0516)



