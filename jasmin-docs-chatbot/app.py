from typing import Optional
import os

import chainlit as cl
from src.rag_lib import RAGController

rc = RAGController()
pw = os.environ.get("APP_PASSWORD", "")


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    if password == pw and username.endswith("@stfc.ac.uk"):
        return cl.User(
            identifier=username, metadata={"role": "user", "provider": "credentials"}
        )
    else:
        return None


@cl.on_message
async def main(message: cl.Message):
    # Your custom logic 
    rag_response = rc.get_response(message.content)
    
    # Send a response back to the user
    await cl.Message(
        content=rag_response, 
    ).send()
