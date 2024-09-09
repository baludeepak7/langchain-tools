from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate,ChatPromptTemplate
import json
from template import PROMPT_TEMPLATE
from langchain.agents import create_tool_calling_agent,AgentExecutor
import requests
import re
import chainlit as cl
from pydantic import BaseModel
from typing import List

llm = ChatOllama(model="llama3.1",temperature=0)

headers = {
    'Content-Type': 'application/json'
}


class BookingPartner(BaseModel):
    id: str
    name: str
    ica: str
    companyId: str
    def to_dict(self):
        
        return {
            'id': self.id,
            'name': self.name,
            'ica':self.ica,
            'companyId':self.companyId
            
        } 

from typing import Optional

def getPartnerProfileById(partner_id: str) -> Optional[BookingPartner]:
    partners = gatAllPartnerProfiles()
    for partner in partners:
        if partner.id == partner_id:
            return partner
    return None 


@tool
def updatePartnerProfile(name:str,nameToChange:str) -> str:
    """
    Update the travel partner profile.
    
    """
    prompt_template = PromptTemplate.from_template(
    template=PROMPT_TEMPLATE
     )
    json_data=gatAllPartnerProfiles()
    partners_dict = [partner.to_dict() for partner in json_data]
    http_response = json.dumps(partners_dict)
    prompt_template.input_variables = ["http_response", "name"]
    chain = prompt_template | llm
    input_data = {
    "http_response": http_response,
    "name": name
}
    result = chain.invoke(input_data)
    print(result.content)
    numbers = re.findall(r'\d+', result.content)
    id = ''.join(numbers)

    url = 'http://localhost:9097/travel/booking-partner/'+id
    partner = getPartnerProfileById(id)
    data = {
             "id": id,
             "name": nameToChange,
             "ica": partner.ica,
             "companyId": partner.companyId
            }
    response = requests.put(url, headers=headers, json=data)
    if response.status_code == 200:
     print('Success:', response.json())
     return "Updated booking partner successfully "+response.text
    else:
     print('Error:', response.status_code, response.text)
     return "Failed to update booking partner "

 
def gatAllPartnerProfiles() -> List[BookingPartner]:
    url = 'http://localhost:9097/travel/booking-partner/'
    response = requests.get(url, headers=headers)
    print(url)
    if response.status_code == 200:
     print('Success:', response.json())
     partners = [BookingPartner(**item) for item in response.json()]
     return partners
    else:
      print('Failed:', response.status_code, response.text)
      return []
 
tools = [updatePartnerProfile]

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a buddy bot and use the tools to get and update travel partner profiles."),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder","{agent_scratchpad}"),
    ]
)

@cl.on_chat_start
def setup_multiple_chains():
    agent = create_tool_calling_agent(llm, tools ,prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    cl.user_session.set("agent_executor", agent_executor)


@cl.on_message
async def handle_message(message: cl.Message):
    user_message = message.content.lower()
    agent_executor = cl.user_session.get("agent_executor")
    response =  agent_executor.invoke({"input":user_message})

    response_key = "output" if "output" in response else "text"
    await cl.Message(response.get(response_key, "")).send()
