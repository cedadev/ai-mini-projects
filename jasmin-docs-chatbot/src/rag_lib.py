import os, time, sys
import warnings
warnings.filterwarnings("ignore")

import pandas as pd

from sentence_transformers import SentenceTransformer
from langchain_openai import ChatOpenAI
from langchain.prompts.chat import ChatPromptTemplate

from pinecone import Pinecone, ServerlessSpec

sys.path.extend(["..", "."])
from jasmin_docs_parser import clone_repo, parse_repo


# Check that service API keys are defined as environment variables
req_keys = ["PINECONE_API_KEY", "OPENAI_API_KEY"]
for req_key in req_keys:
    if req_key not in os.environ:
	    raise KeyError(f"Missing env var: {req_key}")

pinecone_api_key = os.environ["PINECONE_API_KEY"]
openai_api_key = os.environ["OPENAI_API_KEY"]

# Embedder classes: for embedding docs using relevant model 
class AbstractEmbedder:
    def __init__(self, **kwargs):
       pass

class OpenAIEmbedder(AbstractEmbedder):

    def __init__(self):
        super().__init__()

    def embed(self, sentences):
        pass

class SentenceTransformerEmbedder(AbstractEmbedder):
    def __init__(self, model_path, device="cpu"):
        super().__init__()

        self.model = SentenceTransformer(model_path)
        self.model.to(device)

    def embed(self, sentences):
        return self.model.encode(sentences, show_progress_bar=True)


# The RAG Controller class that manages the RAG model:
# - Regenerates the index
# - Queries the index
class RAGController:
    def __init__(self, openai_api_key=openai_api_key, pinecone_api_key=pinecone_api_key):
        self.openai_api_key = openai_api_key
        self.pinecone_api_key = pinecone_api_key

        self.pc = Pinecone(api_key=pinecone_api_key)
        self.csv_path = "jasmin_docs.csv"
        self.df = None

        self.pc_index = None
        self.index_name = "jasmin-documentation"
        self.embeddings = None
        self.encoder = self._get_encoder()
        self.metric = "cosine"   # https://docs.pinecone.io/docs/indexes#distance-metrics

    def _get_encoder(self):
        # Instantiate an encoder
        # https://huggingface.co/sentence-transformers/paraphrase-MiniLM-L6-v2
        embedding_model = "paraphrase-MiniLM-L6-v2"
        encoder = SentenceTransformerEmbedder(embedding_model, device="cpu")
        return encoder

    def regenerate(self):
        self._remove_csv()
        self._reclone_repo()
        self._create_csv()
        self._create_embeddings()
        self._delete_index()
        self._create_index()
        self._upsert_index() 

    def _remove_csv(self):
        if os.path.isfile(self.csv_path):
            os.remove(self.csv_path)
            print(f"Removed: {self.csv_path}")

    def _reclone_repo(self):
        print("Recloning JASMIN docs repo...")
        clone_repo(force=True)

    def _create_csv(self):
        self.df = parse_repo(csv_path=self.csv_path)
        print(f"Wrote: {self.csv_path}")

    def load_df(self):
        if isinstance(self.df, pd.DataFrame): 
            return

        if os.path.isfile(self.df_csv):
            print(f"Loading docs from: {self.csv_path}")
            self.df = pd.read_csv(self.csv_path)
        else:
            print("Parsing docs from GitHub repo...")
            self.df = parse_repo(csv_path=self.csv_path)
            self.df.to_csv(self.csv_path, index=False)
            print(f"Wrote: {self.csv_path}")

        word_count_threshold = 10
        char_count_threshold = 25

        # Filter out rows with less than N words or  M chars.
        self.df = self.df[self.df.word_count > word_count_threshold]
        self.df = self.df[self.df.char_count > char_count_threshold]
        print("Content found (first 5 records):\n", self.df.head())

    def _create_embeddings(self):
        docs = self.df.contents.tolist()

        # Encode documents
        self.embeddings = self.encoder.embed(docs)  # takes ~30-45 seconds on average in sandbox instance
        self.dimension = len(self.embeddings[0])
        print("Length (dimension) of embeddings is: {dimension}")
    
    def _get_index(self):
        # connect to the index
        if not self.pc_index:
            self.pc_index = self.pc.Index(self.index_name) 

        return self.pc_index
    
    def _create_index(self):
        if self.index_name not in self.pc.list_indexes().names():
            print(f"Creating index: {self.index_name}")
            # https://docs.pinecone.io/reference/create_index
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=self.metric,
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

    def _delete_index(self):
        self.pc.delete_index(
            name=self.index_name,
        )
        print(f"Deleted: {self.index_name}")

    def _upsert_index(self):
        self.load_df()
        docs = self.df.contents.tolist()

        # Encode documents
        if self.embeddings != None:
            self._create_embeddings()

        ids = self.df.index.values
        # connect to the index
        index = self._get_index()

        vectors = [
            {
                "id": str(idx),
                "values": emb.tolist(),
                "metadata": {"text": txt},
            }
            for idx, (txt, emb) in enumerate(zip(docs, self.embeddings))
        ]
        
        upsert_response = index.upsert(vectors=vectors)
        print(f"Index {self.index_name} has been successfully populated.")


    def get_response(self, query):
        print(f"\n\nTesting this query:\n\t'{query}'.")

        human_template = "{user_query}"

        # Embed the query with the same vector embedder as used with the docs
        k = 5

        # Now encode the query and in vector space and see which document (fragments) match
        # from our JASMIN docs.
        vector = self.encoder.embed([query])[0]
        index = self._get_index()
        matches = index.query(vector=vector.tolist(), top_k=k, include_metadata=True)
        matches = matches.to_dict()["matches"]

        # Gather indexes of the matching docs
        row_idxs = []
        for m in matches:
            row_idxs.append(int(m["id"]))

        self.load_df()
        retrieved_results = self.df.iloc[row_idxs, :]

        os.environ["TOKENIZERS_PARALLELISM"] = "false"

        # Set up the prompt to send the message to the OpenAI model
        system_message = """
    You are a helpful assistant that helps scientists to use the JASMIN platform for their data workflows.

    Here is some relevant context you can use, each with links to a page in the JASMIN documentation where the context is retrieved from:
    """

        context_template = """
    {system_message}

    {context}

    Use the above pieces of context to condition the response.
    """

        # Prepare the context to send to the OpenAI model
        _context = ""
        for _, row in retrieved_results.iterrows():
            _context += "\n### context: {}\n### url: {} \n".format(row.contents, row.page_url)

        human_template = "{user_query}"

        # Send the query to the OpenAI model
        chat_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", context_template),
                ("human", human_template),
            ]
        )

        chat = ChatOpenAI(openai_api_key=self.openai_api_key)

        response = chat.invoke(
            chat_prompt.format_messages(
                user_query=query, context=_context, system_message=system_message
            )
        )

        return response.content


if __name__ == "__main__":
    rc = RAGController(openai_api_key=openai_api_key, 
                       pinecone_api_key=pinecone_api_key)
    rc.regenerate()