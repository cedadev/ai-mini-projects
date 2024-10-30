from src.rag_lib import RAGController
rc = RAGController()

print("[INFO] Regenerating everything...")
rc.regenerate()


print("[INFO] Running a test JASMIN query...")
resp = rc.get_response("How do I use the JASMIN platform?")
print(resp)

print("\n----------------------\n")
print("[INFO] Running a test CEDA query...")
resp = rc.get_response("What kind of data is held in the CEDA Catalogue?")
print(resp)
