import chainlit as cl
from src.rag_lib import get_response


@cl.on_message
async def main(message: cl.Message):
    # Your custom logic 
    rag_response = get_response(message.content)
    
    # Send a response back to the user
    await cl.Message(
        content=rag_response, 
    ).send()


