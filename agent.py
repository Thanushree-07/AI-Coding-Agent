import os
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


client=Groq(api_key=os.getenv("GROQ_API_KEY"))

def read_file(path):
    with open(path,"r") as f:
        data=f.read()
    return data

tools=[
    {
        "type":"function",
        "function":{
            "name":"read_file",
            "description":"read contents of file",
            "parameters":{
                "type":"object",
                "properties":
                {
                    "path":{
                        "type":"string",
                        "description":"this gives name of file you want to read"
                       
                    }

                    
                },
                "required":["path"]
            }
        }
    }
]


messages=[]
while True:
    user_input=input("Thanu :")
    if user_input=="quit":
        break

    messages.append({
        "role":"user",
        "content":user_input
    })


    response=client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        temperature=0.2,
        tools=tools,
    )
    msg=response.choices[0].message
    if msg.tool_calls:
        messages.append(msg)
        call=msg.tool_calls[0]
        args=json.loads(call.function.arguments)
        result=read_file(args["path"])
        messages.append({
            "role":"tool",
            "tool_call_id":call.id,
            "content":result,
        })

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=messages,
        tools=tools,
        temperature=0.2,
    )

    msg=response.choices[0].message
   
    messages.append({"role":"assistant","content":msg.content})
    print("AI :",msg.content)
    # print(messages)

