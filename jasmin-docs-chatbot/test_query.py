from src.rag_lib import RAGController
rc = RAGController()

#resp = rc.get_response("How do I use the JASMIN platform?")
resp = rc.get_response("What about Weather data at CEDA?")
print(resp)
