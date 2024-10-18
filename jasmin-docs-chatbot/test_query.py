from src.rag_lib import RAGController
rc = RAGController()

resp = rc.get_response("How do I use the JASMIN platform?")
print(resp)