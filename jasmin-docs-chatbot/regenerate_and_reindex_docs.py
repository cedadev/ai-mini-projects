from src.rag_lib import RAGController
rc = RAGController()

print("Regenerating everything...")
rc.regenerate()


print("Running a test query...")
rc.get_response("How do I use the JASMIN platform?")
print(resp)
