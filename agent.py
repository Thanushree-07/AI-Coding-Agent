import os
import subprocess
import json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()


client=Groq(api_key=os.getenv("GROQ_API_KEY"))

def read_file(path):
    with open(path,"r") as f:
        data=f.read()
    return data

def list_files(path="."):
    try:
        return "\n".join(os.listdir(path))
    except Exception as e:
        return f"Error:{e}"

# print(list_files("playgrounds"))

def edit_file(path,content):
    try:
        with open(path,"w") as f:
            f.write(content)
        return f"Wrote {path}"
    except Exception as e:
        return f"error ocurred .coudnt write to specified file :{e}"


def run_command(command):
    try:
        r=subprocess.run(command,shell=True,capture_output=True,text=True,timeout=30)
        return (r.stdout+r.stderr) or "(no output)"
    except Exception as e:
        return f"Error :{e}"


available_tools={
    "read_file":read_file,
    "list_files":list_files,
    "edit_file":edit_file,
    "run_command":run_command
}


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
    },
    {
        "type":"function",
        "function":
        {
            "name":"list_files",
            "description":"list all files in the given directory",
            "parameters":
            {
                "type":"object",
                "properties":
                {
                    "path":
                    {
                    "type":"string",
                    "description":"folder to list"
                    },
                },
                "required":[],
            },
        },
    },
    {
        "type":"function",
        "function":
        {
            "name":"edit_file",
            "description": "Replace the ENTIRE contents of a file with new content. Always read the file first, then send the full updated text. Also use this to create new files.",
            "parameters":
            {
                "type":"object",
                "properties":
                {
                    "path":
                    {
                        "type":"string",
                        "description":"name of file whose contents need to be edited"
                    },
                    "content":
                    {
                        "type":"string",
                        "description":"contains content"
                    }
                },
                "required":["path","content"],
            },
        },
    },
    {
        "type":"function",
        "function":{

        "name":"run_command",
        "description":"Running command on command prompt and give result",
        "parameters":
        {
            "type":"object",
            "properties":
            {
                "command":{
                    "type":"string",
                    "description":"this contains the command that needs to be executed"
                }
            },
            "required":["command"],
        },
    },
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
    while msg.tool_calls:
        messages.append(msg)
        for call in msg.tool_calls:
            args=json.loads(call.function.arguments)
            print("TOOL CALLED:", call.function.name, args)
            func=available_tools[call.function.name]
            result=func(**args)
            messages.append({
                "role":"tool",
                "tool_call_id":call.id,
                "content":str(result),
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

