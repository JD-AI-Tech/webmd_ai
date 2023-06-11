import streamlit as st
import os
from langchain import OpenAI
from langchain import LLMChain
from langchain.tools import Tool, DuckDuckGoSearchRun
from langchain.agents import AgentOutputParser, LLMSingleActionAgent, AgentExecutor
from langchain.prompts import StringPromptTemplate
from langchain.schema import AgentFinish, AgentAction
from langchain.memory import ConversationBufferWindowMemory

from typing import List, Union
import re
import langchain

# api
os.environ["OPENAI_API_KEY"] = st.secrets['apikey']
langchain.debug = True
search = DuckDuckGoSearchRun()
model_name = 'gpt-3.5-turbo'
#model_name = 'text-davinci-003'

def search_for_advice(user_prompt):
    print(f"**** jddebug in custom_agent.search_for_advise()  {user_prompt}")
    response = agent_executor.run(user_prompt)
    return response

def duck_wrapper(input_text):
    search_results = search.run(f"site:webmd.com  {input_text}")
    #search_results = search.run(f"site:mayoclinic.org  {input_text}")
    return search_results

tools = [
    Tool(
        name = "Search WebMD",
        func=duck_wrapper,
        description="useful for when you need to answer medical and pharmalogical questions"
    )
]

# Set up the base template
template = """Answer the following questions as best you can, but speaking as a virtual medical professional. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin! Remember to answer as a compansionate medical professional when giving your final answer. If you do not know the answer do not make one up.

Previous conversation history:
{history}

Question: {input}
{agent_scratchpad}"""


# Set up a prompt template
class CustomPromptTemplate(StringPromptTemplate):
    # The template to use
    template: str
    # The list of tools available
    tools: List[Tool]

    def format(self, **kwargs) -> str:
        # Get the intermediate steps (AgentAction, Observation tuples)
        # Format them in a particular way
        intermediate_steps = kwargs.pop("intermediate_steps")
        thoughts = ""
        for action, observation in intermediate_steps:
            thoughts += action.log
            thoughts += f"\nObservation: {observation}\nThought: "
        # Set the agent_scratchpad variable to that value
        kwargs["agent_scratchpad"] = thoughts
        # Create a tools variable from the list of tools provided
        kwargs["tools"] = "\n".join([f"{tool.name}: {tool.description}" for tool in self.tools])
        # Create a list of tool names for the tools provided
        kwargs["tool_names"] = ", ".join([tool.name for tool in self.tools])
        return self.template.format(**kwargs)

prompt = CustomPromptTemplate(
    template=template,
    tools=tools,
    # This omits the `agent_scratchpad`, `tools`, and `tool_names` variables because those are generated dynamically
    # This includes the `intermediate_steps` variable because that is needed
    input_variables=["input", "intermediate_steps", "history"]
)


class CustomOutputParser(AgentOutputParser):
    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if "Final Answer:" in llm_output:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={"output": llm_output.split("Final Answer:")[-1].strip()},
                log=llm_output,
            )
        # Parse out the action and action input
        regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            regex = r"Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)"
            match = re.search(regex, llm_output, re.DOTALL)
            if not match:
               raise ValueError(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        # Return the action and action input
        jd_tool_input = action_input.strip(" ").strip('"')
        print(f"jddebug ********* action=  {action}")
        print(f"jddebug ********* tool_input=  {jd_tool_input}")
        return AgentAction(tool=action, tool_input=action_input.strip(" ").strip('"'), log=llm_output)


output_parser = CustomOutputParser()

llm = OpenAI(temperature=0, model_name=model_name)
llm_chain = LLMChain(llm=llm, prompt=prompt)

tool_names = [tool.name for tool in tools]
print(f"jddebug tool_names[] = {tool_names}")

agent = LLMSingleActionAgent(
    llm_chain=llm_chain,
    output_parser=output_parser,
    stop=["\nObservation:"],
    allowed_tools=tool_names
)
print(f"jddebug tool_names[] = {tool_names}")
memory=ConversationBufferWindowMemory(k=2)
agent_executor = AgentExecutor.from_agent_and_tools(agent=agent,
                                                    tools=tools,
                                                    verbose=True,
                                                    memory=memory)
